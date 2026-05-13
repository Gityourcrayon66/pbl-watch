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

# 활성화할 소스. False로 두면 해당 소스 skip.
# GAO는 검색 매칭이 약해 noise 많음 → 기본 비활성 (필요시 본인이 True로)
SOURCES = {
    "arxiv": True,
    "openalex": True,
    "gao": False,
    "ddg": True,
    "seed": True,
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

MAX_PER_RUN = 5
MAX_TEXT_CHARS = 12000

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HTTP_TIMEOUT = 30
HTTP_DELAY = 2.0  # 정중하게 — 폭주 금지
