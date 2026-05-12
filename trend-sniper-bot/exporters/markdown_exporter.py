"""채널별 파일 내보내기 (ZIP 미사용)."""
from datetime import datetime
from pathlib import Path
from storage import get_session
from storage.models import Project, ChannelContent
from channels.base import get_channel

EXPORT_DIR = Path("./data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_name(s: str, n: int = 40) -> str:
    s = "".join(c if c.isalnum() or c in "-_" else "_" for c in s)
    return s[:n] or "untitled"


def export_project(project_id: int) -> list[tuple[str, Path]]:
    """프로젝트 → 채널별 파일 생성. [(channel, path), ...] 반환."""
    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            return []
        topic = project.topic
        contents = (
            session.query(ChannelContent)
            .filter_by(project_id=project_id)
            .all()
        )
        rows = [(c.channel, c.body, c.hashtags) for c in contents]

    if not rows:
        return []

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = EXPORT_DIR / f"p{project_id}_{_safe_name(topic)}_{ts}"
    base.mkdir(parents=True, exist_ok=True)

    files: list[tuple[str, Path]] = []
    for channel, body, hashtags in rows:
        spec = get_channel(channel)
        ext = "md" if spec.use_markdown else "txt"
        path = base / f"{channel}.{ext}"
        path.write_text(body, encoding="utf-8")
        files.append((channel, path))

    # 메타 정보
    meta = base / "_README.txt"
    meta.write_text(
        f"프로젝트 #{project_id}\n"
        f"주제: {topic}\n"
        f"생성: {ts}\n\n"
        f"채널: {', '.join(c for c, _ in files)}\n",
        encoding="utf-8",
    )
    files.append(("readme", meta))
    return files
