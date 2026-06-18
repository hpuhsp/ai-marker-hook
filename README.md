# ai-marker-hook

[中文](README.zh.md) | **English**

A `PostToolUse` hook for Claude Code and Qoder that automatically annotates AI-generated or AI-modified code blocks with structured authorship comments — recording the model, date, version, change type, and author. Designed for team AI usage tracking and code traceability.

---

## Marker Format

### New file (Write / create_file)

A single file-level header is inserted at the top:

```java
// === AI GENERATED FILE | claude-sonnet-4-6 | 2026-06-18 | v1.2.0 | Zhang San ===
```

### New code block (Edit with no original content)

```java
// === AI GENERATED BEGIN | claude-sonnet-4-6 | 2026-06-18 | v1.2.0 | generated | Zhang San ===
public void newMethod() {
    // ...
}
// === AI GENERATED END ===
```

### Modified code (change ratio < 80%)

```python
# === AI MODIFIED BEGIN | claude-sonnet-4-6 | 2026-06-18 | v1.2.0 | modified | Zhang San ===
def updated_function():
    pass
# === AI MODIFIED END ===
```

### Major rewrite (change ratio ≥ 80%)

The original code is commented out inline for easy comparison:

```python
# === AI REPLACED BEGIN | claude-sonnet-4-6 | 2026-06-18 | v1.2.0 | replaced | Zhang San ===
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
=== AI {TYPE} BEGIN | {model} | {date} | {version} | {type} | {author} ===
```

| Field | Description |
|-------|-------------|
| `TYPE` | `GENERATED` / `MODIFIED` / `REPLACED` |
| `model` | AI model name, read from environment variables |
| `date` | ISO-format date of the edit |
| `version` | Project version, auto-detected from version files |
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

#### Claude Code — global (all projects)

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
            "command": "python \"C:/Users/<username>/.claude/hooks/ai_marker.py\""
          }
        ]
      }
    ]
  }
}
```

#### Claude Code — project-level

Create `.claude/settings.json` in the project root with the same content.

#### Qoder — global

Edit `~/.qoder/settings.json` and add a `hooks` key:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|search_replace|create_file",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Users/<username>/.claude/hooks/ai_marker.py\""
          }
        ]
      }
    ]
  }
}
```

#### Qoder — project-level

Create `.qoder/settings.json` in the project root with the same content.

> Claude Code and Qoder share a single `ai_marker.py` file — no need to copy it.

### Step 3 (optional) — Pin project version

If you prefer a fixed version string over auto-detection, pass `--project-version` in the command:

```json
"command": "python \"~/.claude/hooks/ai_marker.py\" --project-version v2.1.0"
```

Priority: `--project-version` arg → version file auto-detection → `v?.?.?`

---

## Environment Variables

Model name is resolved in this order (no manual setup needed):

```
CLAUDE_MODEL → QODER_MODEL → AI_MODEL → "unknown-model"
```

Claude Code injects `CLAUDE_MODEL` automatically; Qoder injects `QODER_MODEL`.

---

## Version Auto-Detection

The script walks up to 6 parent directories looking for:

| File | Project type |
|------|-------------|
| `package.json` | Node.js |
| `pom.xml` | Maven |
| `build.gradle` / `build.gradle.kts` | Gradle |
| `pyproject.toml` | Python |
| `gradle.properties` | Gradle |
| `Cargo.toml` | Rust |

Falls back to `v?.?.?` if none found.

---

## Verify It Works

After configuring, ask the AI to edit any supported file and check for `=== AI ... BEGIN` markers.

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
