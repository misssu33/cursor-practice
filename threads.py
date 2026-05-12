import os
import time
import requests

BASE = "https://graph.threads.net/v1.0"


def post_to_threads(text: str) -> str:
    user_id = os.getenv("THREADS_USER_ID")
    token = os.getenv("THREADS_ACCESS_TOKEN")

    # 1) 미디어 컨테이너 생성
    r = requests.post(
        f"{BASE}/{user_id}/threads",
        data={"media_type": "TEXT", "text": text, "access_token": token},
    )
    r.raise_for_status()
    creation_id = r.json()["id"]

    # 2) 컨테이너 처리 대기
    time.sleep(3)

    # 3) 발행
    r2 = requests.post(
        f"{BASE}/{user_id}/threads_publish",
        data={"creation_id": creation_id, "access_token": token},
    )
    r2.raise_for_status()
    return r2.json()["id"]
