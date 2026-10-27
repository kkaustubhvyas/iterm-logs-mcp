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
- `open_iterm_window(cwd=None)` — opens a new iTerm2 window with the default profile and
  returns its `session_id`. If `cwd` is given, `cd`s into it first.
- `stop_iterm_process(session_id, timeout=5.0, force=False)` — sends Ctrl-C to that session and
  waits up to `timeout` seconds for it to return to its shell. With `force=True`, anything still
  running afterwards gets SIGTERM. Returns `stopped`, the `method` used, and any `remaining`
  processes. Running state comes from the tty's foreground process group (`ps`), not iTerm2's
  `jobName`, which can read `zsh` while a child is still running.
- `close_iterm_window(session_id, force=False)` — closes the whole window containing that
  session, all tabs included. Refuses and lists the busy sessions if any tab is still running
  something, unless `force=True`.

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
