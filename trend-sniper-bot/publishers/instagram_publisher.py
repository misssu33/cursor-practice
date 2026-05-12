"""Instagram 반자동 발행 — Cloudinary URL 기반 캐러셀."""
import time
import requests
from publishers.base import PublishResult
from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID, MAX_RETRY
from oauth.instagram_oauth import is_configured as ig_configured
from storage import get_session
from storage.models import InstagramImage
from utils.logger import get_logger

logger = get_logger(__name__)
API = "https://graph.facebook.com/v20.0"


def _create_item(image_url: str) -> str | None:
    try:
        r = requests.post(
            f"{API}/{INSTAGRAM_BUSINESS_ID}/media",
            data={
                "image_url": image_url,
                "is_carousel_item": "true",
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        logger.error(f"ig item 실패 ({image_url}): {e}")
        return None


def _create_carousel(children_ids: list[str], caption: str) -> str | None:
    try:
        r = requests.post(
            f"{API}/{INSTAGRAM_BUSINESS_ID}/media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": caption,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        logger.error(f"ig carousel 실패: {e}")
        return None


def _publish(creation_id: str) -> dict | None:
    try:
        r = requests.post(
            f"{API}/{INSTAGRAM_BUSINESS_ID}/media_publish",
            data={"creation_id": creation_id, "access_token": INSTAGRAM_ACCESS_TOKEN},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"ig publish 실패: {e}")
        return None


def publish(content_id: int, caption: str) -> PublishResult:
    if not ig_configured():
        return PublishResult(ok=False, error="Instagram 미설정")

    with get_session() as session:
        images = (
            session.query(InstagramImage)
            .filter_by(content_id=content_id)
            .order_by(InstagramImage.seq)
            .all()
        )
        urls = [img.cloud_url for img in images if img.cloud_url]

    if len(urls) < 2:
        return PublishResult(
            ok=False,
            error=f"캐러셀은 최소 2장 필요 (현재 cloud_url 있는 이미지 {len(urls)}장). "
                  "Cloudinary 설정과 /ch_instagram → 📷 업로드를 확인하세요."
        )
    if len(urls) > 10:
        urls = urls[:10]

    # 1단계: 자식 컨테이너 생성
    children_ids: list[str] = []
    for i, url in enumerate(urls, 1):
        cid = None
        for attempt in range(MAX_RETRY):
            cid = _create_item(url)
            if cid:
                break
            time.sleep(2 ** attempt)
        if not cid:
            return PublishResult(ok=False, error=f"슬라이드 {i} 컨테이너 실패")
        children_ids.append(cid)
        logger.info(f"IG child {i}/{len(urls)} 생성: {cid}")

    # 2단계: 캐러셀 컨테이너
    time.sleep(3)
    carousel_id = _create_carousel(children_ids, caption)
    if not carousel_id:
        return PublishResult(ok=False, error="캐러셀 컨테이너 실패")

    # 3단계: 발행
    time.sleep(5)
    res = _publish(carousel_id)
    if not res:
        return PublishResult(ok=False, error="최종 발행 실패")

    post_id = res.get("id")
    url = f"https://www.instagram.com/p/{post_id}/" if post_id else None
    logger.info(f"Instagram 발행: id={post_id}")
    return PublishResult(ok=True, url=url, raw=res)
