"""채널별 SEO 점수 검증 (0~100)."""
import re
from dataclasses import dataclass
from channels.base import get_channel, ChannelSpec


@dataclass
class SEOReport:
    channel: str
    score: int                  # 0~100
    char_count: int
    hashtag_count: int
    keyword_density: float      # %
    issues: list[str]
    passed: bool


def _count_keyword(body: str, keyword: str) -> int:
    if not keyword:
        return 0
    return len(re.findall(re.escape(keyword), body, re.IGNORECASE))


def _extract_hashtags(body: str) -> list[str]:
    return re.findall(r"#\w+", body)


def score(channel_key: str, body: str, main_keyword: str = "") -> SEOReport:
    spec: ChannelSpec = get_channel(channel_key)
    issues: list[str] = []
    s = 100

    # 1. 분량
    char_count = len(body)
    if char_count < spec.min_len:
        issues.append(f"분량 부족: {char_count} < {spec.min_len}")
        s -= 25
    elif char_count > spec.max_len * 1.2:
        issues.append(f"분량 초과: {char_count} > {spec.max_len}")
        s -= 10

    # 2. 해시태그
    hashtags = _extract_hashtags(body)
    if len(hashtags) < spec.hashtag_min:
        issues.append(f"해시태그 부족: {len(hashtags)} < {spec.hashtag_min}")
        s -= 15
    elif len(hashtags) > spec.hashtag_max:
        issues.append(f"해시태그 초과: {len(hashtags)} > {spec.hashtag_max}")
        s -= 5

    # 3. 메인 키워드 밀도 (1~3% 권장)
    density = 0.0
    if main_keyword and char_count > 0:
        count = _count_keyword(body, main_keyword)
        density = (count * len(main_keyword)) / char_count * 100
        if count == 0:
            issues.append(f"메인 키워드 '{main_keyword}' 미등장")
            s -= 20
        elif density < 0.5:
            issues.append(f"키워드 밀도 낮음: {density:.2f}%")
            s -= 10
        elif density > 3.5:
            issues.append(f"키워드 밀도 과다 (스팸 위험): {density:.2f}%")
            s -= 15

    # 4. 채널별 추가 규칙
    if channel_key == "adsense":
        if not re.search(r"^##\s+\d+\.", body, re.MULTILINE):
            issues.append("애드센스: H2 번호 형식(## 1.) 없음")
            s -= 10
        if not re.search(r"^###\s+\d+-\d+\.", body, re.MULTILINE):
            issues.append("애드센스: H3 번호 형식(### 1-1.) 없음")
            s -= 10
        if "FAQ" not in body and "자주 묻는" not in body:
            issues.append("애드센스: FAQ 섹션 없음")
            s -= 5

    elif channel_key == "naver":
        if re.search(r"^#{1,6}\s", body, re.MULTILINE):
            issues.append("네이버: 마크다운 헤더 사용 금지")
            s -= 15

    elif channel_key == "threads":
        # 5포스트로 분할 가정: \n\n---\n\n 구분자
        posts = re.split(r"\n-{3,}\n", body)
        for i, p in enumerate(posts, 1):
            if len(p) > 500:
                issues.append(f"Threads 포스트 {i}: 500자 초과 ({len(p)})")
                s -= 8
        if len(posts) < 3:
            issues.append(f"Threads: 포스트 수 부족 ({len(posts)} < 3)")
            s -= 10

    elif channel_key == "instagram":
        # 캡션 + 슬라이드 구분 가정
        if len(body) < 200:
            issues.append("Instagram 캡션 너무 짧음")
            s -= 10

    elif channel_key == "linkedin":
        if not re.search(r"[?？]", body):
            issues.append("LinkedIn: 마무리 질문(CTA) 없음")
            s -= 5

    s = max(0, min(100, s))
    return SEOReport(
        channel=channel_key,
        score=s,
        char_count=char_count,
        hashtag_count=len(hashtags),
        keyword_density=round(density, 2),
        issues=issues,
        passed=(s >= 70),
    )


def format_report(report: SEOReport) -> str:
    icon = "✅" if report.passed else "⚠️"
    lines = [
        f"{icon} *SEO 검증 — {report.channel}*",
        f"점수: *{report.score}/100* ({'합격' if report.passed else '재작성 권장'})",
        f"분량: {report.char_count}자 · 해시태그: {report.hashtag_count}개 · 키워드 밀도: {report.keyword_density}%",
    ]
    if report.issues:
        lines.append("")
        lines.append("📋 개선 항목:")
        for issue in report.issues:
            lines.append(f"  • {issue}")
    return "\n".join(lines)
