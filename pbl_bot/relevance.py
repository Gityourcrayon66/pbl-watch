"""Deterministic PBL relevance classifier (no LLM).

classify(text, title) -> "high" | "medium" | "low" | "unknown"
  - "unknown": empty input
  - "high":    explicit PBL phrase appears
  - "medium":  sustainment / product support / 군수지원 family
  - "low":     anything else
"""

HIGH_TERMS_EN = (
    "performance based logistics",
    "performance-based logistics",
    "performance based sustainment",
    "performance-based sustainment",
)
HIGH_TERMS_KO = (
    "성과기반군수지원",
    "성과 기반 군수지원",
)

MEDIUM_TERMS_EN = (
    "sustainment",
    "product support",
    "logistics support",
    "availability contract",
    "availability-based contract",
    "spare parts contract",
    "depot maintenance",
)
MEDIUM_TERMS_KO = (
    "군수지원",
    "정비계약",
)


def classify(text: str, title: str = "") -> str:
    raw = ((title or "") + "\n" + (text or "")).strip()
    if not raw:
        return "unknown"
    lower = raw.lower()
    if any(t in lower for t in HIGH_TERMS_EN):
        return "high"
    if any(t in raw for t in HIGH_TERMS_KO):
        return "high"
    if any(t in lower for t in MEDIUM_TERMS_EN):
        return "medium"
    if any(t in raw for t in MEDIUM_TERMS_KO):
        return "medium"
    return "low"
