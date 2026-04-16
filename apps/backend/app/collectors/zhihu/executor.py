from __future__ import annotations

import asyncio
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Literal

from app.core.settings import crawl_settings

ExecutionStatus = Literal[
    "SUCCESS",
    "FAILED",
    "RATE_LIMITED",
    "LOGIN_EXPIRED",
    "PROXY_FAILED",
    "VERIFICATION_REQUIRED",
]


@dataclass
class ExecuteParams:
    task_id: str
    platform: str
    collect_type: Literal["search", "detail", "creator"]
    query_keyword: str
    source_id: str | None
    source_url: str | None
    limit: int
    proxy: str | None = None


@dataclass
class ExecuteResult:
    status: ExecutionStatus
    raw_output_file: str | None
    log_file: str
    error_message: str | None = None
    pid: int | None = None
    return_code: int | None = None
    duration_seconds: float = 0.0


@dataclass
class ProcessSpec:
    command: list[str]
    cwd: str | None = None
    env: dict[str, str] | None = None


class ZhihuCrawlerExecutor:
    def __init__(self) -> None:
        self._semaphore = asyncio.Semaphore(crawl_settings.max_concurrent_tasks)
        self._profile_sync_locks: dict[str, asyncio.Lock] = {}

    async def execute_task(self, params: ExecuteParams) -> ExecuteResult:
        async with self._semaphore:
            return await self._execute_locked(params)

    async def _execute_locked(self, params: ExecuteParams) -> ExecuteResult:
        started_at = datetime.now(UTC)
        timestamp = started_at.strftime("%Y%m%d_%H%M%S")

        raw_dir = Path(crawl_settings.raw_output_root) / params.platform / params.task_id / timestamp
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_output_file = raw_dir / "raw.json"

        logs_dir = Path(crawl_settings.logs_dir)
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"task_{params.task_id}.log"

        temp_user_data_dir = await self._create_temp_user_data_dir(params.task_id, params.platform)
        process_spec = self._build_process_spec(params, raw_dir, raw_output_file, temp_user_data_dir)

        with log_file.open("a", encoding="utf-8") as log_writer:
            self._write_event(
                log_writer,
                event="task_started",
                task_id=params.task_id,
                collect_type=params.collect_type,
                command=process_spec.command,
                cwd=process_spec.cwd,
                raw_output_file=str(raw_output_file),
            )

            return_code, pid, duration_seconds, timeout_hit, combined_log = await self._run_async_process(
                process_spec,
                log_writer,
            )

            if timeout_hit:
                await self._sync_persistent_browser_state(params.platform, temp_user_data_dir, log_writer)
                self._safe_cleanup_temp(temp_user_data_dir, log_writer)
                self._write_event(
                    log_writer,
                    event="task_finished",
                    task_id=params.task_id,
                    pid=pid,
                    return_code=return_code,
                    duration_seconds=duration_seconds,
                    status="FAILED",
                    reason="timeout",
                )
                return ExecuteResult(
                    status="FAILED",
                    raw_output_file=str(raw_output_file),
                    log_file=str(log_file),
                    error_message="crawler task timeout",
                    pid=pid,
                    return_code=return_code,
                    duration_seconds=duration_seconds,
                )

            await self._sync_persistent_browser_state(params.platform, temp_user_data_dir, log_writer)
            self._safe_cleanup_temp(temp_user_data_dir, log_writer)

            if not raw_output_file.exists():
                self._materialize_raw_output(raw_dir, raw_output_file)

            normalized_code = -1 if return_code is None else return_code
            status = self._classify_status(normalized_code, combined_log.lower())
            if status == "SUCCESS" and not raw_output_file.exists():
                return ExecuteResult(
                    status="FAILED",
                    raw_output_file=str(raw_output_file),
                    log_file=str(log_file),
                    error_message="crawler completed but raw output is missing",
                    pid=pid,
                    return_code=return_code,
                    duration_seconds=duration_seconds,
                )

            error_message = None if status == "SUCCESS" else "crawler failed"
            self._write_event(
                log_writer,
                event="task_finished",
                task_id=params.task_id,
                pid=pid,
                return_code=return_code,
                duration_seconds=duration_seconds,
                status=status,
            )
            return ExecuteResult(
                status=status,
                raw_output_file=str(raw_output_file),
                log_file=str(log_file),
                error_message=error_message,
                pid=pid,
                return_code=return_code,
                duration_seconds=duration_seconds,
            )

    def _build_process_spec(
        self,
        params: ExecuteParams,
        raw_dir: Path,
        raw_output_file: Path,
        temp_user_data_dir: Path,
    ) -> ProcessSpec:
        if self._can_use_realmode_mediacrawler():
            return ProcessSpec(
                command=self._build_realmode_command(params, raw_dir),
                cwd=crawl_settings.mediacrawler_project_dir,
                env=self._build_realmode_env(temp_user_data_dir),
            )
        return ProcessSpec(
            command=self._build_fallback_command(params, raw_output_file, temp_user_data_dir),
            cwd=None,
        )

    def _build_realmode_command(self, params: ExecuteParams, raw_dir: Path) -> list[str]:
        python_executable = self._resolve_mediacrawler_python()
        keyword = self._normalize_keyword(params.query_keyword)
        save_data_path = str(raw_dir.resolve())
        command = [
            python_executable,
            "main.py",
            "--platform",
            params.platform,
            "--lt",
            "qrcode",
            "--type",
            params.collect_type,
            "--headless",
            "false",
            "--save_data_option",
            "json",
            "--save_data_path",
            save_data_path,
            "--max_concurrency_num",
            "1",
            "--get_comment",
            "false",
            "--get_sub_comment",
            "false",
            "--start",
            "1",
        ]

        if params.collect_type == "search":
            command.extend(["--keywords", keyword or "历史人物"])
        elif params.collect_type == "detail":
            detail_value = params.source_url or params.source_id or ""
            command.extend(["--specified_id", detail_value])
        elif params.collect_type == "creator":
            creator_value = params.source_url or params.source_id or ""
            command.extend(["--creator_id", creator_value])

        return command

    @staticmethod
    def _normalize_keyword(value: str | None) -> str:
        if not value:
            return ""

        candidates = [value]
        for source_encoding in ("latin-1", "gbk"):
            try:
                repaired = value.encode(source_encoding).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            candidates.append(repaired)

        def score(text: str) -> tuple[int, int]:
            cjk_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
            question_penalty = -text.count("?")
            return (cjk_count, question_penalty)

        best = value
        best_score = score(value)
        for candidate in candidates[1:]:
            candidate_score = score(candidate)
            if candidate_score > best_score:
                best = candidate
                best_score = candidate_score
        return best

    @staticmethod
    def _resolve_mediacrawler_python() -> str:
        project_dir = Path(crawl_settings.mediacrawler_project_dir)
        windows_venv_python = project_dir / ".venv" / "Scripts" / "python.exe"
        if windows_venv_python.exists():
            return str(windows_venv_python)
        return sys.executable

    @staticmethod
    def _build_realmode_env(temp_user_data_dir: Path) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["MEDIACRAWLER_USER_DATA_DIR"] = str(temp_user_data_dir)
        return env

    def _build_fallback_command(
        self,
        params: ExecuteParams,
        raw_output_file: Path,
        temp_user_data_dir: Path,
    ) -> list[str]:
        min_delay = random.randint(3, 5)
        max_delay = random.randint(6, 8)
        base_cmd = [
            crawl_settings.mediacrawler_executable,
            "--platform",
            params.platform,
            "--type",
            params.collect_type,
            "--output",
            str(raw_output_file),
            "--limit",
            str(params.limit),
            "--user-data-dir",
            str(temp_user_data_dir),
            "--min-delay",
            str(min_delay),
            "--max-delay",
            str(max_delay),
        ]

        if params.query_keyword:
            base_cmd.extend(["--keyword", params.query_keyword])
        if params.source_id:
            base_cmd.extend(["--id", params.source_id])
        if params.proxy:
            base_cmd.extend(["--proxy", params.proxy])

        if crawl_settings.fallback_to_mock and shutil.which(crawl_settings.mediacrawler_executable) is None:
            return [
                sys.executable,
                "scripts/mock_mediacrawler_runner.py",
                "--output",
                str(raw_output_file),
                "--type",
                params.collect_type,
                "--keyword",
                params.query_keyword or "zhihu",
                "--id",
                params.source_id or "",
                "--limit",
                str(params.limit),
            ]

        return base_cmd

    async def _run_async_process(
        self,
        process_spec: ProcessSpec,
        log_writer,
    ) -> tuple[int, int | None, float, bool, str]:
        start = monotonic()
        try:
            process = await asyncio.create_subprocess_exec(
                *process_spec.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=process_spec.cwd,
                env=process_spec.env,
            )
        except PermissionError:
            # Some sandboxed Windows environments deny PIPE creation.
            return await asyncio.to_thread(self._run_blocking_subprocess, process_spec, log_writer, start)

        pid = process.pid
        combined_lines: list[str] = []

        stream_tasks = [
            asyncio.create_task(self._stream_to_log(process.stdout, "stdout", log_writer, combined_lines)),
            asyncio.create_task(self._stream_to_log(process.stderr, "stderr", log_writer, combined_lines)),
        ]

        timed_out = False
        try:
            await asyncio.wait_for(process.wait(), timeout=crawl_settings.task_timeout_seconds)
        except TimeoutError:
            timed_out = True
            process.kill()
            await process.wait()
        finally:
            await asyncio.gather(*stream_tasks, return_exceptions=True)

        duration_seconds = monotonic() - start
        normalized_code = -1 if process.returncode is None else process.returncode
        return normalized_code, pid, duration_seconds, timed_out, "\n".join(combined_lines)

    @staticmethod
    def _run_blocking_subprocess(
        process_spec: ProcessSpec,
        log_writer,
        start: float,
    ) -> tuple[int, int | None, float, bool, str]:
        combined_lines: list[str] = []
        timed_out = False
        pid: int | None = None
        return_code = -1
        try:
            proc = subprocess.Popen(
                process_spec.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                cwd=process_spec.cwd,
                env=process_spec.env,
            )
            pid = proc.pid
            try:
                stdout_text, stderr_text = proc.communicate(timeout=crawl_settings.task_timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                stdout_text, stderr_text = proc.communicate()

            if stdout_text:
                for line in stdout_text.splitlines():
                    combined_lines.append(line)
                    log_writer.write(f"[{datetime.now(UTC).isoformat()}] [stdout] {line}\n")
            if stderr_text:
                for line in stderr_text.splitlines():
                    combined_lines.append(line)
                    log_writer.write(f"[{datetime.now(UTC).isoformat()}] [stderr] {line}\n")
            log_writer.flush()
            return_code = -1 if proc.returncode is None else proc.returncode
        except Exception as exc:
            combined_lines.append(str(exc))
            log_writer.write(f"[{datetime.now(UTC).isoformat()}] [stderr] {exc}\n")
            log_writer.flush()

        duration_seconds = monotonic() - start
        return return_code, pid, duration_seconds, timed_out, "\n".join(combined_lines)

    @staticmethod
    async def _stream_to_log(stream, stream_name: str, log_writer, sink: list[str]) -> None:
        if stream is None:
            return
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip("\n")
            sink.append(text)
            log_writer.write(f"[{datetime.now(UTC).isoformat()}] [{stream_name}] {text}\n")
            log_writer.flush()

    @staticmethod
    def _classify_status(return_code: int, combined_log: str) -> ExecutionStatus:
        if "captcha" in combined_log or "verification" in combined_log or "滑块" in combined_log:
            return "VERIFICATION_REQUIRED"
        if "rate limit" in combined_log or "too many requests" in combined_log:
            return "RATE_LIMITED"
        if (
            "login expired" in combined_log
            or "cookie expired" in combined_log
            or "登录失效" in combined_log
            or "zerr_not_login" in combined_log
            or "authenticationerror" in combined_log
        ):
            return "LOGIN_EXPIRED"
        if "proxy" in combined_log and ("failed" in combined_log or "error" in combined_log):
            return "PROXY_FAILED"
        if return_code == 0:
            return "SUCCESS"
        return "FAILED"

    @staticmethod
    def _write_event(log_writer, event: str, **fields: object) -> None:
        payload = {
            "time": datetime.now(UTC).isoformat(),
            "event": event,
            **fields,
        }
        log_writer.write(json.dumps(payload, ensure_ascii=False) + "\n")
        log_writer.flush()

    async def _create_temp_user_data_dir(self, task_id: str, platform: str) -> Path:
        configured_prefix = Path(crawl_settings.temp_user_data_dir_prefix)
        temp_parent = configured_prefix.parent if str(configured_prefix.parent) != "." else Path(tempfile.gettempdir())
        temp_parent.mkdir(parents=True, exist_ok=True)
        prefix = configured_prefix.name or "mediacrawler_"
        temp_dir = Path(tempfile.mkdtemp(prefix=f"{prefix}{task_id}_", dir=str(temp_parent)))
        await self._seed_persistent_browser_state(platform, temp_dir)
        return temp_dir

    async def _seed_persistent_browser_state(self, platform: str, target_dir: Path) -> None:
        persistent_dir = self._persistent_browser_state_dir(platform)
        if not persistent_dir.exists():
            return

        lock = self._get_profile_sync_lock(platform)
        async with lock:
            await asyncio.to_thread(self._copy_tree_contents, persistent_dir, target_dir)

    async def _sync_persistent_browser_state(self, platform: str, source_dir: Path, log_writer) -> None:
        if not source_dir.exists():
            return

        persistent_dir = self._persistent_browser_state_dir(platform)
        persistent_dir.parent.mkdir(parents=True, exist_ok=True)
        lock = self._get_profile_sync_lock(platform)
        async with lock:
            await asyncio.to_thread(self._replace_tree, source_dir, persistent_dir)
        self._write_event(
            log_writer,
            event="persistent_browser_state_synced",
            platform=platform,
            path=str(persistent_dir),
        )

    def _get_profile_sync_lock(self, platform: str) -> asyncio.Lock:
        if platform not in self._profile_sync_locks:
            self._profile_sync_locks[platform] = asyncio.Lock()
        return self._profile_sync_locks[platform]

    @staticmethod
    def _persistent_browser_state_dir(platform: str) -> Path:
        return Path(crawl_settings.persistent_browser_state_root) / platform

    @staticmethod
    def _copy_tree_contents(source: Path, target: Path) -> None:
        if not source.exists():
            return
        shutil.copytree(
            source,
            target,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                "Crashpad",
                "GrShaderCache",
                "GraphiteDawnCache",
                "ShaderCache",
                "Safe Browsing",
                "segmentation_platform",
                "*.tmp",
                "*.temp",
                "*-journal",
                "Singleton*",
                "lockfile",
            ),
        )

    @staticmethod
    def _replace_tree(source: Path, target: Path) -> None:
        if target.exists():
            shutil.rmtree(target, ignore_errors=False)
        ZhihuCrawlerExecutor._copy_tree_contents(source, target)

    @staticmethod
    def _safe_cleanup_temp(target: Path, log_writer) -> None:
        try:
            shutil.rmtree(target, ignore_errors=False)
            ZhihuCrawlerExecutor._write_event(log_writer, event="temp_dir_cleaned", path=str(target))
        except Exception as exc:
            ZhihuCrawlerExecutor._write_event(
                log_writer,
                event="temp_dir_cleanup_failed",
                path=str(target),
                error=str(exc),
            )

    @staticmethod
    def _can_use_realmode_mediacrawler() -> bool:
        if not crawl_settings.mediacrawler_enable_real:
            return False
        root = Path(crawl_settings.mediacrawler_project_dir)
        return root.exists() and (root / "main.py").exists()

    @staticmethod
    def _materialize_raw_output(raw_dir: Path, target_file: Path) -> None:
        content_json_files = sorted(raw_dir.glob("**/*_contents_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if content_json_files:
            source = content_json_files[0]
            payload = json.loads(source.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                target_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                return
            if isinstance(payload, dict):
                target_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                return

        content_jsonl_files = sorted(raw_dir.glob("**/*_contents_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if content_jsonl_files:
            source = content_jsonl_files[0]
            items: list[dict] = []
            for line in source.read_text(encoding="utf-8").splitlines():
                text = line.strip()
                if not text:
                    continue
                try:
                    value = json.loads(text)
                    if isinstance(value, dict):
                        items.append(value)
                except json.JSONDecodeError:
                    continue
            if items:
                target_file.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


executor = ZhihuCrawlerExecutor()
