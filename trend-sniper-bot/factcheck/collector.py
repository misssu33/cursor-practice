"""팩트체크 자료 수집 — 네이버 뉴스 + 구글 검색 결과."""
from factcheck.source_tiers import classify, tier_icon
from crawlers import naver_api
from utils.logger import get_logger

logger = get_logger(__name__)


def collect_sources(claim: str, limit: int = 10) -> list[dict]:
    """주장 → 검증 후보 출처 리스트.

    Returns:
        [{title, url, snippet, tier, tier_label, icon}]
    """
    sources: list[dict] = []

    # 1. 네이버 뉴스 검색
    news_items = naver_api.search_news(claim, display=limit)
    for n in news_items:
        tier, label = classify(n["link"])
        sources.append({
            "title": n["title"],
            "url": n["link"],
            "snippet": n["description"][:200],
            "tier": tier,
            "tier_label": label,
            "icon": tier_icon(tier),
            "source": "naver_news",
        })

    # 2. 네이버 블로그 (Tier 3 참고용)
    blog_items = naver_api.search_blog(claim, display=5)
    for b in blog_items:
        tier, label = classify(b["link"])
        sources.append({
            "title": b["title"],
            "url": b["link"],
            "snippet": b["description"][:200],
            "tier": tier,
            "tier_label": label,
            "icon": tier_icon(tier),
            "source": "naver_blog",
        })

    # Tier 오름차순 정렬 (1차 우선 노출, 0은 맨 뒤)
    sources.sort(key=lambda s: (s["tier"] if s["tier"] > 0 else 99, s["source"]))
    return sources[:limit]


def format_sources(claim: str, sources: list[dict]) -> str:
    """텔레그램 메시지용 출처 목록."""
    lines = [f"🔬 *팩트체크 자료* — `{claim[:80]}`", ""]
    if not sources:
        lines.append("⚠️ 관련 출처를 찾을 수 없습니다.")
        return "\n".join(lines)

    # Tier별 통계
    tier_counts = {1: 0, 2: 0, 3: 0, 0: 0}
    for s in sources:
        tier_counts[s["tier"]] = tier_counts.get(s["tier"], 0) + 1
    lines.append(
        f"📊 1차 {tier_counts.get(1,0)} · "
        f"2차 {tier_counts.get(2,0)} · "
        f"3차 {tier_counts.get(3,0)} · "
        f"미분류 {tier_counts.get(0,0)}"
    )
    lines.append("")

    for i, s in enumerate(sources, 1):
        lines.append(f"{i}. {s['icon']} *{s['tier_label']}*")
        lines.append(f"   {s['title'][:70]}")
        if s.get("snippet"):
            lines.append(f"   _{s['snippet'][:120]}_")
        lines.append(f"   🔗 {s['url']}")
        lines.append("")

    lines.append("👉 위 자료를 참고하여 판정해 주세요.")
    return "\n".join(lines)
