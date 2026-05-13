from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
DB_PATH = DATA_DIR / "pbl.db"

KEYWORDS = [
    "Performance Based Logistics",
    "Performance-Based Logistics",
    "PBL sustainment",
    "성과기반군수지원",
]

# 5개 RSS 피드 — pivot 후 주 수집 채널
RSS_FEEDS = [
    {"source": "dod_news",         "url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10"},
    {"source": "dod_contracts",    "url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=400&Site=945&max=10"},
    {"source": "defense_news",     "url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml"},
    {"source": "air_space_forces", "url": "https://www.airandspaceforces.com/feed/"},
    {"source": "defense_one",      "url": "https://www.defenseone.com/rss/all/"},
]
RSS_PER_FEED_MAX = 20
MIN_BODY_CHARS = 300  # 본문 이 미만이면 분류기 우회하고 'low' 강제

# 활성화할 소스. RSS pivot 이후 키워드 검색은 모두 비활성.
SOURCES = {
    "arxiv":    False,
    "openalex": False,
    "gao":      False,
    "ddg":      False,
    "seed":     True,
    "rss":      True,
}

# 차단할 URL — discovery 시 skip, 이미 DB에 있어도 화면에서 숨김
# (Streamlit 카드의 "차단 추가" 링크가 GitHub 편집 페이지로 안내)
BLOCKED_URLS: list[str] = [
]

ARXIV_QUERY = '"performance based logistics" OR "performance-based logistics"'
ARXIV_MAX = 10

# OpenAlex: 학술 메타데이터, 무료, 봇 친화. mailto 넣으면 polite pool (우선순위).
# 빈 문자열이면 안 보냄. 본인 이메일 노출 싫으면 비워두기.
OPENALEX_CONTACT = ""
OPENALEX_MAX = 25

GAO_SEARCH_URL = "https://www.gao.gov/reports-testimonies?keyword={kw}&processed=1"

# DuckDuckGo 일반 웹 검색 (구글 대체, API key 불필요)
DDG_MAX = 10

# 본인이 직접 정독할 가치가 있다고 판단한 URL — 직접 추가
# PDF 또는 HTML 모두 지원. 예:
#   "https://www.gao.gov/assets/d24...pdf"         (PDF)
#   "https://www.law.go.kr/법령/방위사업법"          (HTML — 법령 본문)
#   "https://www.law.go.kr/행정규칙/..."             (HTML — 훈령)
SEED_URLS: list[str] = [
    "https://www.gao.gov/assets/d24106786.pdf",
]

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "gemma2:2b"
OLLAMA_TIMEOUT = 180

MAX_PER_RUN = 15
MAX_TEXT_CHARS = 12000

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HTTP_TIMEOUT = 30
HTTP_DELAY = 2.0  # 정중하게 — 폭주 금지
