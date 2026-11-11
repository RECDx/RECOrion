"""
İSTEK #740: genel e-posta (IMAP/SMTP; Gmail/Outlook/iCloud/Yandex/şirket sunucusu) ve Web/RSS kaynağı.

- E-posta araçları: arama ve okuma (READ; okunmadı işareti değişmez, HTML'den metin, ek adları, dış veri uyarısı),
  gönderme WRITE (insan onayı akışına girer; "Yalnızca okuma" bağlantıda hiç sunulmaz). Özel ağ sunucusu reddedilir.
- Outlook/Gmail hesapla giriş: RECDx platform istemcisi yoksa anlaşılır 409; varsa yetkilendirme adresi ve dönüşte token kasaya yazılır.
- RSS/Atom akışı okunur ({"items": [...]}, otomasyon POLL'una uygun); XML varlık tanımı içeren akış reddedilir.
- Otomasyonla açılan iş bitince sonuç yöneticiye ve seçilen kişiye (e-posta şablonu AUTOMATION_RESULT) iletilir.
"""
import asyncio
import email
import uuid

import pytest

from app.integrations import base, mail, web_source
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

RAW = ("From: =?utf-8?q?Ay=C5=9Fe_Kaya?= <ayse@tedarikci.com>\r\nTo: info@ornek.com\r\nSubject: =?utf-8?q?Sipari=C5=9F_onay=C4=B1?=\r\n"
       "Date: Tue, 10 Nov 2026 09:00:00 +0300\r\nMessage-ID: <abc@tedarikci.com>\r\nMIME-Version: 1.0\r\n"
       "Content-Type: multipart/mixed; boundary=XX\r\n\r\n--XX\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
       "<p>Merhaba,</p><p>Siparişiniz <b>onaylandı</b>.</p><script>x</script>\r\n--XX\r\n"
       "Content-Type: application/pdf\r\nContent-Disposition: attachment; filename=\"fatura.pdf\"\r\n\r\nJVBERi0=\r\n--XX--\r\n").encode()


class FakeIMAP:
    calls = []

    def __init__(self, host, port, ssl_context=None, timeout=None):
        self.host = host

    def login(self, user, pw):
        if pw != "uygulama-sifresi":
            raise mail.imaplib.IMAP4.error("auth")
        FakeIMAP.calls.append(("login", user))

    def authenticate(self, mech, cb):
        FakeIMAP.calls.append(("auth", mech, cb(b"")))

    def select(self, folder, readonly=False):
        FakeIMAP.calls.append(("select", folder, readonly))
        return "OK", [b"1"]

    def uid(self, cmd, *args):
        FakeIMAP.calls.append(("uid", cmd) + tuple(str(a) for a in args))
        if cmd == "SEARCH":
            return "OK", [b"7"]
        part = "BODY.PEEK[HEADER]" if "HEADER" in args[1] else "BODY.PEEK[]"
        return "OK", [(f"7 ({part} {{1}}".encode(), RAW), b")"]

    def logout(self):
        pass


@pytest.fixture
def fake_imap(monkeypatch):
    FakeIMAP.calls = []
    monkeypatch.setattr(mail.imaplib, "IMAP4_SSL", FakeIMAP)

    async def public(url):
        if "127.0.0.1" in url or "intranet" in url:
            from app.core.net import UnsafeURLError
            raise UnsafeURLError("özel")
    monkeypatch.setattr("app.core.net.assert_public_url", public)
    return FakeIMAP


def _ctx(**cfg):
    return base.Context(config={"provider": "gmail", "username": "info@ornek.com", **cfg}, secrets={"password": "uygulama-sifresi"})


def _run(coro):
    return asyncio.run(coro)


