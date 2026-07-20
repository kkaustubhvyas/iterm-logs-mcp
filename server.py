"""MCP server exposing iTerm2 tab/session logs to agents."""

from mcp.server.fastmcp import FastMCP

import iterm

mcp = FastMCP("iterm-logs")


@mcp.tool()
def list_iterm_tabs() -> list[dict]:
    """List every open iTerm2 window/tab/session with its cwd and running job,
    so the caller can pick which one to read logs from."""
    return iterm.list_sessions()


@mcp.tool()
def get_iterm_tab_logs(session_id: str, max_lines: int = 500) -> str:
    """Get scrollback/log contents for one iTerm2 session, identified by the
    session_id returned from list_iterm_tabs. Returns the last max_lines lines."""
    return iterm.get_session_contents(session_id, max_lines)


if __name__ == "__main__":
    mcp.run()
