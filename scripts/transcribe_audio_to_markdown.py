#!/usr/bin/env python3
"""Transcribe a local audio file and generate transcript + Markdown skeleton.

This script is intentionally narrow:
- It performs deterministic local transcription via faster-whisper.
- It writes a UTF-8 raw transcript with timestamps.
- It writes a Markdown skeleton that preserves the raw transcript unchanged.

The cleaned summary, translation, and action items are left as placeholders so
Codex can refine them in a follow-up step using the skill instructions.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_MODEL = "small"


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def add_vendor_paths(vendor_dirs: Iterable[Path]) -> None:
    for path in vendor_dirs:
        if path and path.exists():
            sys.path.insert(0, str(path))


def resolve_snapshot(model_root: Path) -> Path:
    snapshots = model_root / "snapshots"
    if not snapshots.exists():
        return model_root
    candidates = sorted((p for p in snapshots.iterdir() if p.is_dir()), key=lambda p: p.name)
    if not candidates:
        return model_root
    return candidates[-1]


def find_local_model(explicit: Optional[str], model_name: str) -> str:
    if explicit:
        return str(resolve_snapshot(Path(explicit)))

    hf_home = os.environ.get("HF_HOME")
    candidate_roots = [
        Path(hf_home) if hf_home else None,
        Path.home() / ".cache" / "huggingface" / "hub",
    ]
    expected = f"models--Systran--faster-whisper-{model_name}"
    for root in candidate_roots:
        if not root:
            continue
        candidate = root / expected
        if candidate.exists():
            return str(resolve_snapshot(candidate))
    return model_name


def slugify_stem(path: Path) -> str:
    name = path.stem.strip()
    safe = re.sub(r"[^0-9A-Za-z._-]+", "_", name)
    return safe.strip("._-") or "audio"


def format_time(seconds: float) -> str:
    minutes, secs = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


@dataclass
class SegmentLine:
    start: float
    end: float
    text: str


def collect_segments(audio_path: str, model_path: str, language: Optional[str]) -> tuple[list[SegmentLine], str, float]:
    from faster_whisper import WhisperModel  # imported late on purpose

    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        audio_path,
        language=language,
        task="transcribe",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=True,
        word_timestamps=False,
    )
    items: list[SegmentLine] = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            items.append(SegmentLine(seg.start, seg.end, text))
    return items, info.language, info.duration


def build_transcript(lines: list[SegmentLine], language: str) -> str:
    output = [f"[detected_language={language}]"]
    output.append("")
    for line in lines:
        output.append(f"[{line.start:06.2f}-{line.end:06.2f}] {line.text}")
    return "\n".join(output) + "\n"


def build_markdown(
    title: str,
    source_path: Path,
    transcript_name: str,
    language: str,
    duration_seconds: float,
    transcript_text: str,
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"# {title}\n\n"
        f"## 说明\n\n"
        f"- 本文件由 `scripts/transcribe_audio_to_markdown.py` 自动生成。\n"
        f"- 原文章节保留脚本转写结果，不做修改。\n"
        f"- `整理后的内容`、`关键信息` 和 `代办事项` 为待补充区域，可继续由 Codex 根据 skill 完成。\n\n"
        f"## 音频信息\n\n"
        f"- 源文件：`{source_path}`\n"
        f"- 检测语言：`{language}`\n"
        f"- 时长：`{format_time(duration_seconds)}`\n"
        f"- 生成时间：`{generated_at}`\n"
        f"- 原始转写文件：`{transcript_name}`\n\n"
        f"## 关键信息\n\n"
        f"- 待补充\n\n"
        f"## 整理后的内容\n\n"
        f"待补充。\n\n"
        f"## 原文（不做修改）\n\n"
        f"```text\n{transcript_text}```\n\n"
        f"## 代办事项\n\n"
        f"- [ ] 待补充\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe a local audio file and create transcript + Markdown skeleton."
    )
    parser.add_argument("audio", help="Path to the local audio file")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for generated files. Defaults to current directory.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional Markdown title. Defaults to the audio filename stem.",
    )
    parser.add_argument(
        "--language",
        default="zh",
        help="Language hint for Whisper. Use 'auto' to allow detection. Default: zh",
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL,
        help="Model name fallback when no local model path is found. Default: small",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        help="Explicit path to a local faster-whisper model directory or snapshot.",
    )
    parser.add_argument(
        "--vendor-dir",
        action="append",
        default=[],
        help="Optional extra import directory for faster-whisper and dependencies. Repeatable.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        eprint(f"Audio file not found: {audio_path}")
        return 1

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    add_vendor_paths(Path(p).expanduser().resolve() for p in args.vendor_dir)

    try:
        model_path = find_local_model(args.model_path, args.model_name)
        language = None if args.language == "auto" else args.language
        segments, detected_language, duration_seconds = collect_segments(
            str(audio_path), model_path, language
        )
    except ModuleNotFoundError as exc:
        eprint("Missing dependency:", exc)
        eprint("Install faster-whisper into a local vendor dir or pass --vendor-dir.")
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI handling
        eprint("Transcription failed:", exc)
        return 3

    transcript_text = build_transcript(segments, detected_language)
    stem = slugify_stem(audio_path)
    transcript_path = output_dir / f"transcript_{stem}.txt"
    markdown_path = output_dir / f"{stem}.md"
    title = args.title or audio_path.stem

    transcript_path.write_text(transcript_text, encoding="utf-8")
    markdown_path.write_text(
        build_markdown(
            title=title,
            source_path=audio_path,
            transcript_name=transcript_path.name,
            language=detected_language,
            duration_seconds=duration_seconds,
            transcript_text=transcript_text,
        ),
        encoding="utf-8",
    )

    print(f"Transcript: {transcript_path}")
    print(f"Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
