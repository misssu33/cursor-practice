"""Threads 5연속 포스트 (각 ≤500자, 마크다운 금지)."""
from writers.base import WriterInput, WriterOutput, build_hashtags, _join_hashtags


def write(inp: WriterInput) -> WriterOutput:
    hook = (inp.hooks or [inp.main_message])[0]

    # 포스트 1: 후킹 + 예고
    post1 = f"""{hook}

{inp.audience}이라면 한 번쯤 생각해봤을 주제예요.

오늘 다섯 개 포스트로 정리합니다.
👇""".strip()

    # 포스트 2: 데이터
    data_lines = "\n".join(f"• {d}" for d in (inp.data_points or [])[:3])
    post2 = f"""1️⃣ 먼저 숫자부터.

{data_lines}

생각보다 큰 흐름이죠.""".strip()

    # 포스트 3: 사례
    cases_lines = "\n".join(f"→ {c}" for c in (inp.cases or [])[:2])
    post3 = f"""2️⃣ 실제로 어떻게 나타나고 있나.

{cases_lines}

데이터가 현실에서 보이는 모습입니다.""".strip()

    # 포스트 4: 인사이트
    insight_top = (inp.insights or [inp.main_message])[0]
    post4 = f"""3️⃣ 제가 발견한 핵심.

"{insight_top}"

{inp.main_message}""".strip()

    # 포스트 5: 요약 + 질문 CTA
    hashtags = build_hashtags(
        inp.main_keyword, inp.sub_keywords, inp.related_keywords or [], target_count=2
    )
    post5 = f"""4️⃣ 정리하면

— {inp.main_keyword}은(는) 지금 주목할 가치가 있다
— 데이터·사례가 같은 방향
— 행동할 시점

여러분은 어떻게 보시나요?
댓글로 의견 들려주세요 👇

{_join_hashtags(hashtags)}""".strip()

    posts = [post1, post2, post3, post4, post5]
    # 각 포스트 500자 보장
    posts = [p[:497] + "..." if len(p) > 500 else p for p in posts]

    body_full = "\n\n---\n\n".join(posts)

    return WriterOutput(
        channel="threads",
        body=body_full,
        hashtags=hashtags,
        char_count=len(body_full),
        extra={"posts": posts, "post_count": len(posts)},
    )
