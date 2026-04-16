from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.prompt_manager import prompt_manager
from app.core.settings import ai_settings
from app.models.schemas import AnalysisLLMOutput
from app.services.ai_client import AIClientError, ai_client, schema_from_model


def _fallback_analysis(title: str, content_text: str) -> dict:
    text = f"{title}\n{content_text}".strip()
    segments = [item.strip() for item in content_text.splitlines() if item.strip()]
    main_topic = title.split(" ")[0] if " " in title else title[:12]

    if "反常识" in text:
        hook_text = "反常识切入"
    elif "如果" in text:
        hook_text = "假设提问切入"
    else:
        hook_text = "观点直陈切入"

    fact_risk_items: list[str] = []
    if "据说" in text or "传闻" in text:
        fact_risk_items.append("存在未经证实的传闻性表述")
    if "数据" in text and "来源" not in text:
        fact_risk_items.append("出现数据表述但未给出来源")

    return {
        "summary": (content_text[:120] + "...") if len(content_text) > 120 else content_text,
        "main_topic": main_topic,
        "hook_text": hook_text,
        "narrative_structure": {
            "opening": segments[0] if segments else content_text[:30],
            "body": segments[1:3] if len(segments) > 1 else [content_text[:60]],
            "ending": segments[-1] if segments else "总结观点",
        },
        "emotional_driver": "好奇 + 争议",
        "fact_risk_level": "medium" if fact_risk_items else "low",
        "fact_risk_items": fact_risk_items,
    }


def analyze_content_features(
    title: str,
    content_text: str,
    *,
    db: Session | None = None,
    prompt_version: str = "analysis.zhihu.history.v1",
    model_name: str | None = None,
) -> dict:
    model = model_name or ai_settings.default_model_name
    if not ai_settings.configured:
        return _fallback_analysis(title, content_text)

    prompt = prompt_manager.load(
        prompt_id=prompt_version,
        variables={"title": title, "content": content_text},
    )
    try:
        response = ai_client.chat_completion_sync(
            prompt=prompt,
            schema=schema_from_model(AnalysisLLMOutput, name="analysis_result"),
            model=model,
            task_type="analysis",
            prompt_version=prompt_version,
            db=db,
        )
        parsed = AnalysisLLMOutput.model_validate(response["result"])
        return parsed.model_dump(mode="json")
    except (AIClientError, ValueError):
        if not ai_settings.allow_mock_fallback:
            raise
        return _fallback_analysis(title, content_text)
