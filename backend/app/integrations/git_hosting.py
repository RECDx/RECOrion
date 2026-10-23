"""GitHub ve Gitea bağlayıcıları (ADIM 10.3): depo/issue okuma; onayla issue açma ve yorum (yazma = insan onayı).

Müşterinin kendi hesabı ve token'ı kullanılır (kasada şifreli). Aynı bağlantı proje kod deposunun bu hesaba yansıtılmasında
da kullanılır (#297, code_repo.set_mirror). İki sistemin REST API'si bu araçlar için aynı biçimdedir; fark adres ve yetki başlığıdır.
"""
import base64
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import httpx

from app.integrations.base import READ, WRITE, Connector, Context, Field, Tool, ToolError, http_client, require


def api_base(code: str, ctx: Context) -> str:
    if code == "github":
        return "https://api.github.com"
    url = (ctx.config.get("base_url") or "").strip().rstrip("/")
    if not url.startswith(("https://", "http://")):
        raise ToolError("Sunucu adresi http(s):// ile başlamalı.")
    return f"{url}/api/v1"


def web_base(code: str, ctx: Context) -> str:
    return "https://github.com" if code == "github" else (ctx.config.get("base_url") or "").strip().rstrip("/")


def _headers(code: str, ctx: Context) -> Dict[str, str]:
    token = ctx.secrets.get("token")
    if not token:
        raise ToolError("Erişim token'ı tanımlı değil.")
    if code == "github":
        return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    return {"Authorization": f"token {token}"}


async def call(code: str, ctx: Context, method: str, path: str, json: Optional[Dict[str, Any]] = None,
               params: Optional[Dict[str, Any]] = None) -> Any:
    title = "GitHub" if code == "github" else "Gitea"
    try:
        async with http_client(headers=_headers(code, ctx)) as c:
            r = await c.request(method, f"{api_base(code, ctx)}{path}", json=json, params=params)
    except httpx.HTTPError as exc:
        raise ToolError(f"{title}'a ulaşılamadı ({exc.__class__.__name__}).")
    if r.status_code >= 400:
        try:
            msg = (r.json() or {}).get("message") or ""
        except ValueError:
            msg = ""
        raise ToolError(f"{title} hata döndürdü: {r.status_code} {msg[:200]}".strip())
    return r.json() if r.content else {}


def split_repo(value: str) -> Tuple[str, str]:
    """'sahip/depo' veya depo adresi → (sahip, depo)."""
    v = (value or "").strip()
    if v.startswith(("https://", "http://")):
        v = urlparse(v).path
    parts = [p for p in v.strip("/").removesuffix(".git").split("/") if p]
    if len(parts) != 2:
        raise ToolError("Depo 'sahip/depo' biçiminde olmalı.")
    return parts[0], parts[1]


