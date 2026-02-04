# agent-skills

Agent Skills精选与索引，聚焦开放标准与主流平台实现。

## 这是什么

Agent Skills 是一个开放格式，用来为智能体提供可复用的能力与专长。Skills 以“文件夹”为单位，包含说明、脚本与资源，做到一次编写、多处复用。该开放格式由 Anthropic 维护并开放社区贡献。OpenAI Codex 与 Anthropic Claude 都支持基于该标准的技能机制。

## Skill 的基本结构

技能以 `SKILL.md` 为入口文件，并可按需附带脚本、参考资料与模板等资源。典型结构如下：

```text
my-skill/
  SKILL.md        # 必需：说明 + 元数据
  scripts/        # 可选：可执行脚本
  references/     # 可选：参考文档
  assets/         # 可选：模板/资源
```

`SKILL.md` 需要包含 YAML frontmatter（例如 `name` 与 `description`）以便系统发现并自动触发。技能采用“渐进披露”机制：启动时仅加载元数据，需要时再读取说明与资源。

## OpenAI Codex 技能要点

- Codex 使用 `SKILL.md` + 目录结构描述技能，并支持显式调用（`/skills` 或 `$skill`）与隐式调用（自动触发）。
- 技能可放在 `.agents/skills` 目录中，支持仓库内多层级与用户目录等位置。
- Codex Skills 构建在开放的 Agent Skills 规范之上。

## Anthropic Claude 技能要点

- Claude Skills 是文件系统中的模块化能力，包含说明、元数据与可选脚本/模板。
- Claude 可在相关任务中自动使用技能，Anthropic 提供了预置技能，也支持自定义技能在 claude.ai、Claude Code 与 API 中使用。
- 技能基于渐进披露与文件系统加载机制，仅在需要时读取相关文件或执行脚本。

## 快速开始（通用）

1. 新建一个技能目录并添加 `SKILL.md`。
2. 在 `SKILL.md` 的 YAML frontmatter 中提供 `name` 与 `description`。
3. 需要时增加 `scripts/`、`references/`、`assets/` 等目录。
4. 依据目标平台的规则放置或注册技能（见下方链接）。

## 资源链接

- Agent Skills 开放标准（agentskills/agentskills）：https://github.com/agentskills/agentskills
- OpenAI Codex Skills 文档：https://developers.openai.com/codex/skills/
- Anthropic Agent Skills 文档：https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

## 贡献

欢迎 PR 或 issue 补充更多技能示例、模板与最佳实践。建议遵循 Agent Skills 规范，保证跨平台可复用。

## 许可证

MIT License
