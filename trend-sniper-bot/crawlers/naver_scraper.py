"""네이버 자동완성 스크래퍼 (공식 API 없음)."""
import requests
from utils.logger import get_logger

logger = get_logger(__name__)
_TIMEOUT = 6


def get_autocomplete(keyword: str) -> list[str]:
    """네이버 자동완성. 비공식 endpoint — 변경 가능성 있음."""
    try:
        url = "https://ac.search.naver.com/nx/ac"
        params = {
            "q": keyword, "con": "1", "frm": "nv", "ans": "2",
            "r_format": "json", "r_enc": "UTF-8", "r_unicode": "0",
            "t_koreng": "1", "run": "2", "rev": "4", "q_enc": "UTF-8", "st": "100",
        }
        r = requests.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [[]])[0] if data.get("items") else []
        return [it[0] for it in items if it][:10]
    except Exception as e:
        logger.error(f"naver autocomplete 실패: {e}")
        return []
