import json
import logging

import requests

from . import config

log = logging.getLogger(__name__)

PROMPT = """다음은 영문 국방/군수/획득 관련 기사 또는 보고서의 본문 일부다. 한국어로 요약해라.

반드시 다음 JSON 스키마로만 응답해라. 다른 텍스트 금지. 모든 값은 한국어로 작성.

{{
  "한줄요약": "기사 핵심을 한 문장으로",
  "핵심포인트": ["사실 또는 결정사항 1", "사실 또는 결정사항 2", "사실 또는 결정사항 3"],
  "주요키워드": ["고유명사 또는 핵심 용어 3-6개"]
}}

본문:
---
{text}
---
"""


def summarize(text: str) -> dict:
    prompt = PROMPT.format(text=text)
    r = requests.post(
        f"{config.OLLAMA_HOST}/api/generate",
        json={
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        },
        timeout=config.OLLAMA_TIMEOUT,
    )
    r.raise_for_status()
    raw = (r.json().get("response") or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Ollama returned non-JSON, preserving raw output")
        return {
            "한줄요약": raw[:500],
            "_invalid_json": True,
        }
