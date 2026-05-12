"""네이버 블로그 (2,500~3,500자, 마크다운 금지, 친근 톤)."""
from writers.base import WriterInput, WriterOutput, build_hashtags, _join_hashtags


def write(inp: WriterInput) -> WriterOutput:
    hook = (inp.hooks or [inp.main_message])[0]

    intro = f"""안녕하세요! 오늘은 {inp.topic}에 대해 이야기해보려고 해요.

{hook}

이 글은 {inp.audience}을(를) 위해 정리했습니다.
끝까지 읽으시면 {inp.main_keyword}에 대한 큰 그림이 잡힐 거예요 😊

[이미지1]
""".strip()

    # 데이터 섹션
    data_section = "【핵심 데이터로 본 현황】\n\n"
    for i, d in enumerate(inp.data_points or [], 1):
        data_section += f"{i}. {d}\n"
    data_section += "\n자료가 보여주는 흐름은 분명합니다. 숫자로 확인하니 더 와닿네요.\n"

    # 사례 섹션
    cases_section = "\n【실제 사례 살펴보기】\n\n"
    for i, c in enumerate(inp.cases or [], 1):
        cases_section += f"▶ 사례 {i}. {c}\n\n"

    cases_section += "[이미지2]\n"

    # 인사이트 섹션
    insights_section = "\n【제가 정리한 인사이트】\n\n"
    for i, ins in enumerate(inp.insights or [], 1):
        insights_section += f"💡 {ins}\n"

    # 마무리
    outro = f"""

【마무리하며】

{inp.main_message}

{inp.differentiation or ''}

{inp.main_keyword}에 관심 있으신 분들께 조금이라도 도움이 되었으면 좋겠어요.
공감 ♥, 댓글, 이웃추가 모두 큰 힘이 됩니다 :)

{inp.cta or ''}
""".strip()

    body = intro + "\n\n" + data_section + cases_section + insights_section + outro

    # 분량 보강
    while len(body) < 2500 and inp.data_points and len(inp.data_points) > 3:
        body += f"\n\n참고로 {inp.data_points[-1]}라는 점도 함께 짚어두면 좋겠습니다."
        break

    hashtags = build_hashtags(
        inp.main_keyword, inp.sub_keywords, inp.related_keywords or [], target_count=8
    )
    body_full = body + "\n\n" + _join_hashtags(hashtags)

    return WriterOutput(
        channel="naver",
        body=body_full,
        hashtags=hashtags,
        char_count=len(body_full),
        extra={"image_placeholders": ["이미지1", "이미지2"]},
    )
