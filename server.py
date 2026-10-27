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



@mcp.tool()
def stop_iterm_process(session_id: str, timeout: float = 5.0, force: bool = False) -> dict:
    """Stop whatever is running in the foreground of one iTerm2 session by
    sending Ctrl-C, then wait up to timeout seconds for the tab to return to
    its shell. If it is still running and force is true, send SIGTERM to the
    remaining foreground processes and wait again. Returns stopped (bool),
    method used, and any processes still running."""
    return iterm.stop_process(session_id, timeout, force)


@mcp.tool()
def close_iterm_window(session_id: str, force: bool = False) -> dict:
    """Close the iTerm2 window that contains session_id, including all of its
    tabs. Refuses (closed=false, with the busy sessions listed) if any tab in
    the window is still running a process, unless force is true — stop them
    first with stop_iterm_process."""
    return iterm.close_window(session_id, force)


if __name__ == "__main__":
    mcp.run()
