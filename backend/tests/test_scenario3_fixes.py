"""Aşama 3 senaryosunda canlıda yapılan düzeltmelerin birim testleri (C3-43/58, C3-59)."""
from app.services import code_repo
from app.services.agent_work import with_manager_note


class T:
    order_index, title = 8, "Kurulum ve Duman Testi"


FENCE = "`" * 3


def test_manager_note_is_prepended_and_kept_with_review_note():
    """C3-43/58: yönetici notu kontrol notunun önüne ÖNCELİKLİ olarak eklenir; kontrol notu kaybolmaz."""
    out = with_manager_note("main.py'yi TAM yaz", "Statik dosyalar 404")
    assert out.startswith("Proje yöneticisinin yönlendirmesi (ÖNCELİKLİ")
    assert "main.py'yi TAM yaz" in out and "Önceki kontrol notu:\nStatik dosyalar 404" in out
    assert with_manager_note("  yalnız not  ", None).endswith("yalnız not")


def test_no_manager_note_leaves_feedback_unchanged():
    """Son yeniden deneme notsuz yapıldıysa eski not taşınmaz; geri bildirim aynen kalır."""
    assert with_manager_note(None, "kontrol notu") == "kontrol notu"
    assert with_manager_note("   ", "kontrol notu") == "kontrol notu"
    assert with_manager_note("", None) is None


def test_long_manager_note_is_capped():
    out = with_manager_note("x" * 5000, None)
    assert out.count("x") == 3000


def test_partial_file_is_not_written_but_reported():
    """C3-59: '// ... (kalan kodlar aynı)' içeren blok yazılmaz ve kısaltılmış olarak raporlanır."""
    out = "\n".join([
        "### `src/web/app.js`", "Düzeltilmiş tam dosya.", "", f"{FENCE}javascript", "// src/web/app.js",
        "export function a() { return 1; }", "// ... (kalan kodlar aynı)", FENCE, "",
        f"{FENCE}json recorion.json", '{"services": []}', FENCE,
    ])
    partials = []
    files = code_repo.files_from_output(T(), out, partials)
    assert "src/web/app.js" not in files
    assert partials == ["src/web/app.js"]
    assert files["recorion.json"] == '{"services": []}\n'


def test_full_and_partial_same_file_is_not_reported():
    """Aynı dosyanın tam hâli de verildiyse kısaltılmış uyarısı gerekmez (commit_step bunu süzer)."""
    out = "\n".join([
        f"{FENCE}javascript src/web/app.js", "export const a = 1;", FENCE, "",
        f"{FENCE}javascript src/web/app.js", "// ... değişmedi", FENCE,
    ])
    partials = []
    files = code_repo.files_from_output(T(), out, partials)
    assert files["src/web/app.js"] == "export const a = 1;\n"
    assert [p for p in partials if p not in files] == []


def test_partials_argument_is_optional():
    assert "src/a.py" in code_repo.files_from_output(T(), f"{FENCE}python src/a.py\nx = 1\n{FENCE}")
