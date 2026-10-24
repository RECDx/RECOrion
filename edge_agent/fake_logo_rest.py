"""
Sahte Logo REST servisi (ADIM 12.5) — Edge ajanının REST şablonlarını denemek ve test etmek için. GERÇEK LOGO DEĞİLDİR.

Gerçek Logo REST servisinin uç adları ve alan adları sürüme göre değişebilir; templates.logo_rest.example.json içindeki
yol ve alanları kendi Logo REST servis belgenize göre uyarlayın. Bu sunucu yalnızca şu davranışı taklit eder:
- POST /api/v1/token (parola akışı, istemci Basic kimliği; firmno formda) → erişim token'ı
- GET  /api/v1/items?code=..  · POST /api/v1/items · PUT /api/v1/items/{ref}     (malzeme kartı; aynı kod reddedilir)
- GET  /api/v1/Arps?tax_id=.. · POST /api/v1/Arps  · PUT /api/v1/Arps/{ref}      (cari kart; aynı kod reddedilir)
Kayıtlar bellekte tutulur; GET /__state tüm kayıtları döner (test doğrulaması).

    python fake_logo_rest.py 32001
"""
import base64
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

USER, PASSWORD, CLIENT = "LOGO", "sahte-parola", "recorion:sahte-istemci"
STATE = {"items": {}, "Arps": {}, "next": 1000, "token": "sahte-logo-token", "issued": 0}
UNIQUE = {"items": "CODE", "Arps": "CODE"}
FILTER = {"items": ("code", "CODE"), "Arps": ("tax_id", "TAX_ID")}
LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # sessiz
        pass

    def _send(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _authed(self):
        return self.headers.get("Authorization") == f"Bearer {STATE['token']}"

    def _route(self):
        parts = urlsplit(self.path)
        seg = [p for p in parts.path.split("/") if p]
        return parts, seg

    def do_GET(self):
        parts, seg = self._route()
        if parts.path == "/__state":
            return self._send(200, {k: list(v.values()) for k, v in STATE.items() if k in UNIQUE} | {"tokens_issued": STATE["issued"]})
        if not self._authed():
            return self._send(401, {"Message": "Yetkisiz"})
        if len(seg) == 3 and seg[:2] == ["api", "v1"] and seg[2] in UNIQUE:
            q = {k: v[0] for k, v in parse_qs(parts.query).items()}
            key, field = FILTER[seg[2]]
            rows = [r for r in STATE[seg[2]].values() if key not in q or str(r.get(field)) == q[key]]
            return self._send(200, {"items": rows, "count": len(rows)})
        return self._send(404, {"Message": "Bulunamadı"})

    def do_POST(self):
        parts, seg = self._route()
        raw = self._body()
        if parts.path == "/api/v1/token":
            form = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
            basic = "Basic " + base64.b64encode(CLIENT.encode()).decode()
            if self.headers.get("Authorization") != basic or form.get("username") != USER or form.get("password") != PASSWORD or form.get("firmno") != "1":
                return self._send(400, {"error": "invalid_grant", "error_description": "Kullanıcı, parola veya firma hatalı"})
            STATE["issued"] += 1
            return self._send(200, {"access_token": STATE["token"], "expires_in": 3600, "token_type": "bearer"})
        if not self._authed():
            return self._send(401, {"Message": "Yetkisiz"})
        if len(seg) == 3 and seg[:2] == ["api", "v1"] and seg[2] in UNIQUE:
            body = json.loads(raw or b"{}")
            res = seg[2]
            with LOCK:
                if not body.get("CODE"):
                    return self._send(400, {"Message": "CODE zorunlu"})
                if any(r.get(UNIQUE[res]) == body.get(UNIQUE[res]) for r in STATE[res].values()):
                    return self._send(409, {"Message": f"Bu kodla kayıt zaten var: {body.get('CODE')}"})
                STATE["next"] += 1
                rec = {"INTERNAL_REFERENCE": STATE["next"], **body}
                STATE[res][STATE["next"]] = rec
            return self._send(201, rec)
        return self._send(404, {"Message": "Bulunamadı"})

    def do_PUT(self):
        parts, seg = self._route()
        body = json.loads(self._body() or b"{}")
        if not self._authed():
            return self._send(401, {"Message": "Yetkisiz"})
        if len(seg) == 4 and seg[:2] == ["api", "v1"] and seg[2] in UNIQUE and seg[3].isdigit() and int(seg[3]) in STATE[seg[2]]:
            rec = STATE[seg[2]][int(seg[3])]
            rec.update({k: v for k, v in body.items() if k != "INTERNAL_REFERENCE"})
            return self._send(200, rec)
        return self._send(404, {"Message": "Kayıt bulunamadı"})


def serve(port: int) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 32001
    print(f"Sahte Logo REST servisi http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
