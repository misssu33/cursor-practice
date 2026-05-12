"""출처 신뢰도 자동 분류 (B-2 우회안).

LLM 미사용. 도메인 화이트리스트 기반으로 1~3차 신뢰도 자동 부여.
진위 판정은 사용자가 수행 (A안).
"""
from urllib.parse import urlparse


# Tier 1: 정부·학술·공식 기관
TIER1_DOMAINS = {
    # 정부
    "go.kr", "gov", "gov.kr",
    # 학술
    "ac.kr", "edu", "nature.com", "science.org", "ieee.org", "acm.org",
    "scholar.google.com", "pubmed.ncbi.nlm.nih.gov", "arxiv.org",
    # 공식 통계
    "kostat.go.kr", "data.go.kr", "kdi.re.kr",
    # 국제기관
    "who.int", "un.org", "oecd.org", "worldbank.org", "imf.org",
}

# Tier 2: 주요 언론·팩트체크 기관
TIER2_DOMAINS = {
    # 한국 주요 언론
    "yna.co.kr", "yonhapnews.co.kr", "kbs.co.kr", "mbc.co.kr", "sbs.co.kr",
    "chosun.com", "donga.com", "joongang.co.kr", "hankyung.com", "mk.co.kr",
    "hani.co.kr", "khan.co.kr", "ohmynews.com",
    # 해외 주요 언론
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "nytimes.com",
    "washingtonpost.com", "theguardian.com", "wsj.com", "ft.com",
    "bloomberg.com", "cnn.com", "economist.com",
    # 팩트체크
    "snu-factcheck.org", "factcheck.org", "politifact.com", "fullfact.org",
    # IT/전문 매체
    "zdnet.co.kr", "bloter.net", "techcrunch.com", "wired.com",
}

# Tier 3: 위키·블로그·커뮤니티·SNS
TIER3_DOMAINS = {
    "wikipedia.org", "namu.wiki", "wiki.com",
    "blog.naver.com", "tistory.com", "brunch.co.kr", "velog.io", "medium.com",
    "youtube.com", "youtu.be", "twitter.com", "x.com", "facebook.com",
    "instagram.com", "threads.net", "reddit.com",
    "dcinside.com", "fmkorea.com", "clien.net", "ppomppu.co.kr",
}


def classify(url: str) -> tuple[int, str]:
    """URL → (tier, tier_label). tier: 1~3, 0=unknown."""
    if not url:
        return 0, "unknown"
    try:
        host = urlparse(url).hostname or ""
        host = host.lower().lstrip("www.")
    except Exception:
        return 0, "unknown"

    # 완전 일치 또는 서브도메인 매칭
    for domain in TIER1_DOMAINS:
        if host == domain or host.endswith("." + domain) or host.endswith(domain):
            return 1, "1차 (정부·학술)"
    for domain in TIER2_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return 2, "2차 (주요 언론·팩트체크)"
    for domain in TIER3_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return 3, "3차 (위키·블로그·SNS)"

    return 0, "미분류"


def tier_icon(tier: int) -> str:
    return {1: "🟢", 2: "🟡", 3: "🟠", 0: "⚪"}.get(tier, "⚪")
