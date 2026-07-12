from __future__ import annotations

import asyncio
import shlex
from typing import Callable, Dict, Optional, Tuple, Union

from e2b import Sandbox
from e2b.sandbox.commands.command_handle import CommandExitException

from codeforge.config import settings
from codeforge.schemas import ToolResult

APP_ROOT = "/home/user"
MAX_OUTPUT = 4000
EXCLUDED = {"node_modules", ".next", ".git", "dist", "build"}
_terminal_cwd: Dict[str, str] = {}
_project_dirs: Dict[str, str] = {}


def _is_ignored_file(rel: str) -> bool:
    parts = rel.split("/")
    if not parts or parts[0] in EXCLUDED:
        return True
    return any(p.startswith(".") for p in parts)


def _cache_project_dir(sandbox_id: str, path: str) -> None:
    top = path.split("/")[0]
    if not top or top.startswith("."):
        return
    _project_dirs[sandbox_id] = f"{APP_ROOT}/{top}"


def truncate(text: str, max_len: int = MAX_OUTPUT) -> str:
    if len(text) <= max_len:
        return text
    return f"...[truncated {len(text) - max_len} chars]\n{text[-max_len:]}"


def format_command_output(
    stdout: str,
    stderr: str,
    exit_code: int,
    error: Optional[str] = None,
) -> str:
    parts = [f"exit_code: {exit_code}"]
    if stdout:
        parts.append(f"stdout:\n{stdout}")
    if stderr:
        parts.append(f"stderr:\n{stderr}")
    if error:
        parts.append(f"error: {error}")
    if exit_code != 0 and not stdout and not stderr and not error:
        parts.append("(no output captured)")
    return truncate("\n".join(parts))


def format_terminal_output(
    stdout: str,
    stderr: str,
    exit_code: int,
    error: Optional[str] = None,
) -> str:
    """Console-friendly output — no exit_code/stdout labels."""
    parts = [stdout.rstrip("\n"), stderr.rstrip("\n")]
    if error:
        parts.append(error.rstrip("\n"))
    combined = "\n".join(p for p in parts if p)
    if not combined and exit_code != 0:
        combined = f"Command failed (exit {exit_code})"
    return truncate(combined)


def terminal_prompt(cwd: str) -> str:
    if cwd == APP_ROOT:
        return "~"
    rel = cwd.removeprefix(f"{APP_ROOT}/")
    return f"~/{rel}" if rel else "~"


def get_terminal_cwd(session_id: str) -> str:
    return _terminal_cwd.get(session_id, APP_ROOT)


def _resolve_cd(cwd: str, target: str) -> Optional[str]:
    if not target or target == "~":
        return APP_ROOT
    parts = (target if target.startswith("/") else f"{cwd}/{target}").split("/")
    stack: list[str] = []
    for part in parts:
        if not part or part == ".":
            continue
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)
    clean = "/" + "/".join(stack) if stack else "/"
    if clean != APP_ROOT and not clean.startswith(f"{APP_ROOT}/"):
        return None
    return clean


def normalize_path(rel: str) -> str:
    """Project-relative path (no /home/user prefix)."""
    clean = rel.strip().replace("\\", "/").removeprefix("./")
    for prefix in (f"{APP_ROOT}/", APP_ROOT, "home/user/", "/home/user/"):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    clean = clean.lstrip("/")
    if ".." in clean.split("/"):
        raise ValueError(f"Invalid path: {rel}")
    return clean


def resolve_path(rel: str) -> str:
    clean = normalize_path(rel)
    return f"{APP_ROOT}/{clean}" if clean else APP_ROOT


