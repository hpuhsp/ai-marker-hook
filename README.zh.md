# ai-marker-hook

**中文** | [English](README.md)

Claude Code 的 `PostToolUse` Hook，在 AI 生成或修改代码后自动注入结构化标记注释，记录模型、日期、操作类型及作者信息，用于团队 AI 使用度量与代码溯源。

---

## 标记格式

### 新建文件（Write）

在文件顶部插入一行文件级标记：

```java
// === AI GENERATED FILE | claude-sonnet-4-6 | 2026-06-18 | Zhang San ===
```

### 新增代码块（Edit，无原始内容）

```java
// === AI GENERATED BEGIN | claude-sonnet-4-6 | 2026-06-18 | generated | Zhang San ===
public void newMethod() {
    // ...
}
// === AI GENERATED END ===
```

### 修改代码（改动 < 90%）

```python
# === AI MODIFIED BEGIN | claude-sonnet-4-6 | 2026-06-18 | modified | Zhang San ===
def updated_function():
    pass
# === AI MODIFIED END ===
```

### 大幅重写（改动 ≥ 90%）

原始代码被注释保留，便于对比：

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

## Header 字段说明

```
=== AI {TYPE} BEGIN | {model} | {date} | {type} | {author} ===
```

| 字段 | 说明 |
|------|------|
| `TYPE` | `GENERATED` / `MODIFIED` / `REPLACED` |
| `model` | AI 模型名称，优先从 transcript 读取，其次读取 `CLAUDE_MODEL` 环境变量 |
| `date` | 操作日期（ISO 格式） |
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

### 第二步：注册 Hook

#### 全局配置（对所有项目生效）

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
            "command": "python /path/to/.claude/hooks/ai_marker.py"
          }
        ]
      }
    ]
  }
}
```

#### 项目级配置（仅对当前项目生效）

在项目根目录创建 `.claude/settings.json`，内容同上。

### 第三步（可选）：修复 Windows 下 model 名称

Claude Code 在 Windows 上可能不会自动将 `CLAUDE_MODEL` 注入 hook 子进程。可在 `~/.claude/settings.json` 的 `env` 节显式配置：

```json
{
  "env": {
    "CLAUDE_MODEL": "claude-sonnet-4-6"
  }
}
```

切换模型时同步更新此值即可。

---

## 验证是否生效

配置完成后，让 Claude 修改任意支持语言的文件，检查文件中是否出现 `=== AI ... BEGIN` 标记。

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
