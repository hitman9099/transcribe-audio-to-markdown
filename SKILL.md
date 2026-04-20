---
name: transcribe-audio-to-markdown
description: Transcribe local audio files such as .m4a, .mp3, .wav, or short video/audio clips into Markdown with an exact raw transcript, a cleaned or translated version, key facts, and action items. Use when Codex needs to process voice notes, call recordings, interview audio, or meeting clips, especially when the user wants the original transcript preserved exactly, asks for a Markdown deliverable, or needs deadlines and todos extracted from the recording.
---

# Transcribe Audio To Markdown

## Overview

Turn a local audio file into a Markdown note that keeps the raw transcript, adds a cleaned or translated version, and extracts actionable follow-ups. Prefer offline/local transcription first and treat the model's direct transcript output as the source of truth.

## Quick Start

When a deterministic first pass is useful, run the bundled script first:

```powershell
python scripts/transcribe_audio_to_markdown.py C:\path\to\clip.m4a --output-dir C:\path\to\out
```

If `faster-whisper` is installed into a workspace-local vendor directory, pass it explicitly:

```powershell
python scripts/transcribe_audio_to_markdown.py C:\path\to\clip.m4a --output-dir C:\path\to\out --vendor-dir C:\path\to\.codex_vendor
```

Then use the generated transcript and Markdown skeleton as the base artifact for the final cleaned note.

## Workflow

### 1. Confirm the input and output paths

- Resolve the local audio path first.
- Default the outputs to the current workspace unless the user asks for a different location.
- Derive filenames from the source stem when practical.
- Prefer one transcript text file plus one final Markdown file.

Example:

- Input: `C:\path\to\clip.m4a`
- Transcript: `transcript_clip.txt`
- Markdown: `clip.md`

### 2. Prepare a transcription path

- Check that the source file exists.
- Check for local tools such as `ffmpeg`, `ffprobe`, and `python`.
- Prefer offline transcription.
- Look for cached speech models before attempting downloads.
- Prefer `faster-whisper` with a local cached model when available.
- If a Python package is missing, install it into a workspace-local vendor directory instead of modifying the global Python environment.
- If sandbox restrictions block package install or model-directory access, request approval and continue.

### 3. Generate the raw transcript

- Use `scripts/transcribe_audio_to_markdown.py` when a deterministic local script is preferable.
- Use `faster-whisper` when available.
- Use `language="zh"` when the recording is clearly Chinese; otherwise follow the user's requested language or allow detection.
- Enable VAD for short pauses when it improves segmentation.
- Keep timestamps in the raw transcript.
- Save the transcript as UTF-8.

Recommended defaults for local CPU transcription:

```python
from faster_whisper import WhisperModel

model = WhisperModel(model_path, device="cpu", compute_type="int8")
segments, info = model.transcribe(
    audio_path,
    language="zh",
    task="transcribe",
    beam_size=5,
    vad_filter=True,
    condition_on_previous_text=True,
    word_timestamps=False,
)
```

### 4. Guard against encoding issues

- Do not trust a saved transcript file if it shows mojibake or garbled Chinese.
- If encoding corruption appears, reuse the direct model output or rewrite the transcript file as UTF-8.
- Treat the direct transcription result as authoritative, not a broken intermediate file.

### 5. Build the Markdown deliverable

Use a structure close to this unless the user asks for a different format:

1. Notes or caveats
2. Key facts
3. Cleaned version or translated version
4. Raw transcript, unchanged
5. Action items

For each section:

- Notes or caveats
  State obvious uncertainties such as school names, person names, or ASR mistakes.
- Key facts
  Summarize times, locations, required documents, official channels, and deadlines.
- Cleaned version or translated version
  Write a readable version for the user.
- Raw transcript, unchanged
  Paste the raw transcript exactly as produced, including timestamps if they exist.
- Action items
  Extract concrete next actions as checkboxes.

### 6. Handle translation requests carefully

- If the user explicitly asks for translation into another language, translate into that target language.
- If the source audio is already Chinese and the user asks for a translated version without naming another language, treat that as a cleaned Chinese rewrite unless the user says otherwise.
- Do not silently rewrite the raw transcript section.

### 7. Normalize relative dates and times

- Convert relative phrases such as "today", "tomorrow", "next Monday", or "next Tuesday at 1 PM" into explicit calendar dates when enough context exists.
- Use the current date and the user's locale/time zone to infer the intended date.
- Write the explicit date in the Markdown when ambiguity is possible.
- Preserve the spoken wording only in the raw transcript section.

### 8. Extract action items

Extract only actions the user can actually perform. Typical items include:

- Downloading or printing a document
- Verifying identity details or registration info
- Bringing documents to a location
- Contacting an office if information is wrong
- Reviewing instructions before an interview or exam
- Showing up at a specific time and place

Prefer checklist items with explicit dates when dates are known.

### 9. Deliver the result

- Save the Markdown file.
- Return the file path.
- Summarize the most important action items in the final response.
- Mention any names, dates, or places that may need manual confirmation because of ASR uncertainty.

## Resources

### scripts/

- `scripts/transcribe_audio_to_markdown.py`
  Run a local faster-whisper transcription and generate:
  - `transcript_<stem>.txt`
  - `<stem>.md`

Use the script for the mechanical first pass, then complete the final cleaned version and action items in the Markdown file.

## Practical Notes

- Preserve the exact raw transcript when the user says not to modify it.
- Keep the cleaned section readable, but do not invent facts that were not in the recording.
- If the recording is extremely short or noisy, say that the transcript may need manual review.
- If the user asks for only one artifact, still prefer saving the Markdown file unless they explicitly ask for inline text only.

## Example User Requests

- `Turn this .m4a file into Markdown and extract action items.`
- `Transcribe this call, keep the raw transcript, and do not modify it.`
- `Rewrite this voice note into a readable note and list the follow-ups.`
- `Translate this recording into English and include the original transcript and action items.`
