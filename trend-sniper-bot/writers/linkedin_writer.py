"""LinkedIn 장문 (1,500~2,500자, 전문가 톤, 질문 CTA)."""
from writers.base import WriterInput, WriterOutput, build_hashtags, _join_hashtags


def write(inp: WriterInput) -> WriterOutput:
    hooks = inp.hooks or [inp.main_message]
    hook_line = hooks[0] if hooks else inp.main_message

    data_block = "\n".join(f"• {d}" for d in (inp.data_points or [])[:5])
    cases_block = "\n".join(f"→ {c}" for c in (inp.cases or [])[:3])
    insights_block = "\n".join(f"💡 {i}" for i in (inp.insights or [])[:3])

    body = f"""{hook_line}

저는 최근 {inp.topic}에 대해 깊이 들여다볼 기회가 있었습니다.
{inp.audience}을(를) 위해 정리한 내용을 공유드립니다.

— 핵심 데이터
{data_block}

— 현장 사례
{cases_block}

— 제가 발견한 인사이트
{insights_block}

{inp.main_message}

{inp.differentiation or ''}

여러분은 {inp.main_keyword}에 대해 어떻게 생각하시나요?
경험이나 의견을 댓글로 들려주시면 함께 이야기 나누고 싶습니다.

{inp.cta or ''}
""".strip()

    # 분량 보강 (1500자 미만이면 인사이트 확장)
    if len(body) < 1500 and len(inp.insights or []) > 3:
        extra = "\n".join(f"💡 {i}" for i in inp.insights[3:6])
        body = body.replace(insights_block, insights_block + "\n" + extra)

    hashtags = build_hashtags(
        inp.main_keyword, inp.sub_keywords, inp.related_keywords or [], target_count=7
    )
    body_full = body + "\n\n" + _join_hashtags(hashtags)

    return WriterOutput(
        channel="linkedin",
        body=body_full,
        hashtags=hashtags,
        char_count=len(body_full),
        extra={},
    )
