"""Tests for cursor_bridge MCP dispatch."""


from jarvis.cursor_bridge import MCP_TOOLS, handle_mcp_tool, list_project_files


def test_mcp_tools_registered():
    names = {t["name"] for t in MCP_TOOLS}
    assert "jarvis_read_file" in names
    assert "jarvis_search_code" in names


def test_list_project_files(tmp_path):
    (tmp_path / "hello.py").write_text("print('hi')\n", encoding="utf-8")
    files = list_project_files(tmp_path, limit=10)
    assert "hello.py" in files


def test_handle_unknown_tool(tmp_path):
    result = handle_mcp_tool("no_such_tool", {}, tmp_path)
    assert "Unknown tool" in result.get("error", "")
