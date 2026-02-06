# 仓库规范

## 适用范围
- 本仓库用于存放可复用的 OpenAI Codex Agent Skills。
- 技能内容应保持为文件形态，便于在 git 中审阅与追踪。

## Skill 目录结构（Codex）
- 每个 skill 使用独立目录，且必须包含 `SKILL.md`。
- 推荐结构：
  - `SKILL.md`（必需）
  - `scripts/`（可选，可执行辅助脚本）
  - `references/`（可选，深度参考资料）
  - `assets/`（可选，模板或静态资源）
- 仓库顶层文档保持在 `README.md` 与 `LICENSE`。

## `SKILL.md` 要求
- `SKILL.md` 顶部必须包含 YAML frontmatter。
- 必填字段：
  - `name`
  - `description`
- OpenAI 可选字段：
  - `openai.tools`（skill 依赖的工具数组）
- 文档编写遵循“渐进披露”：
  - `SKILL.md` 保持简洁。
  - 详细内容放入 `references/`，按需加载。

## Skill 发现路径（Codex）
- Codex 按以下顺序查找目录，命中同名 skill 后即停止继续查找：
  1. `./.agents/skills`
  2. `./agents/skills`
  3. `./skills`
  4. 父目录（向上遍历时重复以上三个路径）
  5. `~/.agents/skills`
  6. `~/.config/agents/skills`
  7. `/etc/agents/skills`
- 父目录向上遍历有边界：从 CWD 和 repo root 分别向上最多 5 层。
- 命名规则：目录名使用小写加连字符（kebab-case），并与 skill 的 `name` 保持一致。
- 说明：部分 Codex 页面仍展示历史 `.codex/skills` 示例；本仓库优先使用 `.agents/skills`。

## 编写风格
- Python：4 空格缩进，文件名与函数名使用 snake_case。
- Markdown：标题简短、要点清晰，命令与示例使用代码块。
- 示例应尽量可复现、可执行。

## 校验命令
- 列出 skill 文件：`find skills .agents/skills -name SKILL.md 2>/dev/null`
- 快速检查必填 frontmatter 字段：
  - `rg -n "^name:|^description:" skills .agents/skills 2>/dev/null`
- 可选脚本执行格式：
  - `python3 <skill-path>/scripts/<script>.py`

## 测试建议
- 当前仓库未配置统一测试框架。
- 若新增测试，放在 `skills/<skill-name>/tests/`，文件命名为 `test_*.py`。
- 优先采用可重复、确定性的测试，并支持 `python3 -m pytest` 运行。

## Commit 与 PR 建议
- Commit message 使用清晰祈使句（示例：`Add ETF scenario-analysis skill`）。
- PR 建议包含：
  - skill 行为变化说明
  - 示例输入/输出
  - 相关文档或规范链接

## 官方参考
- Codex Skills 概览：`https://developers.openai.com/codex/skills`
- 创建 Skill：`https://developers.openai.com/codex/skills/create-skill`
