import io
import logging
import time

from bs4 import BeautifulSoup
from curl_cffi import requests as cc_requests
from pypdf import PdfReader

from . import config

log = logging.getLogger(__name__)


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as e:
            log.warning("page extract failed: %s", e)
    return "\n".join(pages)


def _extract_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def fetch_text(url: str) -> str:
    """URL에서 PDF 또는 HTML을 받아 본문 텍스트 반환."""
    time.sleep(config.HTTP_DELAY)  # 정중함 — 같은 도메인 연속 호출 시 부담 방지
    r = cc_requests.get(url, impersonate="chrome120", timeout=config.HTTP_TIMEOUT)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "").lower()

    if "pdf" in ctype or r.content[:4] == b"%PDF":
        text = _extract_pdf(r.content)
    elif "html" in ctype or "xml" in ctype or r.text.lstrip().lower().startswith("<!doctype"):
        text = _extract_html(r.text)
    else:
        raise ValueError(f"unsupported content-type: {ctype}")

    return text[: config.MAX_TEXT_CHARS]


# 하위 호환 (혹시 외부 import 있을 경우)
fetch_pdf_text = fetch_text
