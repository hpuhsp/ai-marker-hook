#!/usr/bin/env python3
"""
AI marker injection hook for Claude Code.
Wraps AI-generated/modified code sections with authorship markers.
"""

import json
import sys
import os
import re
import subprocess
import difflib
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

# ─────────────────────────── Comment style ───────────────────────────

@dataclass(frozen=True)
class CommentStyle:
    prefix: str
    is_html: bool = False

COMMENT_STYLES: dict[str, CommentStyle] = {
    **{ext: CommentStyle('#') for ext in [
        '.py', '.sh', '.bash', '.zsh', '.rb', '.r', '.rmd',
        '.yaml', '.yml', '.toml', '.tf', '.dockerfile',
    ]},
    **{ext: CommentStyle('//') for ext in [
        '.java', '.kt', '.kts', '.js', '.mjs', '.cjs',
        '.ts', '.tsx', '.jsx', '.go', '.swift',
        '.c', '.h', '.cpp', '.cc', '.cxx', '.cs',
        '.php', '.rs', '.scala', '.dart', '.groovy',
    ]},
    **{ext: CommentStyle('--') for ext in ['.sql', '.lua', '.hs', '.elm']},
    **{ext: CommentStyle('', is_html=True) for ext in [
        '.html', '.htm', '.xml', '.vue', '.svg',
    ]},
}

def get_style(file_path: str) -> CommentStyle | None:
    return COMMENT_STYLES.get(Path(file_path).suffix.lower())

# ─────────────────────────── Metadata ───────────────────────────

def model_from_transcript(transcript_path: str) -> str | None:
    try:
        lines = Path(transcript_path).read_text(encoding='utf-8').splitlines()
        for line in reversed(lines[-30:]):
            try:
                entry = json.loads(line)
                model = (entry.get('model')
                         or entry.get('message', {}).get('model'))
                if model:
                    return model
            except Exception:
                continue
    except Exception:
        pass
    return None

def git_author() -> str:
    try:
        r = subprocess.run(['git', 'config', 'user.name'],
                           capture_output=True, text=True, timeout=3)
        return r.stdout.strip() or 'unknown'
    except Exception:
        return 'unknown'

# ─────────────────────────── Marker building ───────────────────────────

TODAY = date.today().isoformat()
TODAY_DATE = date.fromisoformat(TODAY)

def build_header(style: CommentStyle, change_type: str, meta: dict) -> str:
    fields = f" | {meta['model']} | {meta['date']} | {change_type.lower()} | {meta['author']}"
    if style.is_html:
        return f"<!-- === AI {change_type} BEGIN{fields} === -->"
    return f"{style.prefix} === AI {change_type} BEGIN{fields} ==="

def build_footer(style: CommentStyle, change_type: str) -> str:
    if style.is_html:
        return f"<!-- === AI {change_type} END === -->"
    return f"{style.prefix} === AI {change_type} END ==="

def comment_out(lines: list[str], prefix: str) -> list[str]:
    return [f"{prefix} {ln}" if ln.strip() else prefix for ln in lines]

def wrap_block(code: str, style: CommentStyle, change_type: str, meta: dict) -> str:
    h = build_header(style, change_type, meta)
    f = build_footer(style, change_type)
    return h + '\n' + code.rstrip('\n') + '\n' + f + '\n'

def wrap_replaced(old: str, new: str, style: CommentStyle, meta: dict) -> str:
    h = build_header(style, 'REPLACED', meta)
    f = build_footer(style, 'REPLACED')
    if style.is_html:
        orig_block = '\n'.join(
            ['<!-- [ORIGINAL]'] + old.rstrip('\n').splitlines() + ['[/ORIGINAL] -->']
        )
    else:
        orig_block = (f"{style.prefix} [ORIGINAL]\n"
                      + '\n'.join(comment_out(old.rstrip('\n').splitlines(), style.prefix)) + '\n'
                      + f"{style.prefix} [/ORIGINAL]")
    return h + '\n' + orig_block + '\n' + new.rstrip('\n') + '\n' + f + '\n'

# ─────────────────────────── Change ratio ───────────────────────────

def change_ratio(old: str, new: str) -> float:
    old_lines = old.splitlines()
    if not old_lines:
        return 0.0
    matcher = difflib.SequenceMatcher(None, old_lines, new.splitlines())
    kept = sum(n for _, _, n in matcher.get_matching_blocks())
    return 1.0 - kept / len(old_lines)

def find_changed_region(old: str, new: str) -> tuple[int, int]:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    first_j, last_j = len(new_lines), -1
    for tag, _, _, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            first_j = min(first_j, j1)
            last_j  = max(last_j, j2 - 1)

    if last_j < 0:
        return 0, len(new)

    start = sum(len(l) for l in new_lines[:first_j])
    end   = sum(len(l) for l in new_lines[:last_j + 1])
    return start, end

# ─────────────────────────── Marker cleanup ───────────────────────────

DATE_RE = re.compile(r'AI \w+ BEGIN\s*\|\s*[^|]+\|\s*(\d{4}-\d{2}-\d{2})\s*\|')
CUTOFF = timedelta(days=183)
_HTML_END_RE = re.compile(r'=== AI \w+ END', re.IGNORECASE)

@lru_cache(maxsize=8)
def _marker_pat(style: CommentStyle, which: str) -> re.Pattern:
    if style.is_html:
        return re.compile(rf'<!--\s*=== AI \w+ {which}.*?===\s*-->', re.IGNORECASE)
    esc = re.escape(style.prefix)
    return re.compile(rf'^{esc}\s*=== AI \w+ {which}.*===$', re.MULTILINE | re.IGNORECASE)

