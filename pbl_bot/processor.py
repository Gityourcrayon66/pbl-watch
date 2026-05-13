import io
import logging

from curl_cffi import requests as cc_requests
from pypdf import PdfReader

from . import config

log = logging.getLogger(__name__)


def fetch_pdf_text(url: str) -> str:
    r = cc_requests.get(url, impersonate="chrome120", timeout=config.HTTP_TIMEOUT)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "").lower()
    if "pdf" not in ctype and r.content[:4] != b"%PDF":
        raise ValueError(f"not a pdf (content-type={ctype})")

    reader = PdfReader(io.BytesIO(r.content))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as e:
            log.warning("page extract failed: %s", e)
    return "\n".join(pages)[: config.MAX_TEXT_CHARS]
