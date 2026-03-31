import re
import base64
import json
from datetime import datetime
from dateutil import parser as dateparser
import anthropic
import os

# Lines to skip when looking for the description
_SKIP_PATTERNS = [
    r'^\d{1,2}/\w+/\d{4}',           # date headers
    r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
    r'^start\s',
    r'^finish\s',
    r'^break\s',
    r'^\d+:\d+hrs',                   # duration lines like "6:30hrs + ..."
    r'intially viewed',
    r'initially viewed',
    r'^special uniform',
    r'strath village',                 # location
]

def _is_skip_line(line: str) -> bool:
    low = line.lower().strip()
    return any(re.match(p, low) for p in _SKIP_PATTERNS)


def parse_text(text: str) -> list[dict]:
    """Parse pasted schedule text and return list of shift dicts."""
    blocks = re.split(r'\n{2,}', text.strip())
    shifts = []
    for block in blocks:
        shift = _parse_block(block)
        if shift:
            shifts.append(shift)
    return shifts


def _parse_block(block: str) -> dict | None:
    lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
    if not lines:
        return None

    start_dt = None
    end_dt = None
    description = None
    special_uniform = False

    for line in lines:
        # Start time: "Start 6:00 AM Monday 06/Apr/2026"
        m = re.match(
            r'start\s+(\d{1,2}:\d{2}\s*[ap]m)\s+\w+\s+(\d{1,2}/\w+/\d{4})',
            line, re.IGNORECASE
        )
        if m:
            start_dt = dateparser.parse(f"{m.group(2)} {m.group(1)}", dayfirst=True)
            continue

        # Finish time: "Finish 1:00 PM Monday 06/Apr/2026"
        m = re.match(
            r'finish\s+(\d{1,2}:\d{2}\s*[ap]m)',
            line, re.IGNORECASE
        )
        if m and start_dt:
            end_dt = dateparser.parse(f"{start_dt.strftime('%d/%b/%Y')} {m.group(1)}", dayfirst=True)
            continue

        if 'special uniform is required' in line.lower():
            special_uniform = True
            continue

    # Description: last non-skip line in the block
    for line in reversed(lines):
        if not _is_skip_line(line) and line:
            description = line
            break

    if not start_dt or not end_dt:
        return None

    return {
        "date": start_dt.strftime("%Y-%m-%d"),
        "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "end": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "description": description or "",
        "special_uniform": special_uniform,
    }


def parse_image(image_bytes: bytes, mime_type: str = "image/png") -> list[dict]:
    """Send image to Claude Vision and extract shifts as structured data."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    prompt = """Extract all work shifts from this schedule image. Return ONLY a JSON array with no additional text.

Each shift object must have these exact keys:
- "date": ISO date string "YYYY-MM-DD"
- "start": ISO datetime "YYYY-MM-DDTHH:MM:SS" (24-hour)
- "end": ISO datetime "YYYY-MM-DDTHH:MM:SS" (24-hour)
- "description": the role/shift type line (e.g. "DT2:DT Intermediate - OTC"), NOT break times or location
- "special_uniform": boolean, true if "Special Uniform is Required" appears

Example output:
[
  {
    "date": "2026-04-06",
    "start": "2026-04-06T06:00:00",
    "end": "2026-04-06T13:00:00",
    "description": "DT2:DT Intermediate - OTC",
    "special_uniform": false
  }
]"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    return json.loads(raw)
