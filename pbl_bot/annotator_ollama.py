import json
import logging

import requests

from . import config

log = logging.getLogger(__name__)

PROMPT = """다음은 영문 군수/획득 정책 문서의 본문 일부다. PBL(Performance Based Logistics, 성과기반군수지원) 관점에서 한국어로 요약해라.

반드시 다음 JSON 스키마로만 응답해라. 다른 텍스트 금지.

{{
  "한줄요약": "한 문장",
  "핵심포인트": ["...", "...", "..."],
  "PBL관련성": "high",
  "관련성근거": "1-2문장",
  "주요키워드": ["...", "...", "..."]
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
            "PBL관련성": "unknown",
            "_invalid_json": True,
        }
