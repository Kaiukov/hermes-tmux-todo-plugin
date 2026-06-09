"""Tmux runtime adapter — orchestrate AI coding agents in tmux sessions.

Supports OpenCode, Codex, and Claude with monitor-silence completion
detection and literal-mode prompt delivery (no shell interpretation).
"""

import subprocess
import time


class TmuxRuntimeError(Exception):
    """Tmux command failure (session not found, tmux not installed, etc.)."""


class TmuxRuntimeAdapter:
    """Tmux-based AI agent orchestrator.

    Usage:
        tmux = TmuxRuntimeAdapter()
        tmux.ensure_session("agent")
        info = tmux.open_worker("refactor auth", backend="opencode")
        time.sleep(12)  # wait for TUI init
        tmux.send(info["target"], "Implement JWT auth")
        print(tmux.capture_tail(info["target"], lines=20))
        tmux.kill_session("agent")
    """

    BACKENDS = {
        "opencode": {
            "cmd": "opencode --model opencode/deepseek-v4-flash-free",
            "enter": "C-m",
        },
        "codex": {"cmd": "codex", "enter": "Enter"},
        "claude": {"cmd": "claude --dangerously-skip-permissions", "enter": "Enter"},
    }

    def __init__(self, silence_timeout: int = 5):
        self.silence_timeout = silence_timeout

    def _tmux(self, *args: str) -> str:
        try:
            r = subprocess.run(
                ["tmux", *args],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            raise TmuxRuntimeError("tmux not found — is it installed?")
        except subprocess.TimeoutExpired:
            raise TmuxRuntimeError(f"tmux timed out: {' '.join(args)}")
        if r.returncode != 0:
            raise TmuxRuntimeError(
                f"tmux {' '.join(args)} failed: {r.stderr.strip()}"
            )
        return r.stdout

    def has_session(self, name: str) -> bool:
        try:
            self._tmux("has-session", "-t", name)
            return True
        except TmuxRuntimeError:
            return False

    def ensure_session(self, name: str) -> dict:
        if self.has_session(name):
            return {"session": name, "created": False, "status": "exists"}
        self._tmux("new-session", "-d", "-s", name, "-x", "140", "-y", "40")
        self._tmux("set", "-t", name, "monitor-silence", str(self.silence_timeout))
        return {"session": name, "created": True, "status": "ready"}

    def kill_session(self, name: str) -> dict:
        try:
            self._tmux("kill-session", "-t", name)
            return {"session": name, "status": "killed"}
        except TmuxRuntimeError:
            return {"session": name, "status": "not_found"}

    def open_worker(self, task: str, backend: str = "opencode") -> dict:
        backend = backend.lower()
        if backend not in self.BACKENDS:
            raise TmuxRuntimeError(
                f"Unknown backend '{backend}'. Options: {', '.join(self.BACKENDS)}"
            )
        cfg = self.BACKENDS[backend]
        name = _sanitize(task)
        self._tmux("new-window", "-d", "-n", name)
        self._tmux("set", "-t", name, "monitor-silence", str(self.silence_timeout))
        self._tmux("send-keys", "-t", name, cfg["cmd"], "Enter")
        return {"target": name, "backend": backend, "task": task, "status": "launched"}

    def rename(self, target: str, name: str) -> dict:
        self._tmux("rename-window", "-t", target, name)
        return {"target": target, "new_name": name, "status": "renamed"}

    def send(self, target: str, text: str) -> dict:
        """Send prompt text using literal mode (-l), chunked for safety."""
        chunk_size = 1000
        total = len(text)
        for i in range(0, total, chunk_size):
            chunk = text[i : i + chunk_size]
            self._tmux("send-keys", "-t", target, "-l", chunk)
            if i + chunk_size < total:
                self._tmux("send-keys", "-t", target, "Enter")
                time.sleep(0.05)
        self._tmux("send-keys", "-t", target, "C-m")
        return {"target": target, "chars_sent": total, "status": "sent"}

    def capture_tail(self, target: str, lines: int = 40) -> str:
        return self._tmux("capture-pane", "-t", target, "-p", "-S", f"-{lines}")

    def list_windows(self, session: str | None = None) -> list[dict]:
        """List windows with flags for silence/activity detection."""
        args = ["-t", session] if session else []
        args += ["-F", "#{window_name}\t#{window_flags}"]
        return [
            {"name": n, "flags": f}
            for line in self._tmux(*args).strip().split("\n")
            if "\t" in line
            for n, f in [line.split("\t", 1)]
        ]

    def check_silence(self, target: str) -> bool:
        """Check if monitor-silence (~ flag) triggered for a window."""
        return any(
            w["name"] == target and "~" in w["flags"]
            for w in self.list_windows()
        )

    def wait_for_silence(
        self, target: str, timeout: int = 300, interval: int = 3
    ) -> dict:
        """Poll until monitor-silence fires or timeout."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self.check_silence(target):
                return {"status": "silence_detected", "elapsed": time.monotonic() - start}
            time.sleep(interval)
        return {"status": "timeout", "elapsed": time.monotonic() - start}


def _sanitize(task: str, max_len: int = 40) -> str:
    safe = "".join(c if c.isalnum() or c in " _-" else " " for c in task)
    return safe.strip().replace(" ", "-")[:max_len] or "worker"
