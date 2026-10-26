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


@mcp.tool()
def send_iterm_command(session_id: str, command: str, press_enter: bool = True) -> str:
    """Type text into one iTerm2 session, identified by the session_id returned
    from list_iterm_tabs, and press Enter unless press_enter is false. Returns
    immediately — read the output afterwards with get_iterm_tab_logs."""
    iterm.send_text(session_id, command, press_enter)
    return f"Sent to session {session_id}"


@mcp.tool()
def open_iterm_window(cwd: str | None = None) -> str:
    """Open a new iTerm2 window with the default profile and return the
    session_id of its shell. If cwd is given, cd into it first. Use the
    returned session_id with send_iterm_command / get_iterm_tab_logs."""
    return iterm.create_window(cwd)


if __name__ == "__main__":
    mcp.run()