def find_enclosing_marker(content: str, pos: int, style: CommentStyle) -> tuple | None:
    candidates = [(m.start(), m.end(), m.group())
                  for m in _marker_pat(style, 'BEGIN').finditer(content) if m.start() <= pos]
    if not candidates:
        return None

    b_start, b_end, b_text = candidates[-1]

    end_match = _marker_pat(style, 'END').search(content, b_end)
    if not end_match:
        return None

    e_end = end_match.end()
    if e_end < len(content) and content[e_end] == '\n':
        e_end += 1
    if not (b_start <= pos <= e_end):
        return None

    dm = DATE_RE.search(b_text)
    if not dm:
        return None
    try:
        marker_date = date.fromisoformat(dm.group(1))
    except ValueError:
        return None

    return (b_start, e_end, marker_date)

def extract_active_code(block: str, style: CommentStyle) -> str:
    lines = block.splitlines(keepends=True)
    result = []
    in_original = False

    if style.is_html:
        for i, line in enumerate(lines):
            s = line.rstrip()
            if i == 0: continue
            if _HTML_END_RE.search(s): continue
            if '<!-- [ORIGINAL]' in s: in_original = True; continue
            if '[/ORIGINAL] -->' in s: in_original = False; continue
            if not in_original:
                result.append(line)
    else:
        end_pat = _marker_pat(style, 'END')
        orig_start = f'{style.prefix} [ORIGINAL]'
        orig_end   = f'{style.prefix} [/ORIGINAL]'
        for i, line in enumerate(lines):
            s = line.rstrip()
            if i == 0: continue
            if end_pat.match(s): continue
            if s == orig_start: in_original = True; continue
            if s == orig_end:   in_original = False; continue
            if not in_original:
                result.append(line)

    return ''.join(result)

# ─────────────────────────── Write handler ───────────────────────────

def handle_write(file_path: str, tool_input: dict, style: CommentStyle, meta: dict):
    content = Path(file_path).read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)

    insert_at = 1 if lines and lines[0].startswith('#!') else 0
    if len(lines) > insert_at and 'AI GENERATED FILE' in lines[insert_at]:
        return

    if style.is_html:
        marker = (f"<!-- === AI GENERATED FILE"
                  f" | {meta['model']} | {meta['date']}"
                  f" | {meta['author']} === -->\n")
    else:
        marker = (f"{style.prefix} === AI GENERATED FILE"
                  f" | {meta['model']} | {meta['date']}"
                  f" | {meta['author']} ===\n")

    lines.insert(insert_at, marker)
    Path(file_path).write_text(''.join(lines), encoding='utf-8')

# ─────────────────────────── Edit handler ───────────────────────────

def handle_edit(file_path: str, tool_input: dict, style: CommentStyle, meta: dict):
    old_str: str = tool_input.get('old_string', '') or ''
    new_str: str = tool_input.get('new_string', '') or ''

    if not new_str:
        return

    content = Path(file_path).read_text(encoding='utf-8')

    occurrences = [m.start() for m in re.finditer(re.escape(new_str), content)]
    if len(occurrences) != 1:
        return

    pos = occurrences[0]

    enclosing = find_enclosing_marker(content, pos, style)
    if enclosing is not None:
        b_start, e_end, marker_date = enclosing
        if TODAY_DATE - marker_date <= CUTOFF:
            return
        block = content[b_start:e_end]
        content = content[:b_start] + extract_active_code(block, style) + content[e_end:]
        occurrences = [m.start() for m in re.finditer(re.escape(new_str), content)]
        if len(occurrences) != 1:
            return
        pos = occurrences[0]

    if not old_str:
        marked = wrap_block(new_str, style, 'GENERATED', meta)
    elif change_ratio(old_str, new_str) >= 0.9:
        marked = wrap_replaced(old_str, new_str, style, meta)
    else:
        c_start, c_end = find_changed_region(old_str, new_str)
        marked = (new_str[:c_start]
                  + wrap_block(new_str[c_start:c_end], style, 'MODIFIED', meta)
                  + new_str[c_end:])

    Path(file_path).write_text(
        content[:pos] + marked + content[pos + len(new_str):],
        encoding='utf-8'
    )

# ─────────────────────────── Entry point ───────────────────────────

_EXCLUDED_DIRS = [Path.home() / '.claude']

def main():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace').strip()
        data = json.loads(raw)
    except Exception:
        return

    tool_name: str = data.get('tool_name', '')
    tool_input: dict = data.get('tool_input', {})

    if tool_name not in ('Write', 'Edit'):
        return

    file_path: str = tool_input.get('file_path', '')
    if not file_path:
        return

    resolved = Path(file_path).resolve()
    for excluded in _EXCLUDED_DIRS:
        try:
            resolved.relative_to(excluded)
            return
        except ValueError:
            pass

    style = get_style(file_path)
    if style is None:
        return

    if not Path(file_path).exists():
        return

    model = (model_from_transcript(data.get('transcript_path', ''))
             or os.environ.get('CLAUDE_MODEL')
             or os.environ.get('AI_MODEL')
             or 'claude')

    meta = {
        'model':  model,
        'date':   TODAY,
        'author': git_author(),
    }

    try:
        if tool_name == 'Write':
            handle_write(file_path, tool_input, style, meta)
        else:
            handle_edit(file_path, tool_input, style, meta)
    except Exception:
        pass

if __name__ == '__main__':
    main()
