import logging
import time
from urllib.parse import quote_plus

import feedparser
from bs4 import BeautifulSoup
from curl_cffi import requests as cc_requests

from . import config

log = logging.getLogger(__name__)


def _http_get(url: str):
    time.sleep(config.HTTP_DELAY)
    r = cc_requests.get(
        url,
        impersonate="chrome120",
        timeout=config.HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r


def _pbl_in_text(text: str) -> bool:
    """클라이언트 필터: PBL이 진짜로 'performance based logistics'인지 확인."""
    raw = text or ""
    t = raw.lower()
    return (
        "performance based logistics" in t
        or "performance-based logistics" in t
        or "performance based sustainment" in t
        or "performance-based sustainment" in t
        or "성과기반군수지원" in raw
        or "성과 기반 군수지원" in raw
    )


def _decode_inverted_index(idx: dict) -> str:
    """OpenAlex abstract_inverted_index → 일반 텍스트."""
    if not idx:
        return ""
    positions = []
    for word, locs in idx.items():
        for loc in locs:
            positions.append((loc, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def arxiv_search():
    q = quote_plus(config.ARXIV_QUERY)
    url = (
        f"http://export.arxiv.org/api/query?search_query=all:{q}"
        f"&max_results={config.ARXIV_MAX}&sortBy=submittedDate&sortOrder=descending"
    )
    try:
        r = _http_get(url)
    except Exception as e:
        log.warning("arxiv fetch failed: %s", e)
        return []
    feed = feedparser.parse(r.text)
    out = []
    for e in feed.entries:
        pdf = next(
            (l.href for l in e.links if l.get("type") == "application/pdf"), None
        )
        if not pdf:
            continue
        out.append({
            "source": "arxiv",
            "url": pdf,
            "title": e.title,
            "published": getattr(e, "published", None),
        })
    return out


def openalex_search():
    """OpenAlex: title + abstract에 정확한 phrase가 있는 것만."""
    out = []
    for kw in config.KEYWORDS:
        url = (
            f"https://api.openalex.org/works?search={quote_plus(kw)}"
            f"&per-page={config.OPENALEX_MAX}"
            "&filter=open_access.is_oa:true"
            "&select=id,title,publication_date,best_oa_location,primary_location,abstract_inverted_index"
        )
        if config.OPENALEX_CONTACT:
            url += f"&mailto={config.OPENALEX_CONTACT}"
        try:
            r = _http_get(url)
        except Exception as e:
            log.warning("OpenAlex fetch failed (%s): %s", kw, e)
            continue
        for w in r.json().get("results", []):
            title = w.get("title") or ""
            abstract = _decode_inverted_index(w.get("abstract_inverted_index"))
            if not _pbl_in_text(title + " " + abstract):
                continue
            loc = w.get("best_oa_location") or {}
            pdf = loc.get("pdf_url") or (w.get("primary_location") or {}).get("pdf_url")
            if not pdf:
                continue
            out.append({
                "source": "openalex",
                "url": pdf,
                "title": title,
                "published": w.get("publication_date"),
            })
    return out


def gao_search():
    """GAO 검색 — curl_cffi로 Cloudflare 우회."""
    out = []
    for kw in config.KEYWORDS:
        list_url = config.GAO_SEARCH_URL.format(kw=quote_plus(kw))
        try:
            r = _http_get(list_url)
        except Exception as e:
            log.warning("GAO list fetch failed (%s): %s", kw, e)
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        report_pages = set()
        for a in soup.select("a[href*='/products/']"):
            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https://www.gao.gov" + href
            report_pages.add(href.split("?")[0])

        for page_url in list(report_pages)[:8]:
            try:
                rr = _http_get(page_url)
            except Exception as e:
                log.warning("GAO page fetch failed: %s", e)
                continue
            ps = BeautifulSoup(rr.text, "html.parser")
            title_el = ps.find("h1") or ps.find("title")
            title = title_el.get_text(strip=True) if title_el else page_url
            # 본문 추출하여 PBL phrase 정확 매칭만 통과
            body_text = ps.get_text(" ", strip=True)
            if not _pbl_in_text(title + " " + body_text):
                continue
            pdf_link = None
            for a in ps.select("a[href$='.pdf']"):
                href = a.get("href", "")
                if href.startswith("/"):
                    href = "https://www.gao.gov" + href
                if "/assets/" in href:
                    pdf_link = href
                    break
            if pdf_link:
                out.append({
                    "source": "gao",
                    "url": pdf_link,
                    "title": title,
                    "published": None,
                })
    return out


def seed_urls():
    return [
        {"source": "seed", "url": u, "title": u.rsplit("/", 1)[-1], "published": None}
        for u in config.SEED_URLS
    ]


def all_sources():
    out = []
    for fn in (arxiv_search, openalex_search, gao_search, seed_urls):
        try:
            results = fn()
            log.info("%s: %d items", fn.__name__, len(results))
            out.extend(results)
        except Exception as e:
            log.error("scraper %s failed: %s", fn.__name__, e)
    return out
