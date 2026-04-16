from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.prompt_manager import prompt_manager
from app.core.settings import ai_settings
from app.models.schemas import GeneratedScriptLLMOutput
from app.services.ai_client import AIClientError, ai_client, schema_from_model


def _fallback_script(topic: str, brief: str | None, template_structure: dict[str, Any]) -> dict:
    body_parts = template_structure.get("body", [])
    body_text = "\n".join(f"{idx + 1}. {part}" for idx, part in enumerate(body_parts))
    intro = template_structure.get("opening", "我们先从一个问题开始。")
    outro = template_structure.get("ending", "你怎么看？欢迎在评论区聊聊。")

    title = f"{topic}：一个值得重看的历史叙事角度"
    script_text = (
        f"{intro}\n"
        f"主题：{topic}\n"
        f"背景：{brief or '围绕历史事件的关键因果链展开'}\n"
        f"{body_text}\n"
        f"{outro}"
    )
    return {
        "title_candidates": [title],
        "script_text": script_text,
        "storyboard": [
            {
                "shot_no": 1,
                "duration_seconds": 8,
                "visual_description": "问题钩子与反常识开场",
                "voiceover": intro,
            },
            {
                "shot_no": 2,
                "duration_seconds": 20,
                "visual_description": "史料背景与争议核心",
                "voiceover": body_text or "展开背景和冲突。",
            },
            {
                "shot_no": 3,
                "duration_seconds": 10,
                "visual_description": "结论升华与互动引导",
                "voiceover": outro,
            },
        ],
        "cover_text": f"{topic} | 3分钟看懂争议核心",
        "publish_caption": f"今天聊聊 {topic}，你站哪一边？",
        "hashtags": ["历史", "短视频脚本", "内容研究"],
    }


def _build_reference_analysis_hints(reference_posts: list[dict[str, Any]] | None) -> str:
    if not reference_posts:
        return ""

    lines: list[str] = []
    for post in reference_posts:
        analysis = post.get("analysis")
        if not isinstance(analysis, dict):
            continue
        title = str(post.get("title") or "未命名样本").strip() or "未命名样本"
        main_topic = str(analysis.get("main_topic") or "").strip() or "未知"
        hook_text = str(analysis.get("hook_text") or "").strip() or "无"
        emotional_driver = str(analysis.get("emotional_driver") or "").strip() or "未知"
        narrative_structure = analysis.get("narrative_structure") or {}
        summary = str(analysis.get("summary") or "").strip() or "无"
        lines.append(
            (
                f"- 样本《{title}》\n"
                f"  - 主题: {main_topic}\n"
                f"  - 钩子: {hook_text}\n"
                f"  - 情绪驱动: {emotional_driver}\n"
                f"  - 叙事结构: {json.dumps(narrative_structure, ensure_ascii=False)}\n"
                f"  - 摘要: {summary}"
            )
        )

    if not lines:
        return ""
    return "\n".join(lines)


def generate_script(
    topic: str,
    brief: str | None,
    template_structure: dict[str, Any],
    *,
    reference_posts: list[dict[str, Any]] | None = None,
    db: Session | None = None,
    prompt_version: str = "generation.zhihu_to_video.v1",
    model_name: str | None = None,
) -> dict:
    model = model_name or ai_settings.default_model_name
    if not ai_settings.configured:
        return _fallback_script(topic, brief, template_structure)

    analysis_hints = _build_reference_analysis_hints(reference_posts)
    prompt = prompt_manager.load(
        prompt_id=prompt_version,
        variables={
            "topic": topic,
            "brief": brief or "",
            "template": json.dumps(template_structure, ensure_ascii=False, indent=2),
            "reference_posts": json.dumps(reference_posts or [], ensure_ascii=False, indent=2),
            "reference_analysis_hints": analysis_hints,
        },
    )
    try:
        response = ai_client.chat_completion_sync(
            prompt=prompt,
            schema=schema_from_model(GeneratedScriptLLMOutput, name="generated_script"),
            model=model,
            task_type="generation",
            prompt_version=prompt_version,
            db=db,
        )
        parsed = GeneratedScriptLLMOutput.model_validate(response["result"])
        return parsed.model_dump(mode="json")
    except (AIClientError, ValueError):
        if not ai_settings.allow_mock_fallback:
            raise
        return _fallback_script(topic, brief, template_structure)
