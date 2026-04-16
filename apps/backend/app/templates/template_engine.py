from __future__ import annotations

from typing import Any


def build_template_structure(structure_json: dict[str, Any]) -> dict[str, Any]:
    opening = structure_json.get("opening", "提出一个反直觉问题")
    body = structure_json.get("body", ["给出背景", "呈现冲突", "说明启发"])
    ending = structure_json.get("ending", "引导评论互动")
    return {"opening": opening, "body": body, "ending": ending}

