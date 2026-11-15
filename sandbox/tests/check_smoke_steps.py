"""C3-60: smoke.run_browser adım türleri, bilinmeyen adım hatası ve adım bilgili hata mesajı. Çalıştırma: python sandbox/tests/check_smoke_steps.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "runner"))
sys.path.insert(0, "/srv/runner")
import smoke

calls = []


class Page:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
    def on(self, *a): pass
    def set_default_timeout(self, t): pass
    def close(self): pass
    def _c(self, name, *a, **k):
        calls.append((name, a, k))
        if self.fail_on == name:
            raise RuntimeError(f"{name}: Timeout exceeded.\nayrıntı")
    def goto(self, *a, **k): self._c("goto", *a, **k)
    def fill(self, *a, **k): self._c("fill", *a, **k)
    def click(self, *a, **k): self._c("click", *a, **k)
    def check(self, *a, **k): self._c("check", *a, **k)
    def uncheck(self, *a, **k): self._c("uncheck", *a, **k)
    def press(self, *a, **k): self._c("press", *a, **k)
    def select_option(self, *a, **k): self._c("select", *a, **k)
    def wait_for_selector(self, *a, **k): self._c("wait_for_selector", *a, **k)
    def wait_for_timeout(self, *a, **k): self._c("wait_ms", *a, **k)
    def get_by_text(self, t):
        page = self
        class L:
            first = None
        class F:
            def wait_for(self, **k): page._c("expect_text", t, **k)
        L.first = F()
        return L()


class Browser:
    def __init__(self, page): self.page = page
    def new_page(self): return self.page


svc = {"api": {"ready": True, "port": 8000}}
steps = [{"wait_for_selector": ".card", "state": "visible"}, {"click": ".card"}, {"fill": "#ad", "value": "x"},
         {"check": "#kvkk"}, {"click": "#gonder"}, {"expect_selector": "#ok", "timeout": 3000}, {"expect_text": "Onay"}]
ok, detail = smoke.run_browser({"service": "api", "path": "/", "steps": steps}, svc, {}, Browser(Page()))
assert ok, detail
names = [c[0] for c in calls]
assert names == ["goto", "wait_for_selector", "click", "fill", "check", "click", "wait_for_selector", "expect_text"], names
assert calls[6][2]["timeout"] == 3000 and calls[1][2]["state"] == "visible"

calls.clear()
ok, detail = smoke.run_browser({"service": "api", "path": "/", "steps": [{"tikla": "#x"}]}, svc, {}, Browser(Page()))
assert not ok and "Bilinmeyen adım türü" in detail and "adım 1/1" in detail, detail

calls.clear()
ok, detail = smoke.run_browser({"service": "api", "path": "/", "steps": steps}, svc, {}, Browser(Page(fail_on="check")))
assert not ok and detail.startswith("adım 4/7 (check: #kvkk)"), detail
print("smoke.run_browser: 3/3 senaryo GEÇTİ")