def test_mail_search_read_and_guards(fake_imap):
    tools = {t.name: t for t in mail.CONNECTOR.static_tools}
    r = _run(tools["search_messages"].run(_ctx(), {"from": "tedarikci", "since_days": 3}))
    assert r["count"] == 1 and r["items"][0]["subject"] == "Sipariş onayı" and r["items"][0]["from"] == "ayse@tedarikci.com"
    assert r["items"][0]["id"] == "<abc@tedarikci.com>"
    assert ("select", '"INBOX"', True) in fake_imap.calls  # salt okunur açılır
    m = _run(tools["read_message"].run(_ctx(), {"uid": "7"}))
    assert "Siparişiniz" in m["body"] and "onaylandı" in m["body"] and "x" not in m["body"].split()  # script atıldı
    assert m["attachments"][0]["name"] == "fatura.pdf" and "dış kaynaklıdır" in m["note"]
    assert any(c[:2] == ("uid", "FETCH") and "BODY.PEEK[]" in c[-1] for c in fake_imap.calls)  # okunmadı işareti değişmez
    with pytest.raises(base.ToolError, match="uygulama şifresi"):
        _run(tools["search_messages"].run(base.Context(config={"provider": "gmail", "username": "a@b.com"}, secrets={"password": "yanlis"}), {}))
    with pytest.raises(base.ToolError, match="özel ağ"):
        _run(tools["search_messages"].run(_ctx(provider="imap", imap_host="127.0.0.1", smtp_host="127.0.0.1"), {}))
    # yeni ileti aracı otomasyon POLL'una uygun biçimde döner
    assert "items" in _run(tools["list_new_messages"].run(_ctx(), {}))


def test_mail_send_is_write_and_hidden_when_read_only(fake_imap, monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            self.host = host

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, context=None):
            pass

        def login(self, u, p):
            pass

        def send_message(self, msg):
            sent.append(msg)
    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)
    send = next(t for t in mail.CONNECTOR.static_tools if t.name == "send_message")
    assert send.kind == base.WRITE  # insan onayı akışına girer (tool_gateway)
    r = _run(send.run(_ctx(display_name="Örnek Klinik"), {"to": "a@x.com, b@y.com", "subject": "Randevu", "body": "Yarın 10:00",
                                                         "in_reply_to": "<abc@tedarikci.com>"}))
    assert r["sent"] and r["to"] == ["a@x.com", "b@y.com"]
    assert sent[0]["In-Reply-To"] == "<abc@tedarikci.com>" and "Örnek Klinik" in sent[0]["From"]
    with pytest.raises(base.ToolError):
        _run(send.run(_ctx(), {"to": "geçersiz", "subject": "x", "body": "y"}))
    names = {t.name for t in _run(mail.CONNECTOR.tools(_ctx(access="READ_ONLY")))}
    assert "send_message" not in names and "read_message" in names


def test_oauth_xoauth2_and_feed_parsing(fake_imap):
    ctx = base.Context(config={"provider": "outlook", "username": "a@outlook.com", "auth": "oauth"},
                       secrets={"_access_token": "tok", "_expires_at": None})
    _run(next(t for t in mail.CONNECTOR.static_tools if t.name == "search_messages").run(ctx, {}))
    auth = next(c for c in fake_imap.calls if c[0] == "auth")
    assert auth[1] == "XOAUTH2" and b"user=a@outlook.com\x01auth=Bearer tok" in auth[2]

    rss = (b"<?xml version='1.0'?><rss><channel><item><title>Y\xc3\xb6netmelik</title><link>https://rg.gov.tr/1</link>"
           b"<guid>rg-1</guid><pubDate>Wed, 11 Nov 2026 00:00:00 +0300</pubDate><description>&lt;b&gt;Kurul&lt;/b&gt; karar\xc4\xb1</description>"
           b"</item></channel></rss>")
    items = web_source.parse_feed(rss)
    assert items[0]["id"] == "rg-1" and items[0]["title"] == "Yönetmelik" and items[0]["link"] == "https://rg.gov.tr/1"
    assert "<b>" not in items[0]["summary"] and "Kurul" in items[0]["summary"] and "kararı" in items[0]["summary"]
    assert items[0]["date"].startswith("2026-11-11")
    atom = b"<feed xmlns='http://www.w3.org/2005/Atom'><entry><id>a1</id><title>Duyuru</title><link href='https://x.org/a'/></entry></feed>"
    assert web_source.parse_feed(atom)[0]["link"] == "https://x.org/a"
    with pytest.raises(base.ToolError, match="XML varlık"):
        web_source.parse_feed(b"<!DOCTYPE x [<!ENTITY a 'b'>]><rss/>")


