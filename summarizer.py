import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 추천 모델: llama-3.3-70b-versatile (품질 우수) 또는 llama-3.1-8b-instant (속도 빠름)
MODEL = "llama-3.3-70b-versatile"


def summarize(title: str, content: str) -> str:
    prompt = f"""다음 뉴스를 한국어로 Threads 게시글에 적합하게 요약해줘.
조건:
- 450자 이내 (Threads 글자 제한 500자 고려)
- 핵심 정보 위주, 흥미를 끄는 첫 문장
- 마지막 줄에 관련 해시태그 2~3개
- 과장·낚시성 표현 금지

제목: {title}
본문: {content}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "너는 한국어 뉴스 요약 전문가야. 간결하고 자연스럽게 요약해."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()
