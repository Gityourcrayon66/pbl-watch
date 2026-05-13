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


def ddg_search():
    """DuckDuckGo 일반 웹 검색 — phrase 강제 + 본문 매칭 필터."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        log.warning("duckduckgo_search not installed")
        return []

    out = []
    for kw in config.KEYWORDS:
        query = f'"{kw}"'  # phrase 검색 강제 (특히 한국어 단어 분리 방지)
        try:
            time.sleep(config.HTTP_DELAY)
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=config.DDG_MAX))
        except Exception as e:
            log.warning("DDG search failed (%s): %s", kw, e)
            continue
        for r in results:
            title = r.get("title") or ""
            href = r.get("href") or ""
            body = r.get("body") or ""
            if not href:
                continue
            if not _pbl_in_text(title + " " + body):
                continue
            out.append({
                "source": "ddg",
                "url": href,
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
    registry = {
        "arxiv": arxiv_search,
        "openalex": openalex_search,
        "gao": gao_search,
        "ddg": ddg_search,
        "seed": seed_urls,
    }
    blocked = set(config.BLOCKED_URLS)
    out = []
    for name, fn in registry.items():
        if not config.SOURCES.get(name, True):
            log.info("%s: skipped (disabled in config.SOURCES)", name)
            continue
        try:
            results = fn()
            before = len(results)
            results = [r for r in results if r["url"] not in blocked]
            if before != len(results):
                log.info("%s: %d items (%d blocked)", name, len(results), before - len(results))
            else:
                log.info("%s: %d items", name, len(results))
            out.extend(results)
        except Exception as e:
            log.error("scraper %s failed: %s", name, e)
    return out
