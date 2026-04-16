from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--type", default="search")
    parser.add_argument("--keyword", default="zhihu")
    parser.add_argument("--id", default="")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()

    records = []
    for idx in range(1, args.limit + 1):
        records.append(
            {
                "title": f"{args.keyword} sample {idx}",
                "content": f"content for {args.keyword} sample {idx}",
                "url": f"https://www.zhihu.com/question/mock-{idx}",
                "author_info": {"name": "mock_author"},
                "create_time": now,
                "metrics": {
                    "like_count": idx * 10,
                    "comment_count": idx,
                    "favorite_count": idx * 2,
                    "share_count": idx,
                    "view_count": idx * 100,
                },
                "topic_keywords": [args.keyword, "history"],
                "source_id": args.id or f"mock-{idx}",
                "collect_type": args.type,
            }
        )

    payload = {"items": records, "meta": {"mock": True, "count": len(records)}}
    output_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"mock crawler wrote {len(records)} records to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

