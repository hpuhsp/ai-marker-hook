# ai-marker-hook

**中文** | [English](README.md)

AI 代码标记注入 Hook，兼容 Claude Code 和 Qoder。

当 AI Agent 生成或修改代码后，自动在对应代码块插入结构化标记注释，记录模型、日期、版本、操作类型及作者信息，用于团队 AI 使用度量与代码溯源。

---

## 标记格式

### 新建文件（Write / create_file）

在文件顶部插入一行文件级标记：

```java
// === AI GENERATED FILE | claude-sonnet-4-6 | 2026-06-18 | v1.2.0 | Zhang San ===
```

### 新增代码块（Edit，无原始内容）

```java
// === AI GENERATED BEGIN | claude-sonnet-4-6 | 2026-06-18 | v1.2.0 | generated | Zhang San ===
public void newMethod() {
    // ...
}
// === AI GENERATED END ===
```

### 修改代码（改动 < 80%）

```python
# === AI MODIFIED BEGIN | claude-sonnet-4-6 | 2026-06-18 | v1.2.0 | modified | Zhang San ===
def updated_function():
    pass
# === AI MODIFIED END ===
```

### 大幅重写（改动 ≥ 80%）

原始代码被注释保留，便于对比：

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

## Header 字段说明

```
=== AI {TYPE} BEGIN | {model} | {date} | {version} | {type} | {author} ===
```

| 字段 | 说明 |
|------|------|
| `TYPE` | `GENERATED` / `MODIFIED` / `REPLACED` |
| `model` | AI 模型名称，自动从环境变量读取 |
| `date` | 操作日期（ISO 格式） |
| `version` | 项目版本号，自动从版本文件读取 |
| `type` | 同 TYPE，小写 |
| `author` | `git config user.name` |

---

## 支持的语言

| 注释风格 | 语言 / 文件类型 |
|----------|----------------|
| `#` | Python, Shell, Ruby, YAML, TOML, Terraform, Dockerfile |
| `//` | Java, Kotlin, JavaScript, TypeScript, Go, Swift, C/C++, C#, PHP, Rust, Scala, Dart, Groovy |
| `--` | SQL, Lua, Haskell, Elm |
| `<!-- -->` | HTML, XML, Vue, SVG |

不在列表中的文件类型会被跳过，不插入标记。

---

## 自动清理策略

- **6 个月内**的标记：再次编辑该区域时，不重复嵌套标记。
- **超过 6 个月**的标记：下次编辑时自动剥离旧标记外壳，保留活跃代码，重新打上新标记。

---

## 安装与配置

### 前置要求

- Python 3.10+
- 标准库，无需额外依赖

### 第一步：下载脚本

```bash
# macOS / Linux
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/ai_marker.py \
  https://raw.githubusercontent.com/hpuhsp/ai-marker-hook/main/ai_marker.py
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\hooks"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/hpuhsp/ai-marker-hook/main/ai_marker.py" `
  -OutFile "$env:USERPROFILE\.claude\hooks\ai_marker.py"
```

### 第二步：配置 Hook

#### Claude Code（全局，对所有项目生效）

编辑 `~/.claude/settings.json`：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Users/<用户名>/.claude/hooks/ai_marker.py\""
          }
        ]
      }
    ]
  }
}
```

#### Claude Code（项目级，仅对当前项目生效）

在项目根目录创建 `.claude/settings.json`，内容同上。

#### Qoder（全局）

编辑 `~/.qoder/settings.json`，在顶层加入 `hooks` 字段：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|search_replace|create_file",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Users/<用户名>/.claude/hooks/ai_marker.py\""
          }
        ]
      }
    ]
  }
}
```

#### Qoder（项目级）

在项目根目录创建 `.qoder/settings.json`，内容同上。

> Claude Code 和 Qoder 共用同一个 `ai_marker.py` 文件，无需复制。

### 第三步（可选）：固定项目版本号

如果不想依赖自动检测，可在命令中传入 `--project-version` 参数：

```json
"command": "python \"~/.claude/hooks/ai_marker.py\" --project-version v2.1.0"
```

优先级：`--project-version` 参数 > 自动检测版本文件 > `v?.?.?`

---

## 环境变量说明

脚本按以下优先级读取模型名称，无需手动配置：

```
CLAUDE_MODEL → QODER_MODEL → AI_MODEL → "unknown-model"
```

Claude Code 会自动注入 `CLAUDE_MODEL`，Qoder 会自动注入 `QODER_MODEL`。

---

## 项目版本号自动检测

脚本向上遍历最多 6 层目录，依次查找以下文件：

| 文件 | 适用项目 |
|------|---------|
| `package.json` | Node.js |
| `pom.xml` | Maven |
| `build.gradle` / `build.gradle.kts` | Gradle |
| `pyproject.toml` | Python |
| `gradle.properties` | Gradle |
| `Cargo.toml` | Rust |

找不到则显示 `v?.?.?`。

---

## 验证是否生效

配置完成后，让 AI 修改任意支持语言的文件，检查文件中是否出现 `=== AI ... BEGIN` 标记。

也可以手动模拟测试：

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
