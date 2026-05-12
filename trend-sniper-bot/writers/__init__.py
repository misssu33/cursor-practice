from writers.base import WriterInput, WriterOutput
from writers import (
    linkedin_writer, naver_writer, adsense_writer,
    instagram_writer, threads_writer,
)


WRITERS = {
    "linkedin": linkedin_writer.write,
    "naver": naver_writer.write,
    "adsense": adsense_writer.write,
    "instagram": instagram_writer.write,
    "threads": threads_writer.write,
}


def write_channel(channel_key: str, inp: WriterInput) -> WriterOutput:
    if channel_key not in WRITERS:
        raise KeyError(f"알 수 없는 채널: {channel_key}")
    return WRITERS[channel_key](inp)


__all__ = [
    "WriterInput", "WriterOutput", "WRITERS", "write_channel",
    "linkedin_writer", "naver_writer", "adsense_writer",
    "instagram_writer", "threads_writer",
]
