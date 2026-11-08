"""Senaryo F87 (08.11.2026): devam parçaları birleştirilirken ek yerindeki örtüşme bir kez yazılır."""
from app.services.agent_work import join_pieces


def test_overlap_at_seam_written_once():
    assert join_pieces(["def f():\n    return", "return patients\n"]) == "def f():\n    return patients\n"
    assert join_pieces(["x = 1\nfor p in rows:\n    out.append(p)", "    out.append(p)\nreturn out"]) == \
        "x = 1\nfor p in rows:\n    out.append(p)\nreturn out"


F = "`" * 3


def test_reopened_block_with_devam_header_is_merged():
    """S2 v8/v9: devam parçası "## Devam" ya da "```python src/main.py (Devam)" ile yeni blok açıyordu."""
    a = f"Kod:\n{F}python src/main.py\ndef a():\n    return 1\n"
    b = f"## Devam\n\n{F}python src/main.py\ndef b():\n    return 2\n{F}\n"
    assert join_pieces([a, b]) == f"Kod:\n{F}python src/main.py\ndef a():\n    return 1\ndef b():\n    return 2\n{F}\n"
    g = f"{F}python src/main.py\ndef q(db):\n    cursor.execute(\"SELECT * FROM"
    h = f"{F}python src/main.py (Devam)\n    cursor.execute(\"SELECT * FROM patients\")\n    return cursor.fetchall()\n{F}\n"
    assert join_pieces([g, h]) == f"{F}python src/main.py\ndef q(db):\n    cursor.execute(\"SELECT * FROM patients\")\n    return cursor.fetchall()\n{F}\n"
    i = f"{F}python a.py\nx = foo(1,"
    assert join_pieces([i, f"{F}python a.py (Devam)\n 2)\n{F}\n"]) == f"{F}python a.py\nx = foo(1, 2)\n{F}\n"


def test_new_block_after_closed_block_and_plain_continuation_are_kept():
    c = f"{F}python a.py\nx=1\n{F}\n"
    d = f"## Devam\n{F}python b.py\ny=2\n{F}\n"
    assert join_pieces([c, d]) == c + d
    e = f"{F}python a.py\nx=1\n"
    f = f"y=2\n{F}\n\nAçıklama"
    assert join_pieces([e, f]) == e + f


def test_no_overlap_keeps_pieces_intact():
    assert join_pieces(["a = 1\n", "b = 2\n"]) == "a = 1\nb = 2\n"
    assert join_pieces(["return x", "y + 1"]) == "return xy + 1"  # kısa (5'ten az) rastlantısal eşleşme kırpılmaz
    assert join_pieces(["tek parça"]) == "tek parça"
    assert join_pieces([]) == ""