def _make(code: str, title: str, config_fields, description: str) -> Connector:
    def repo(args: Dict[str, Any]) -> str:
        require(args, "repo")
        owner, name = split_repo(args["repo"])
        return f"/repos/{owner}/{name}"

    async def list_repos(ctx: Context, args: Dict[str, Any]):
        if code == "github":
            rows = await call(code, ctx, "GET", "/user/repos", params={"per_page": 50, "sort": "updated"})
        else:
            rows = (await call(code, ctx, "GET", "/repos/search", params={"limit": 50})).get("data", [])
        return [{"repo": r["full_name"], "private": r.get("private"), "default_branch": r.get("default_branch"),
                 "description": (r.get("description") or "")[:200]} for r in rows]

    async def list_issues(ctx: Context, args: Dict[str, Any]):
        state = args.get("state") if args.get("state") in ("open", "closed", "all") else "open"
        rows = await call(code, ctx, "GET", f"{repo(args)}/issues", params={"state": state, "per_page": 50, "limit": 50, "type": "issues"})
        return [{"number": i["number"], "title": i["title"], "state": i["state"], "url": i.get("html_url"),
                 "labels": [lb["name"] for lb in i.get("labels") or []]} for i in rows if i.get("pull_request") is None]

    async def read_file(ctx: Context, args: Dict[str, Any]):
        require(args, "path")
        params = {"ref": args["ref"]} if args.get("ref") else None
        data = await call(code, ctx, "GET", f"{repo(args)}/contents/{str(args['path']).lstrip('/')}", params=params)
        if isinstance(data, list):
            return {"directory": [{"name": d["name"], "type": d["type"]} for d in data[:200]]}
        text = base64.b64decode(data.get("content") or "").decode("utf-8", errors="replace")
        return {"path": data.get("path"), "size": data.get("size"), "content": text}

    async def create_issue(ctx: Context, args: Dict[str, Any]):
        require(args, "title")
        i = await call(code, ctx, "POST", f"{repo(args)}/issues", {"title": str(args["title"])[:250], "body": str(args.get("body") or "")[:20000]})
        return {"number": i.get("number"), "url": i.get("html_url")}

    async def comment_issue(ctx: Context, args: Dict[str, Any]):
        require(args, "number", "body")
        c = await call(code, ctx, "POST", f"{repo(args)}/issues/{int(args['number'])}/comments", {"body": str(args["body"])[:20000]})
        return {"comment_id": c.get("id"), "url": c.get("html_url")}

    async def test(ctx: Context) -> str:
        me = await call(code, ctx, "GET", "/user")
        return f"{title} hesabı @{me.get('login')} ile bağlanıldı"

    r = {"type": "string", "description": "Depo, 'sahip/depo' biçiminde"}
    return Connector(
        code=code, title=title, description=description, config_fields=config_fields,
        secret_fields=[Field("token", "Erişim token'ı",
                             help="Depo okuma/yazma ve issue yetkili kişisel erişim token'ı. Kasada şifreli saklanır.")],
        static_tools=[
            Tool("list_repos", f"{title} hesabının erişebildiği depoları listeler.", {"type": "object", "properties": {}}, READ, list_repos),
            Tool("list_issues", "Depodaki issue'ları listeler (en fazla 50).",
                 {"type": "object", "properties": {"repo": r, "state": {"type": "string", "enum": ["open", "closed", "all"]}},
                  "required": ["repo"]}, READ, list_issues),
            Tool("read_file", "Depodaki bir dosyayı veya klasörü okur.",
                 {"type": "object", "properties": {"repo": r, "path": {"type": "string"}, "ref": {"type": "string", "description": "Dal/etiket"}},
                  "required": ["repo", "path"]}, READ, read_file),
            Tool("create_issue", "Depoda issue açar.",
                 {"type": "object", "properties": {"repo": r, "title": {"type": "string"}, "body": {"type": "string"}},
                  "required": ["repo", "title"]}, WRITE, create_issue),
            Tool("comment_issue", "Issue'ya yorum yazar.",
                 {"type": "object", "properties": {"repo": r, "number": {"type": "integer"}, "body": {"type": "string"}},
                  "required": ["repo", "number", "body"]}, WRITE, comment_issue),
        ],
        test_fn=test,
    )


GITHUB = _make("github", "GitHub", [Field("username", "GitHub kullanıcı adı", required=False,
                                          help="Kod deposu yansıtmada kullanılır (boşsa token sahibinin adı).")],
               "Şirketin GitHub hesabındaki depoları ve issue'ları okur; onayla issue açar. Proje kodunu bu hesaba yansıtabilir.")
GITEA = _make("gitea", "Gitea", [Field("base_url", "Sunucu adresi", placeholder="https://git.sirket.com"),
                                 Field("username", "Kullanıcı adı", required=False, help="Kod deposu yansıtmada kullanılır.")],
              "Şirketin kendi Gitea sunucusundaki depoları ve issue'ları okur; onayla issue açar. Proje kodunu buraya yansıtabilir.")
