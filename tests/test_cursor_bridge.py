# Source Generated with Decompyle++
# File: test_cursor_bridge.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for cursor_bridge MCP dispatch.'''
import builtins as @py_builtins

rewrite
from jarvis.cursor_bridge import MCP_TOOLS, _CODING_MCP_TOOL_NAMES, discover_mcp_server_tool_names, handle_mcp_tool, list_project_files
_CODING_MCP_TOOL_NAMES = _CODING_MCP_TOOL_NAMES
discover_mcp_server_tool_names = discover_mcp_server_tool_names
handle_mcp_tool = handle_mcp_tool
list_project_files = list_project_files
import _pytest.assertion.rewrite, assertion

def test_mcp_tools_registered():
    pass
# WARNING: Decompyle incomplete


def test_list_project_files(tmp_path):
    (tmp_path / 'hello.py').write_text("print('hi')\n", encoding = 'utf-8')
    files = list_project_files(tmp_path, limit = 10)
    @py_assert0 = 'hello.py'
    @py_assert2 = @py_assert0 in files
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, files)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(files) if 'files' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(files) else 'files' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_handle_unknown_tool(tmp_path):
    result = handle_mcp_tool('no_such_tool', { }, tmp_path)
    @py_assert0 = 'Unknown tool'
    @py_assert4 = result.get
    @py_assert6 = 'error'
    @py_assert8 = ''
    @py_assert10 = @py_assert4(@py_assert6, @py_assert8)
    @py_assert2 = @py_assert0 in @py_assert10
    if not @py_assert2:
        @py_format12 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py11)s\n{%(py11)s = %(py5)s\n{%(py5)s = %(py3)s.get\n}(%(py7)s, %(py9)s)\n}',), (@py_assert0, @py_assert10)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None


def test_server_tools_subset_of_dispatch_registry():
    _DOMAIN_MCP_TOOLS = _DOMAIN_MCP_TOOLS
    import jarvis.cursor_bridge
    server_names = discover_mcp_server_tool_names()
    dispatch = _CODING_MCP_TOOL_NAMES | _DOMAIN_MCP_TOOLS
    @py_assert1 = server_names == dispatch
    if not @py_assert1:
        @py_format3 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py2)s',), (server_names, dispatch)) % {
            'py0': @pytest_ar._saferepr(server_names) if 'server_names' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(server_names) else 'server_names',
            'py2': @pytest_ar._saferepr(dispatch) if 'dispatch' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(dispatch) else 'dispatch' }
        @py_format5 = 'assert %(py4)s' % {
            'py4': @py_format3 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert2 = len(server_names)
    @py_assert5 = 52
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(server_names) if 'server_names' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(server_names) else 'server_names',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None

