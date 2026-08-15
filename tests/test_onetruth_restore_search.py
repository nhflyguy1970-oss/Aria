"""Cross-system one-truth: restore repairs Chat; Search corpora include gallery+chat."""

from __future__ import annotations


def test_search_default_includes_gallery_and_chat():
    from jarvis.search_product.settings import enabled_corpora_set
    from jarvis.search_product.terminology import FACETS

    enabled = enabled_corpora_set()
    assert "gallery" in enabled
    assert "chat" in enabled
    assert "chat" in FACETS
    assert "gallery" in FACETS


def test_restore_chat_gallery_refs_roundtrip(tmp_path, monkeypatch):
    import json

    from jarvis.branches import BRANCHES_FILE
    from jarvis.gallery_product import consistency as cons

    monkeypatch.setattr(cons, "_walk_branch_messages", cons._walk_branch_messages)
    # Use disk path: force assistant path to fail by patching get_assistant
    import jarvis.assistant_instance as ai

    def boom():
        raise RuntimeError("no assistant")

    monkeypatch.setattr(ai, "get_assistant", boom)

    data = {
        "active": "main",
        "branches": {
            "main": {
                "name": "Main",
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Here\n\n![generated](/api/gallery/demo.png)",
                    }
                ],
            }
        },
    }
    BRANCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    BRANCHES_FILE.write_text(json.dumps(data), encoding="utf-8")

    scrub = cons.scrub_chat_gallery_refs("demo.png")
    assert scrub.get("scrubbed", 0) >= 1
    after = json.loads(BRANCHES_FILE.read_text(encoding="utf-8"))
    text = after["branches"]["main"]["messages"][0]["content"]
    assert "/api/gallery/demo.png" not in text
    assert "removed from Gallery" in text

    restored = cons.restore_chat_gallery_refs("demo.png", restored_name="demo.png")
    assert restored.get("restored", 0) >= 1
    after2 = json.loads(BRANCHES_FILE.read_text(encoding="utf-8"))
    text2 = after2["branches"]["main"]["messages"][0]["content"]
    assert "![generated](/api/gallery/demo.png)" in text2
    assert "removed from Gallery" not in text2
