"""5개 소스 병렬 트렌드 스캔 + 종합 인사이트."""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from utils.logger import get_logger

from crawlers import naver_api, naver_scraper, youtube_api, google_trends, rss_collector

logger = get_logger(__name__)


@dataclass
class ScanResult:
    keyword: str
    fetched_at: str
    autocomplete: list[str] = field(default_factory=list)
    naver_news: list[dict] = field(default_factory=list)
    naver_blog: list[dict] = field(default_factory=list)
    youtube: list[dict] = field(default_factory=list)
    trends: dict = field(default_factory=dict)
    rss: list[dict] = field(default_factory=list)
    insights: dict = field(default_factory=dict)


async def _run_sync(func, *args, **kwargs):
    """동기 함수를 스레드풀에서 실행."""
    return await asyncio.to_thread(func, *args, **kwargs)


async def scan(keyword: str) -> ScanResult:
    """5개 소스 병렬 호출."""
    logger.info(f"트렌드 스캔 시작: keyword={keyword}")

    tasks = {
        "autocomplete": _run_sync(naver_scraper.get_autocomplete, keyword),
        "naver_news":   _run_sync(naver_api.search_news, keyword, 10),
        "naver_blog":   _run_sync(naver_api.search_blog, keyword, 10),
        "youtube":      _run_sync(youtube_api.search_videos, keyword, 10),
        "trends":       _run_sync(google_trends.get_interest, keyword),
        "rss":          _run_sync(rss_collector.collect, keyword),
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    bucket = {}
    for (key, _), res in zip(tasks.items(), results):
        if isinstance(res, Exception):
            logger.error(f"{key} 예외: {res}")
            bucket[key] = [] if key != "trends" else {}
        else:
            bucket[key] = res

    # datetime.utcnow() 는 Python 3.12+에서 deprecated. tz-aware UTC 시각을 동일 ISO 형식으로 직렬화.
    fetched_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    result = ScanResult(
        keyword=keyword,
        fetched_at=fetched_at,
        **bucket,
    )
    result.insights = _analyze(result)
    logger.info(f"트렌드 스캔 완료: keyword={keyword}, 인사이트={result.insights.get('summary')}")
    return result


def _analyze(r: ScanResult) -> dict:
    """수집 결과로부터 검색수요·트렌드수명·포화도 등 도출."""
    # 검색수요: 자동완성 + 블로그 + 뉴스 개수 합산
    demand_score = len(r.autocomplete) * 2 + len(r.naver_blog) + len(r.naver_news)

    # 트렌드 수명 (구글 추이 기반)
    timeline = r.trends.get("timeline", [])
    lifespan = _classify_lifespan(timeline)
    cycle_pos = _classify_cycle(timeline)

    # 포화도 (1~5점, 블로그 + 유튜브 결과 많을수록 포화)
    saturation = min(5, max(1, (len(r.naver_blog) + len(r.youtube)) // 4))

    # 상위 연관 키워드 (블루오션 기회)
    related = []
    for item in r.trends.get("related_rising", [])[:5]:
        related.append(item.get("query", ""))
    for kw in r.autocomplete[:5]:
        if kw not in related:
            related.append(kw)

    # 콘텐츠 갭: 뉴스는 있지만 블로그가 적으면 갭
    gap = bool(len(r.naver_news) >= 5 and len(r.naver_blog) <= 3)

    summary = (
        f"수요 {demand_score}/40 · 수명 {lifespan} · 사이클 {cycle_pos} · "
        f"포화도 {saturation}/5 · 갭 {'있음' if gap else '없음'}"
    )

    return {
        "demand_score": demand_score,
        "lifespan": lifespan,
        "cycle_position": cycle_pos,
        "saturation": saturation,
        "related_keywords": related[:8],
        "content_gap": gap,
        "summary": summary,
    }


def _classify_lifespan(timeline: list[dict]) -> str:
    if not timeline:
        return "unknown"
    scores = [t["score"] for t in timeline]
    avg = sum(scores) / len(scores) if scores else 0
    peak = max(scores) if scores else 0
    if peak >= 80 and avg < 30:
        return "flash"        # 반짝 트렌드
    if peak >= 60 and avg < 50:
        return "short"        # 단기
    if avg >= 50:
        return "mid"          # 중기
    return "long"             # 장기 안정


def _classify_cycle(timeline: list[dict]) -> str:
    if len(timeline) < 3:
        return "unknown"
    recent = timeline[-3:]
    if recent[-1]["score"] > recent[0]["score"] * 1.2:
        return "rising"
    if recent[-1]["score"] < recent[0]["score"] * 0.8:
        return "declining"
    return "stable"


def scan_to_dict(result: ScanResult) -> dict:
    """DB 저장용 직렬화."""
    return {
        "keyword": result.keyword,
        "fetched_at": result.fetched_at,
        "autocomplete": result.autocomplete,
        "naver_news": result.naver_news,
        "naver_blog": result.naver_blog,
        "youtube": result.youtube,
        "trends": result.trends,
        "rss": result.rss,
        "insights": result.insights,
    }


def format_summary(result: ScanResult, max_items: int = 5) -> str:
    """텔레그램 메시지용 요약 텍스트."""
    lines = [f"🔍 *트렌드 스캔 결과* — `{result.keyword}`", ""]
    ins = result.insights
    lines.append(f"📊 {ins.get('summary', '')}")
    if ins.get("related_keywords"):
        lines.append(f"🔗 연관: {', '.join(ins['related_keywords'][:6])}")
    lines.append("")

    if result.autocomplete:
        lines.append(f"💡 자동완성 ({len(result.autocomplete)}):")
        for kw in result.autocomplete[:max_items]:
            lines.append(f"  • {kw}")
        lines.append("")

    if result.naver_news:
        lines.append(f"📰 네이버 뉴스 ({len(result.naver_news)}):")
        for n in result.naver_news[:max_items]:
            lines.append(f"  • {n['title'][:60]}")
        lines.append("")

    if result.youtube:
        lines.append(f"▶️ YouTube ({len(result.youtube)}):")
        for v in result.youtube[:max_items]:
            views = f"{v['view_count']:,}" if v.get("view_count") else "?"
            lines.append(f"  • [{views}회] {v['title'][:50]}")
        lines.append("")

    if result.rss:
        lines.append(f"📡 RSS ({len(result.rss)}):")
        for r in result.rss[:max_items]:
            lines.append(f"  • [{r['source']}] {r['title'][:55]}")

    return "\n".join(lines)
