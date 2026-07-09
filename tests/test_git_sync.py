"""Tests for git repository sync."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.knowledge.git_sync import GitRepoState, discover_repositories, list_repo_states, sync_all
from jarvis.knowledge.repo_index import build_repo_index, search_repo_index


class TestGitSync(unittest.TestCase):
    @patch("jarvis.knowledge.git_sync.is_repo", return_value=True)
    @patch("jarvis.knowledge.git_sync.discover_repositories")
    def test_sync_all_empty(self, mock_discover, _repo):
        mock_discover.return_value = []
        result = sync_all()
        self.assertTrue(result.get("ok"))

    def test_git_repo_state_retrieval(self):
        st = GitRepoState(
            id="abc",
            path="/tmp/r",
            label="test",
            chunk_count=10,
            indexing_status="indexed",
        )
        self.assertTrue(st.retrieval_available)

    @patch("jarvis.llm.embed_text", return_value=[0.1, 0.2])
    def test_build_and_search_repo_index(self, _embed):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "hello.py").write_text("def lite_llm_router():\n    return True\n", encoding="utf-8")
            index_path = root / "code_index.json"
            count = build_repo_index(root, index_path=index_path)
            self.assertGreater(count, 0)
            hits = search_repo_index(index_path, "lite_llm", limit=3)
            self.assertTrue(hits)

    def test_git_sync_actions_registered(self):
        from jarvis.behaviors import register_behaviors
        from jarvis.handlers.registry import has_action

        register_behaviors()
        self.assertTrue(has_action("git_sync"))
        self.assertTrue(has_action("git_sync_all"))


if __name__ == "__main__":
    unittest.main()