class E2BSandbox:
    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox
        self.dev_log = ""
        self.dev_handle = None
        self.project_dir: Optional[str] = None

    @classmethod
    async def connect_or_create(
        cls,
        sandbox_id: Optional[str],
        template: str,
        on_created: Optional[Callable[[str], Union[asyncio.Future, object]]] = None,
    ) -> Tuple["E2BSandbox", str]:
        if sandbox_id:
            try:
                sbx = await asyncio.to_thread(Sandbox.connect, sandbox_id)
                return cls(sbx), sbx.sandbox_id
            except Exception:
                pass

        sbx = await asyncio.to_thread(
            Sandbox.create,
            template,
            timeout=30 * 60,
        )
        if on_created:
            result = on_created(sbx.sandbox_id)
            if asyncio.iscoroutine(result):
                await result
        return cls(sbx), sbx.sandbox_id

    async def preview_url_live(self) -> Optional[str]:
        if await self._is_port_responding(3000):
            return f"https://{self.sandbox.get_host(3000)}"
        return None

    async def write_file(self, path: str, content: str) -> ToolResult:
        try:
            full = resolve_path(path)
            await asyncio.to_thread(self.sandbox.files.write, full, content)
            rel = normalize_path(path)
            _cache_project_dir(self.sandbox.sandbox_id, rel)
            return ToolResult(output=f"Wrote {rel} ({len(content)} bytes)", changed_paths=[rel])
        except Exception as e:
            return ToolResult(output=str(e), is_error=True)

    async def edit_file(self, path: str, old_str: str, new_str: str) -> ToolResult:
        try:
            full = resolve_path(path)
            content = await asyncio.to_thread(self.sandbox.files.read, full)
            count = content.count(old_str)
            if count == 0:
                return ToolResult(output=f"old_str not found in {path}", is_error=True)
            if count > 1:
                return ToolResult(output=f"old_str matches {count} times — must be unique", is_error=True)
            updated = content.replace(old_str, new_str, 1)
            await asyncio.to_thread(self.sandbox.files.write, full, updated)
            rel = normalize_path(path)
            _cache_project_dir(self.sandbox.sandbox_id, rel)
            return ToolResult(output=f"Edited {rel}", changed_paths=[rel])
        except Exception as e:
            return ToolResult(output=str(e), is_error=True)

    async def read_file(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> ToolResult:
        try:
            full = resolve_path(path)
            content = await asyncio.to_thread(self.sandbox.files.read, full)
            lines = content.split("\n")
            start = (start_line or 1) - 1
            end = end_line or len(lines)
            numbered = "\n".join(
                f"{str(i + 1).rjust(4)}| {line}" for i, line in enumerate(lines[start:end], start=start)
            )
            return ToolResult(output=numbered)
        except Exception as e:
            return ToolResult(output=str(e), is_error=True)

    async def _scan_files(self, root: str, *, maxdepth: Optional[int] = None) -> list[str]:
        depth = f"-maxdepth {maxdepth} " if maxdepth else ""
        try:
            result = await asyncio.to_thread(
                self.sandbox.commands.run,
                f'find "{root}" {depth}-type f '
                f'! -path "*/node_modules/*" ! -path "*/.next/*" ! -path "*/.git/*" '
                f'2>/dev/null | head -1000',
                timeout=30,
            )
            paths: list[str] = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rel = normalize_path(line)
                except ValueError:
                    continue
                if _is_ignored_file(rel):
                    continue
                paths.append(rel)
            return sorted(set(paths))
        except Exception:
            return []

    async def list_project_files(self) -> list[str]:
        project = await self._find_project_dir()
        if project != APP_ROOT:
            return await self._scan_files(project)

        # ponytail: never list /home/user dotfiles — scan known project roots only
        paths: list[str] = []
        for root in await self._project_roots():
            paths.extend(await self._scan_files(root))
        return sorted(set(paths))

    async def _project_roots(self) -> list[str]:
        roots: list[str] = []
        try:
            r = await asyncio.to_thread(
                self.sandbox.commands.run,
                f'find {APP_ROOT} -maxdepth 4 -name package.json ! -path "*/node_modules/*" 2>/dev/null',
                timeout=15,
            )
            for line in r.stdout.splitlines():
                pkg = line.strip()
                if not pkg:
                    continue
                root = pkg.rsplit("/package.json", 1)[0]
                if root != APP_ROOT and root not in roots:
                    roots.append(root)
        except Exception:
            pass
        return roots

    async def list_files(self, path: str = ".") -> ToolResult:
        try:
            base = resolve_path("" if path == "." else path)
            lines = await self._scan_files(base, maxdepth=4)
            return ToolResult(output="\n".join(lines) or "(empty)")
        except Exception as e:
            return ToolResult(output=str(e), is_error=True)

    async def run_command(self, command: str, timeout_s: int = 120) -> ToolResult:
        try:
            result = await asyncio.to_thread(
                self.sandbox.commands.run,
                command,
                cwd=APP_ROOT,
                timeout=timeout_s,
            )
            return ToolResult(
                output=format_command_output(
                    result.stdout, result.stderr, result.exit_code, result.error,
                ),
                is_error=False,
            )
        except CommandExitException as e:
            return ToolResult(
                output=format_command_output(e.stdout, e.stderr, e.exit_code, e.error),
                is_error=True,
            )
        except Exception as e:
            return ToolResult(output=str(e), is_error=True)

    async def run_terminal(self, session_id: str, command: str, timeout_s: int = 120) -> ToolResult:
        cwd = _terminal_cwd.get(session_id, APP_ROOT)
        cmd = command.strip()
        if not cmd:
            return ToolResult(output="", is_error=False)

        # ponytail: only bare `cd` updates persisted cwd; compound shells run once
        if cmd == "cd" or (cmd.startswith("cd ") and not any(x in cmd for x in ("&&", ";", "|", "`"))):
            target = cmd[2:].strip() if cmd != "cd" else ""
            new_cwd = _resolve_cd(cwd, target)
            if not new_cwd:
                return ToolResult(
                    output=f"cd: {target or '~'}: No such file or directory",
                    is_error=True,
                )
            try:
                check = await asyncio.to_thread(
                    self.sandbox.commands.run,
                    f"test -d {shlex.quote(new_cwd)}",
                    timeout=5,
                )
                if check.exit_code != 0:
                    return ToolResult(
                        output=f"cd: {target or '~'}: No such file or directory",
                        is_error=True,
                    )
            except CommandExitException:
                return ToolResult(
                    output=f"cd: {target or '~'}: No such file or directory",
                    is_error=True,
                )
            _terminal_cwd[session_id] = new_cwd
            return ToolResult(output="", is_error=False)

        shell_cmd = f"bash -lc {shlex.quote(cmd)}"
        try:
            result = await asyncio.to_thread(
                self.sandbox.commands.run,
                shell_cmd,
                cwd=cwd,
                timeout=timeout_s,
            )
            return ToolResult(
                output=format_terminal_output(
                    result.stdout, result.stderr, result.exit_code, result.error,
                ),
                is_error=result.exit_code != 0,
            )
        except CommandExitException as e:
            return ToolResult(
                output=format_terminal_output(e.stdout, e.stderr, e.exit_code, e.error),
                is_error=True,
            )
        except Exception as e:
            return ToolResult(output=str(e), is_error=True)

    async def _find_project_dir(self) -> str:
        sid = self.sandbox.sandbox_id
        cached = _project_dirs.get(sid)
        if cached:
            self.project_dir = cached
            return cached
        if self.project_dir and self.project_dir != APP_ROOT:
            return self.project_dir

        candidates: list[tuple[int, int, str]] = []
        try:
            r = await asyncio.to_thread(
                self.sandbox.commands.run,
                f'find {APP_ROOT} -maxdepth 5 -name package.json ! -path "*/node_modules/*" 2>/dev/null',
                timeout=15,
            )
            for line in r.stdout.splitlines():
                pkg = line.strip()
                if not pkg:
                    continue
                try:
                    content = await asyncio.to_thread(self.sandbox.files.read, pkg)
                except Exception:
                    continue
                root = pkg.rsplit("/package.json", 1)[0]
                if root == APP_ROOT:
                    continue
                score = 0
                if "next" in content:
                    score += 3
                if "vite" in content:
                    score += 3
                if '"dev"' in content:
                    score += 2
                if "react" in content:
                    score += 1
                candidates.append((score, root.count("/"), root))
        except Exception:
            pass

        if candidates:
            candidates.sort(key=lambda x: (-x[0], x[1]))
            self.project_dir = candidates[0][2]
            _project_dirs[sid] = self.project_dir
            return self.project_dir

        self.project_dir = APP_ROOT
        return APP_ROOT

    async def _is_port_listening(self, port: int) -> bool:
        try:
            r = await asyncio.to_thread(
                self.sandbox.commands.run,
                f"ss -tlnH 'sport = :{port}' 2>/dev/null | head -1",
                timeout=5,
            )
            line = r.stdout.strip()
            # E2B port forwarding needs 0.0.0.0, not localhost-only
            return bool(line) and ("0.0.0.0" in line or "*:" in line or "[::]:" in line)
        except Exception:
            return False

    async def _is_port_responding(self, port: int) -> bool:
        if not await self._is_port_listening(port):
            return False
        try:
            r = await asyncio.to_thread(
                self.sandbox.commands.run,
                f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null || echo 000",
                timeout=5,
            )
            code = r.stdout.strip()
            return code not in ("", "000")
        except Exception:
            return False


    async def _dev_start_command(self, project: str) -> str:
        try:
            pkg = await asyncio.to_thread(self.sandbox.files.read, f"{project}/package.json")
            if "next" in pkg:
                return "npx next dev -H 0.0.0.0 -p 3000"
            if "vite" in pkg:
                return "npx vite --host 0.0.0.0 --port 3000"
        except Exception:
            pass
        return "npm run dev -- --hostname 0.0.0.0 --port 3000"

    async def _clear_port(self, port: int) -> None:
        try:
            await asyncio.to_thread(
                self.sandbox.commands.run,
                f"fuser -k {port}/tcp 2>/dev/null; pkill -f 'next dev' 2>/dev/null; pkill -f 'vite' 2>/dev/null; true",
                timeout=10,
            )
        except CommandExitException:
            pass

    def _log_has_fatal_error(self) -> Optional[str]:
        log = self.dev_log.lower()
        for needle in ("enoent", "missing script", "cannot find module", "command not found", "npm err!"):
            if needle in log:
                return needle
        return None

    async def start_dev_server(self) -> ToolResult:
        url = await self.preview_url_live()
        if url:
            return ToolResult(output=f"Dev server already running at {url}", preview_url=url)

        project = await self._find_project_dir()
        cmd = await self._dev_start_command(project)
        self.dev_log = ""
        await self._clear_port(3000)

        def on_stdout(data: str) -> None:
            self.dev_log += data

        def on_stderr(data: str) -> None:
            self.dev_log += data

        try:
            self.dev_handle = await asyncio.to_thread(
                self.sandbox.commands.run,
                cmd,
                cwd=project,
                background=True,
                envs={"HOSTNAME": "0.0.0.0", "PORT": "3000"},
                on_stdout=on_stdout,
                on_stderr=on_stderr,
            )
        except Exception as e:
            return ToolResult(output=truncate(f"Failed to launch dev server: {e}\n{self.dev_log}"), is_error=True)

        # ponytail: 90s cap; port must listen on 0.0.0.0, not log heuristics alone
        for _ in range(45):
            fatal = self._log_has_fatal_error()
            if fatal:
                return ToolResult(
                    output=truncate(f"Dev server failed ({fatal}).\n{self.dev_log}"),
                    is_error=True,
                )
            if await self._is_port_responding(3000):
                await asyncio.sleep(1)
                url = await self.preview_url_live()
                if url:
                    return ToolResult(output=f"Dev server ready at {url}", preview_url=url)
            await asyncio.sleep(2)

        return ToolResult(
            output=truncate(f"Dev server timed out after 90s in {project}.\n{self.dev_log}"),
            is_error=True,
        )

    async def get_dev_server_logs(self, lines: int = 50) -> ToolResult:
        log = "\n".join(self.dev_log.split("\n")[-lines:])
        return ToolResult(output=log or "(no logs yet)")

    async def check_project(self) -> ToolResult:
        project = await self._find_project_dir()
        tsc_code = 0
        try:
            tsc = await asyncio.to_thread(
                self.sandbox.commands.run,
                "npx tsc --noEmit 2>&1",
                cwd=project,
                timeout=120,
            )
            tsc_out = format_command_output(tsc.stdout, tsc.stderr, tsc.exit_code, tsc.error)
            tsc_code = tsc.exit_code
        except CommandExitException as e:
            tsc_out = format_command_output(e.stdout, e.stderr, e.exit_code, e.error)
            tsc_code = e.exit_code
        except Exception as e:
            return ToolResult(output=str(e), is_error=True)

        try:
            lint = await asyncio.to_thread(
                self.sandbox.commands.run,
                "npx eslint . --max-warnings 0 2>&1 || true",
                cwd=project,
                timeout=120,
            )
            lint_out = format_command_output(lint.stdout, lint.stderr, lint.exit_code, lint.error)
        except CommandExitException as e:
            lint_out = format_command_output(e.stdout, e.stderr, e.exit_code, e.error)

        return ToolResult(
            output=f"tsc:\n{tsc_out}\n\neslint:\n{lint_out}",
            is_error=tsc_code != 0,
        )

    async def read_file_raw(self, path: str) -> str:
        return await asyncio.to_thread(self.sandbox.files.read, resolve_path(path))
