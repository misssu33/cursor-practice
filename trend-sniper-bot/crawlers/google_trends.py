"""Google Trends via pytrends."""
from utils.logger import get_logger

logger = get_logger(__name__)


def get_interest(keyword: str, geo: str = "KR", timeframe: str = "today 3-m") -> dict:
    """관심도 추이 + 연관 주제."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="ko-KR", tz=540, timeout=(5, 15))
        pytrends.build_payload([keyword], geo=geo, timeframe=timeframe)

        # 관심도 추이
        interest_df = pytrends.interest_over_time()
        timeline = []
        if not interest_df.empty:
            timeline = [
                {"date": str(idx.date()), "score": int(row[keyword])}
                for idx, row in interest_df.iterrows()
                if keyword in row
            ][-12:]  # 최근 12개 데이터포인트

        # 연관 주제
        related = pytrends.related_queries()
        top = []
        rising = []
        if keyword in related:
            top_df = related[keyword].get("top")
            rising_df = related[keyword].get("rising")
            if top_df is not None and not top_df.empty:
                top = top_df.head(10).to_dict("records")
            if rising_df is not None and not rising_df.empty:
                rising = rising_df.head(10).to_dict("records")

        return {
            "keyword": keyword,
            "geo": geo,
            "timeframe": timeframe,
            "timeline": timeline,
            "related_top": top,
            "related_rising": rising,
        }
    except Exception as e:
        logger.error(f"google trends 실패: {e}")
        return {"keyword": keyword, "timeline": [], "related_top": [], "related_rising": []}
