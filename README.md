# iterm-logs-mcp

Local MCP server exposing iTerm2 tab/session logs to any MCP-capable agent. Reads terminal
state via AppleScript — the agent decides which tab to read by matching on `cwd`/`job`, no
built-in fuzzy-matching logic on the server side.

macOS + iTerm2 only. Local stdio server — not deployed anywhere.

## Tools

- `list_iterm_tabs()` — enumerates every open window/tab/session: `session_id`, `window_index`,
  `tab_index`, `name`, `tty`, `cwd`, `job`.
- `get_iterm_tab_logs(session_id, max_lines=500)` — returns the last `max_lines` lines of
  scrollback for that session.
- `send_iterm_command(session_id, command, press_enter=True)` — types `command` into that
  session and presses Enter (unless `press_enter=False`). Doesn't wait for output; follow up
  with `get_iterm_tab_logs`. This runs arbitrary commands in your real terminals — keep the
  tool on "ask" in your MCP client rather than auto-approving it.

## First run

The first AppleScript call against iTerm2 triggers a one-time macOS Automation permission
prompt for whichever process runs this script (Terminal, iTerm2, or your MCP client host).
Grant it once in System Settings → Privacy & Security → Automation.

## Run it

```bash
uv run --directory /path/to/iterm-logs-mcp server.py
```

## Register with Claude Code

```bash
claude mcp add iterm-logs -- uv run --directory /path/to/iterm-logs-mcp server.py
```

## Register with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "iterm-logs": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/iterm-logs-mcp",
        "server.py"
      ]
    }
  }
}
```