def test_mail_oauth_endpoints(client, db, world, monkeypatch):
    from app.config import settings
    from app.integrations import oauth
    w = world
    admin = w["admin"]["h"]
    r = client.post(f"/api/v1/company/{w['tenant']}/integrations", headers=admin, json={
        "connector": "mail", "name": f"Outlook {uuid.uuid4().hex[:4]}",
        "config": {"provider": "outlook", "auth": "oauth", "username": "info@ornek.com"}, "secrets": {}})
    assert r.status_code == 201, r.text
    conn = r.json()
    assert conn["oauth"]["connected"] is False
    monkeypatch.setattr(settings, "MAIL_MS_CLIENT_ID", "")
    s = client.post(f"/api/v1/company/{w['tenant']}/integrations/{conn['id']}/oauth/start", headers=admin)
    assert s.status_code == 409 and "Uygulama şifresi" in s.json()["detail"]
    monkeypatch.setattr(settings, "MAIL_MS_CLIENT_ID", "recdx-app")
    monkeypatch.setattr(settings, "MAIL_MS_CLIENT_SECRET", "gizli")
    saved = {}

    async def save_pending(state, data):
        saved[state] = data

    async def pop_pending(state):
        return saved.pop(state, None)

    async def token_request(endpoint, client_, methods, data):
        assert client_["id"] == "recdx-app" and data["grant_type"] == "authorization_code" and data["code_verifier"]
        return {"_access_token": "AT", "_refresh_token": "RT", "_expires_at": 9999999999}
    monkeypatch.setattr(oauth, "save_pending", save_pending)
    monkeypatch.setattr(oauth, "pop_pending", pop_pending)
    monkeypatch.setattr(oauth, "_token_request", token_request)
    s = client.post(f"/api/v1/company/{w['tenant']}/integrations/{conn['id']}/oauth/start", headers=admin)
    assert s.status_code == 200, s.text
    url = s.json()["authorize_url"]
    assert url.startswith("https://login.microsoftonline.com/") and "IMAP.AccessAsUser.All" in url and "login_hint=info%40ornek.com" in url
    state = next(iter(saved))
    cb = client.get(f"/api/v1/integrations/oauth/callback?state={state}&code=KOD", follow_redirects=False)
    assert cb.status_code == 302 and "oauth=ok" in cb.headers["location"]
    lst = client.get(f"/api/v1/company/{w['tenant']}/integrations", headers=admin).json()
    me = next(c for c in lst if c["id"] == conn["id"])
    assert me["oauth"]["connected"] is True and "AT" not in str(me)  # token ekrana çıkmaz


def test_automation_result_delivered(client, db, world, monkeypatch):
    from app.db.session import AsyncSessionLocal
    from app.services import agent_work, automations, notify
    w = world
    rid = _exec(db, "INSERT INTO automation_rules (id, tenant_id, name, trigger, status, action, conditions, rate_limit_per_hour) "
                    "VALUES (gen_random_uuid(), %s, 'Günlük e-posta özeti', 'SCHEDULE', 'ACTIVE', %s, '[]', 20) RETURNING id",
                w["tenant"], '{"type": "CREATE_CASE", "deliver_result": true, "notify_actor_ids": ["%s"]}' % w["member"]["id"])[0]
    pid = _exec(db, "INSERT INTO projects (id, tenant_id, name, slug, status, kind, manager_actor_id, source_rule_id) "
                    "VALUES (gen_random_uuid(), %s, 'Özet 11.11', %s, 'ACTIVE', 'CASE', %s, %s) RETURNING id",
                w["tenant"], f"ozet-{uuid.uuid4().hex[:6]}", w["admin"]["id"], rid)[0]
    _exec(db, "INSERT INTO tasks (id, project_id, title, status, completed_at, order_index) VALUES (gen_random_uuid(), %s, 'Özetle', 'DONE', now(), 0)", pid)
    out = []

    async def send(db_, actor_id, text, email_code=None, email_context=None, **k):
        out.append((str(actor_id), email_code, email_context))
        return {}

    async def latest(db_, tid):
        return object()

    async def text(art, limit):
        return "3 yeni e-posta: tedarikçi siparişi onayladı."
    monkeypatch.setattr(notify, "send", send)
    monkeypatch.setattr(agent_work, "latest_artifact", latest)
    monkeypatch.setattr(agent_work, "artifact_text", text)

    async def go():
        from app.db.models import Project
        async with AsyncSessionLocal() as s:
            return await automations.deliver_result(s, await s.get(Project, pid))
    assert client.portal.call(go) == 2
    assert {o[0] for o in out} == {w["admin"]["id"], w["member"]["id"]}
    assert out[0][1] == "AUTOMATION_RESULT" and "tedarikçi" in out[0][2]["result_text"]
    assert _exec(db, "SELECT count(*) FROM email_templates WHERE code = 'AUTOMATION_RESULT'")[0] == 1
