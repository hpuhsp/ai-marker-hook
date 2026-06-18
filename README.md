# ai-marker-hook

[中文](README.zh.md) | **English**

A `PostToolUse` hook for Claude Code that automatically annotates AI-generated or AI-modified code blocks with structured authorship comments — recording the model, date, change type, and author. Designed for team AI usage tracking and code traceability.

---

## Marker Format

### New file (Write)

A single file-level header is inserted at the top:

```java
// === AI GENERATED FILE | claude-sonnet-4-6 | 2026-06-18 | Zhang San ===
```

### New code block (Edit with no original content)

```java
// === AI GENERATED BEGIN | claude-sonnet-4-6 | 2026-06-18 | generated | Zhang San ===
public void newMethod() {
    // ...
}
// === AI GENERATED END ===
```

### Modified code (change ratio < 90%)

```python
# === AI MODIFIED BEGIN | claude-sonnet-4-6 | 2026-06-18 | modified | Zhang San ===
def updated_function():
    pass
# === AI MODIFIED END ===
```

### Major rewrite (change ratio ≥ 90%)

The original code is commented out inline for easy comparison:

```python
# === AI REPLACED BEGIN | claude-sonnet-4-6 | 2026-06-18 | replaced | Zhang San ===
# [ORIGINAL]
# def old_function():
#     old_logic()
# [/ORIGINAL]
def new_function():
    new_logic()
# === AI REPLACED END ===
```

---

## Header Fields

```
=== AI {TYPE} BEGIN | {model} | {date} | {type} | {author} ===
```

| Field | Description |
|-------|-------------|
| `TYPE` | `GENERATED` / `MODIFIED` / `REPLACED` |
| `model` | AI model name, read from transcript or `CLAUDE_MODEL` env var |
| `date` | ISO-format date of the edit |
| `type` | Same as TYPE, lowercase |
| `author` | `git config user.name` |

---

## Supported Languages

| Comment style | Languages / file types |
|---------------|------------------------|
| `#` | Python, Shell, Ruby, YAML, TOML, Terraform, Dockerfile |
| `//` | Java, Kotlin, JavaScript, TypeScript, Go, Swift, C/C++, C#, PHP, Rust, Scala, Dart, Groovy |
| `--` | SQL, Lua, Haskell, Elm |
| `<!-- -->` | HTML, XML, Vue, SVG |

Files with unlisted extensions are skipped silently.

---

## Stale Marker Cleanup

- **Within 6 months**: re-editing a marked block does not nest a new marker.
- **Older than 6 months**: the marker shell is stripped on the next edit, the active code is preserved, and a fresh marker is applied.

---

## Installation & Configuration

### Requirements

- Python 3.10+
- Standard library only, no extra dependencies

### Step 1 — Download the script

```bash
# macOS / Linux
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/ai_marker.py \
  https://raw.githubusercontent.com/hpuhsp/ai-marker-hook/main/ai_marker.py
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\hooks"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/hpuhsp/ai-marker-hook/main/ai_marker.py" `
  -OutFile "$env:USERPROFILE\.claude\hooks\ai_marker.py"
```

### Step 2 — Register the hook

#### Global (all projects)

Edit `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/.claude/hooks/ai_marker.py"
          }
        ]
      }
    ]
  }
}
```

#### Project-level

Create `.claude/settings.json` in the project root with the same content.

### Step 3 (optional) — Fix model name on Windows

Claude Code may not inject `CLAUDE_MODEL` into hook subprocesses on Windows. Add it explicitly to the `env` section in `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_MODEL": "claude-sonnet-4-6"
  }
}
```

Update this value when you switch models.

---

## Verify It Works

After configuring, ask Claude to edit any supported file and check for `=== AI ... BEGIN` markers.

You can also run a manual smoke test:

```bash
echo '{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/tmp/test.py",
    "old_string": "",
    "new_string": "def hello():\n    print(\"hello\")\n"
  }
}' | python ai_marker.py
```

---

## License

MIT
