from pathlib import Path

from app.collectors.zhihu.executor import ExecuteParams, ZhihuCrawlerExecutor
from app.core.settings import crawl_settings
from app.services.collection_service import CollectionService


def test_normalize_possible_mojibake_repairs_utf8_decoded_as_gbk() -> None:
    assert CollectionService._normalize_possible_mojibake("鏉庣櫧") == "李白"
    assert CollectionService._normalize_possible_mojibake("李白") == "李白"


def test_build_process_spec_uses_isolated_browser_dir_and_project_python() -> None:
    executor = ZhihuCrawlerExecutor()
    temp_user_data_dir = executor._create_temp_user_data_dir("ct_test", "zhihu")
    raw_dir = Path("data/raw/zhihu/ct_test/20260412_000000")
    raw_output_file = raw_dir / "raw.json"

    try:
        import asyncio

        temp_user_data_dir = asyncio.run(temp_user_data_dir)
        process_spec = executor._build_process_spec(
            ExecuteParams(
                task_id="ct_test",
                platform="zhihu",
                collect_type="search",
                query_keyword="李白",
                source_id=None,
                source_url=None,
                limit=20,
            ),
            raw_dir=raw_dir,
            raw_output_file=raw_output_file,
            temp_user_data_dir=temp_user_data_dir,
        )

        assert process_spec.cwd == crawl_settings.mediacrawler_project_dir
        assert process_spec.env is not None
        assert process_spec.env["MEDIACRAWLER_USER_DATA_DIR"] == str(temp_user_data_dir)
        assert process_spec.command[0].endswith("python.exe")
    finally:
        executor._safe_cleanup_temp(temp_user_data_dir, log_writer=_NoopLogWriter())


class _NoopLogWriter:
    def write(self, _: str) -> None:
        return None

    def flush(self) -> None:
        return None
