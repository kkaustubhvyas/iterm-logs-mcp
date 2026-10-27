"""AppleScript wrappers for reading iTerm2 window/tab/session state and sending input."""

import os
import shlex
import signal
import subprocess
import time

RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"

_LIST_SESSIONS_SCRIPT = f"""
tell application "iTerm2"
    set out to ""
    set winIdx to 0
    repeat with w in windows
        set winIdx to winIdx + 1
        set tabIdx to 0
        repeat with t in tabs of w
            set tabIdx to tabIdx + 1
            repeat with s in sessions of t
                set sid to (id of s)
                set sname to (name of s)
                set stty to (tty of s)
                tell s
                    try
                        set scwd to (variable named "session.path")
                    on error
                        set scwd to ""
                    end try
                    try
                        set sjob to (variable named "jobName")
                    on error
                        set sjob to ""
                    end try
                end tell
                set out to out & winIdx & "{FIELD_SEP}" & tabIdx & "{FIELD_SEP}" & sid & "{FIELD_SEP}" & sname & "{FIELD_SEP}" & stty & "{FIELD_SEP}" & scwd & "{FIELD_SEP}" & sjob & "{RECORD_SEP}"
            end repeat
        end repeat
    end repeat
    return out
end tell
"""

_FIND_SESSION_HANDLER = """
on findSession(targetId)
    tell application "iTerm2"
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    if (id of s) is targetId then return s
                end repeat
            end repeat
        end repeat
    end tell
    error "No iTerm2 session found with id " & targetId
end findSession
"""

_GET_CONTENTS_SCRIPT = _FIND_SESSION_HANDLER + """
on run argv
    set targetSession to findSession(item 1 of argv)
    tell application "iTerm2" to return contents of targetSession
end run
"""

_WRITE_TEXT_SCRIPT = _FIND_SESSION_HANDLER + """
on run argv
    set targetSession to findSession(item 1 of argv)
    set textToSend to item 2 of argv
    set pressEnter to (item 3 of argv) is "1"
    tell application "iTerm2"
        tell targetSession to write text textToSend newline pressEnter
    end tell
end run
"""

_CLOSE_WINDOW_SCRIPT = """
on run argv
    set targetId to item 1 of argv
    tell application "iTerm2"
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    if (id of s) is targetId then
                        close w
                        return
                    end if
                end repeat
            end repeat
        end repeat
    end tell
    error "No iTerm2 session found with id " & targetId
end run
"""

_CREATE_WINDOW_SCRIPT = """
tell application "iTerm2"
    set newWindow to (create window with default profile)
    return id of (current session of newWindow)
end tell
"""


def _run_osascript(script: str, args: list[str] | None = None) -> str:
    result = subprocess.run(
        ["osascript", "-e", script, *(args or [])],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "osascript failed")
    return result.stdout


def list_sessions() -> list[dict]:
    raw = _run_osascript(_LIST_SESSIONS_SCRIPT)
    sessions = []
    for record in raw.split(RECORD_SEP):
        if not record.strip():
            continue
        fields = record.split(FIELD_SEP)
        if len(fields) != 7:
            continue
        window_index, tab_index, session_id, name, tty, cwd, job = fields
        sessions.append(
            {
                "session_id": session_id,
                "window_index": int(window_index),
                "tab_index": int(tab_index),
                "name": name,
                "tty": tty,
                "cwd": cwd,
                "job": job,
            }
        )
    return sessions


def get_session_contents(session_id: str, max_lines: int = 500) -> str:
    raw = _run_osascript(_GET_CONTENTS_SCRIPT, [session_id])
    # "contents" is the full screen buffer, padded with blank rows below the
    # cursor to fill the visible height — trim that padding before tailing.
    text = raw.rstrip("\n ")
    if max_lines <= 0:
        return text
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


def send_text(session_id: str, text: str, press_enter: bool = True) -> None:
    # Passed via argv rather than interpolated, so quotes/backslashes in the
    # command can't break out of the AppleScript string.
    _run_osascript(_WRITE_TEXT_SCRIPT, [session_id, text, "1" if press_enter else "0"])


def create_window(cwd: str | None = None) -> str:
    session_id = _run_osascript(_CREATE_WINDOW_SCRIPT).strip()
    if cwd:
        send_text(session_id, f"cd {shlex.quote(cwd)}")
    return session_id


def _find_session(session_id: str) -> dict:
    for session in list_sessions():
        if session["session_id"] == session_id:
            return session
    raise RuntimeError(f"No iTerm2 session found with id {session_id}")


def running_processes(tty: str) -> list[dict]:
    """Foreground processes on tty other than the session's shell.

    A '+' in ps stat marks the foreground process group. The shell is the
    process started from outside the tty, either directly by iTerm2 or via the
    `login` session leader ('s' in stat). An idle tab has only the shell in the
    foreground, so anything else means a command is still running. More
    reliable than iTerm2's jobName, which can report the shell while a child
    is running.
    """
    result = subprocess.run(
        ["ps", "-t", tty.removeprefix("/dev/"), "-o", "pid=,ppid=,stat=,command="],
        capture_output=True,
        text=True,
    )
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4:
            pid, ppid, stat, command = parts
            rows.append((int(pid), int(ppid), stat, command))
    on_tty = {pid for pid, _, _, _ in rows}
    leaders = {pid for pid, _, stat, _ in rows if "s" in stat}
    return [
        {"pid": pid, "command": command}
        for pid, ppid, stat, command in rows
        if "+" in stat and ppid in on_tty and ppid not in leaders
    ]


def _wait_until_idle(tty: str, timeout: float) -> list[dict]:
    deadline = time.monotonic() + timeout
    while True:
        remaining = running_processes(tty)
        if not remaining or time.monotonic() >= deadline:
            return remaining
        time.sleep(0.25)


def stop_process(session_id: str, timeout: float = 5.0, force: bool = False) -> dict:
    tty = _find_session(session_id)["tty"]
    if not running_processes(tty):
        return {"stopped": True, "method": "none", "remaining": []}
    send_text(session_id, "\x03", press_enter=False)
    remaining = _wait_until_idle(tty, timeout)
    if not remaining:
        return {"stopped": True, "method": "ctrl-c", "remaining": []}
    if not force:
        return {"stopped": False, "method": "ctrl-c", "remaining": remaining}
    for process in remaining:
        try:
            os.kill(process["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
    remaining = _wait_until_idle(tty, timeout)
    return {"stopped": not remaining, "method": "sigterm", "remaining": remaining}


def close_window(session_id: str, force: bool = False) -> dict:
    target = _find_session(session_id)
    window_sessions = [
        s for s in list_sessions() if s["window_index"] == target["window_index"]
    ]
    busy = {
        s["session_id"]: procs
        for s in window_sessions
        if (procs := running_processes(s["tty"]))
    }
    if busy and not force:
        return {"closed": False, "sessions": len(window_sessions), "busy": busy}
    _run_osascript(_CLOSE_WINDOW_SCRIPT, [session_id])
    return {"closed": True, "sessions": len(window_sessions), "busy": busy}
