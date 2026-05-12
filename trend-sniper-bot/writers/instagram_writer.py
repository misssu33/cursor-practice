"""Instagram 캐러셀 (8~10 슬라이드 + 캡션 200~600자)."""
from writers.base import WriterInput, WriterOutput, build_hashtags, _join_hashtags


def write(inp: WriterInput) -> WriterOutput:
    hook = (inp.hooks or [inp.main_message])[0]

    # 슬라이드 8장 기본 구성
    slides: list[dict] = [
        {
            "seq": 1,
            "type": "cover",
            "headline": _short(hook, 18),
            "sub": _short(inp.main_message, 30),
            "visual": "임팩트 있는 큰 타이포 + 강조색 배경",
        },
        {
            "seq": 2,
            "type": "problem",
            "headline": "이런 적 있지 않나요?",
            "sub": _short(inp.audience + "의 흔한 고민", 40),
            "visual": "공감 일러스트 or 상황 사진",
        },
    ]

    # 데이터 슬라이드 (최대 3장)
    for i, d in enumerate((inp.data_points or [])[:3], start=3):
        slides.append({
            "seq": i,
            "type": "data",
            "headline": f"포인트 {i - 2}",
            "sub": _short(d, 60),
            "visual": "큰 숫자 강조 + 아이콘",
        })

    # 인사이트 슬라이드 (최대 2장)
    base = len(slides)
    for i, ins in enumerate((inp.insights or [])[:2], start=1):
        slides.append({
            "seq": base + i,
            "type": "insight",
            "headline": f"인사이트 {i}",
            "sub": _short(ins, 60),
            "visual": "심플 배경 + 한 줄 카피",
        })

    # 요약 슬라이드
    slides.append({
        "seq": len(slides) + 1,
        "type": "summary",
        "headline": "오늘의 핵심",
        "sub": _short(inp.main_message, 50),
        "visual": "체크리스트 형식",
    })

    # CTA 슬라이드
    slides.append({
        "seq": len(slides) + 1,
        "type": "cta",
        "headline": "도움됐다면 💾저장!",
        "sub": "친구에게도 공유해 주세요",
        "visual": "저장/공유 아이콘 강조",
    })

    # 캡션 (200~600자)
    caption_lines = [
        hook,
        "",
        inp.main_message,
        "",
        f"📌 {inp.audience}을 위해 정리했습니다.",
    ]
    for ins in (inp.insights or [])[:2]:
        caption_lines.append(f"✔ {ins}")
    caption_lines += [
        "",
        "더 자세한 내용은 캐러셀에서 ➡",
        "💾 저장 · 공유 · 팔로우 부탁드려요!",
    ]
    if inp.cta:
        caption_lines.append(inp.cta)

    caption = "\n".join(caption_lines)
    if len(caption) > 600:
        caption = caption[:597] + "..."

    hashtags = build_hashtags(
        inp.main_keyword, inp.sub_keywords, inp.related_keywords or [], target_count=18
    )

    # 본문 = 슬라이드 스크립트 + 캡션 통합 (검증용)
    script_text = "\n\n".join(
        f"[Slide {s['seq']} — {s['type']}]\n📝 {s['headline']}\n💬 {s['sub']}\n🎨 {s['visual']}"
        for s in slides
    )
    body_full = f"{script_text}\n\n=== CAPTION ===\n{caption}\n\n{_join_hashtags(hashtags)}"

    return WriterOutput(
        channel="instagram",
        body=body_full,
        hashtags=hashtags,
        char_count=len(body_full),
        extra={
            "slides": slides,
            "caption": caption,
            "slide_count": len(slides),
        },
    )


def _short(s: str, n: int) -> str:
    s = (s or "").strip().replace("\n", " ")
    return s if len(s) <= n else s[:n - 1] + "…"
