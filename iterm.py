"""AppleScript wrappers for reading iTerm2 window/tab/session state."""

import subprocess

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

_GET_CONTENTS_SCRIPT = """
on run argv
    set targetId to item 1 of argv
    tell application "iTerm2"
        set targetSession to missing value
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    if (id of s) is targetId then
                        set targetSession to s
                    end if
                end repeat
            end repeat
        end repeat
        if targetSession is missing value then
            error "No iTerm2 session found with id " & targetId
        end if
        return contents of targetSession
    end tell
end run
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
