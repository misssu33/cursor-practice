"""구글 애드센스 블로그 (3,500~5,000자, 마크다운, H2/H3 번호 형식, FAQ, 광고 슬롯)."""
from writers.base import WriterInput, WriterOutput, build_hashtags, _join_hashtags


def write(inp: WriterInput) -> WriterOutput:
    title = f"{inp.main_keyword} 완벽 가이드 — {inp.topic}"

    # 인트로 (150~160자 권장)
    intro = (
        f"{inp.main_keyword}에 대해 알아야 할 핵심을 한 번에 정리했습니다. "
        f"{inp.audience}을 위해 데이터·사례·인사이트를 모았으니, "
        f"이 글 하나로 {inp.topic}의 큰 그림을 잡으실 수 있을 거예요."
    )[:160]

    hook = (inp.hooks or [inp.main_message])[0]

    # H2 1. 개요
    h2_1 = f"""## 1. {inp.main_keyword} 핵심 개요

{hook}

### 1-1. 왜 지금 주목해야 하나
{inp.main_message}

### 1-2. 누구에게 필요한가
- 타깃: {inp.audience}
- 목표: {inp.goal}
"""

    # H2 2. 핵심 데이터
    h2_2 = "## 2. 핵심 데이터로 보는 현황\n\n"
    h2_2 += "### 2-1. 주요 통계\n\n"
    h2_2 += "| 항목 | 내용 |\n|---|---|\n"
    for d in (inp.data_points or [])[:5]:
        # 콜론 기준 항목/내용 분리 시도
        if ":" in d:
            k, v = d.split(":", 1)
            h2_2 += f"| {k.strip()} | {v.strip()} |\n"
        else:
            h2_2 += f"| 데이터 | {d} |\n"

    h2_2 += "\n### 2-2. 데이터가 말하는 것\n\n"
    for d in (inp.data_points or [])[:3]:
        h2_2 += f"- **핵심**: {d}\n"

    # H2 3. 실제 사례
    h2_3 = "## 3. 실제 사례 분석\n\n"
    for i, c in enumerate(inp.cases or [], 1):
        h2_3 += f"### 3-{i}. 사례 {i}\n\n> {c}\n\n"

    # H2 4. 핵심 인사이트
    h2_4 = "## 4. 핵심 인사이트\n\n"
    for i, ins in enumerate(inp.insights or [], 1):
        h2_4 += f"### 4-{i}. 인사이트 {i}\n\n**{ins}**\n\n"

    # H2 5. 실행 체크리스트 + FAQ
    h2_5 = f"""## 5. 실행 체크리스트 & FAQ

### 5-1. 바로 적용할 체크리스트
- [ ] {inp.main_keyword} 현황 점검
- [ ] 핵심 데이터 확보
- [ ] 우선순위 정리
- [ ] 실행 일정 수립
- [ ] 결과 측정 지표 설정

### 5-2. 자주 묻는 질문 (FAQ)

**Q1. {inp.main_keyword}을(를) 처음 시작한다면 무엇부터?**
A. {(inp.insights or ['핵심 개념부터 정리하는 것이 좋습니다.'])[0]}

**Q2. 가장 흔한 실수는?**
A. 데이터 없이 감으로 판단하는 것입니다. 위의 통계를 먼저 확인하세요.

**Q3. {inp.audience}에게 특히 중요한 점은?**
A. {inp.main_message}

### 5-3. 마무리
{inp.differentiation or inp.main_message}

{inp.cta or ''}
"""

    body_md = f"""# {title}

> {intro}

<!-- AD_SLOT_TOP -->

{h2_1}

<!-- AD_SLOT_MID_1 -->

{h2_2}

{h2_3}

<!-- AD_SLOT_MID_2 -->

{h2_4}

{h2_5}
""".strip()

    hashtags = build_hashtags(
        inp.main_keyword, inp.sub_keywords, inp.related_keywords or [], target_count=5
    )
    body_full = body_md + "\n\n" + _join_hashtags(hashtags)

    return WriterOutput(
        channel="adsense",
        body=body_full,
        hashtags=hashtags,
        char_count=len(body_full),
        extra={"title": title, "intro": intro},
    )
