# 小说写作纪律 skill：《我听见她的死》

这是一套和具体模型无关的**完整细则**写作纪律包，写、改、审连载小说《我听见她的死》时用。Claude Code、Cursor、Codex、ChatGPT、Gemini 等任何写作助手都可以读它，用同一套规则、账本口径和自检脚本，保证不同助手写出来的章节格式、调性、节奏一致。

**核心文件是 `skills/novel-writing-discipline/SKILL.md`（完整细则，自包含）。** 写或审任何一章之前都要先读这一份；只读这一份即可执行全部纪律。`references/` 是补充证据与蒸馏底稿，不是执行前提。

## 目录

```
AGENTS.md                                   给各类 agent 的入口指引
skills/novel-writing-discipline/SKILL.md    主 skill（YAML 头 + 完整细则正文）
scripts/chapter_selfcheck.py                单章硬指标自检（入口）
scripts/selfcheck_metrics.py                计量函数（自检依赖）
scripts/baseline_866.json                   参考书全书统计基准（只有数字）
scripts/sample_chapter.md                   自检用的小样例（自写，与本书无关）
scripts/README.md                           脚本说明
references/                                 补充证据 / 蒸馏底稿（写作纪律全文等）
```

## 在各工具里怎么用

**Claude Code**
- 项目级：把 `skills/novel-writing-discipline/` 整个复制到小说项目的 `.claude/skills/` 下（变成 `.claude/skills/novel-writing-discipline/SKILL.md`）。
- 全局：复制到 `~/.claude/skills/`。
- `references/` 和 `scripts/` 也建议一起带上（查证据时用）。最省事的做法是把整个仓库放进项目里（例如 `tools/novel-skill/`），再把 `skills/novel-writing-discipline` 复制或软链接到 `.claude/skills/`。

**Cursor**
- 支持 skills 的版本：复制到项目 `.cursor/skills/novel-writing-discipline/`。
- 也可以用 rules：在 `.cursor/rules/` 新建一条规则（例如 `novel.mdc`），写上「写、改、审章节前先读 skills/novel-writing-discipline/SKILL.md，并按其中完整细则执行」，或者直接把 SKILL.md 正文粘进去。

**Codex / 其他读 AGENTS.md 的 agent**
- 把本仓库放进小说项目，根目录的 `AGENTS.md` 已经指向 SKILL.md。项目已有 AGENTS.md 的话，把本仓库 AGENTS.md 里那几行追加进去，路径改成实际位置。

**ChatGPT / Gemini（网页或 App）**
- 建一个 Project（ChatGPT）或 Gem（Gemini），把 `SKILL.md` 作为主知识文件上传；需要查证据时再加 `references/`。项目说明里写：「写、改、审《我听见她的死》任何章节时，严格按 SKILL.md 完整细则执行。」
- 没有项目功能时，把 SKILL.md 全文粘到对话开头。
- 网页环境一般跑不了脚本：可以在本地跑完把输出贴进去，或让助手按 SKILL.md 硬指标表逐项目测，并在回执里注明「未跑脚本」。

## 自检脚本

只需要 Python 3.8+，不用装任何第三方库。

```
python3 scripts/chapter_selfcheck.py scripts/sample_chapter.md                 # 先确认能跑
python3 scripts/chapter_selfcheck.py "正文/第006章 章名-交付版.md"             # 检查一章
python3 scripts/chapter_selfcheck.py a.md b.md --no-color > 自检.txt           # 多章、存档
python3 scripts/chapter_selfcheck.py 章.md --json                              # 机器可读
```

- 一共 16 项硬指标，涵盖段长、分句、身体词、情绪词、「又」、段末金句、「不是…，是」、章首章末长度、语气词和感叹号。越界项会标红并给出行号。
- 退出码 0 表示全部达标，1 表示有越界项。
- 骨架重复、说停就停、打断来源这些要人读，脚本测不了。**脚本达标只是交审前的底线，不代表写得好。**
- 交付格式：段首两个全角空格、段间空行；脚本分段时全角空格不计字。

## 状态纪律（一定要看）

- SKILL.md 里每条写法都带一个标记：
  - 【用户定】：作者亲口下的指令。
  - 【已用户反馈】：有作者实读反馈作依据，但按它写出来的新版本仍然要等作者再读。
  - 【待反馈】：从参考书蒸馏、由我们推出来的写法，**没有被证明有效**，只能当候选。
  - 【推断】：迁移用法是我们推出来的，不是参考书作者的意图。
- 没有作者本人的实读反馈，任何章节都不能叫「定稿」，也不能写「已改善」「已有效」。
- 自评、字数、脚本达标都不是进步证据。

## 2026-11-02 用户定口径（摘要）

- **交付格式**：首行 `# 《我听见她的死》`，段首两个全角空格，段间空一行；旧章不重排。
- **金手指无冷却**：不设冷却期，不得写「冷却中只给碎片」；代价写情绪残留 / 同链不重刷。
- **被害段阻挠者要冷**：司机/保安话少、不接话、例行动作、显然不是第一次；不替自己解释算盘。

## 不在本仓库里的东西（只在作者本地）

- 小说正文 `正文/` 和各章审核、回执。
- 项目账本：`连载总账.md`、`章节账本.md`、`伏笔与钩子总账.md`、`人物与势力账本.md`、`设定总纲.md`、`全书卷纲.md`、`主题完善稿.md`。写章前要读，向作者要最新版。
- `写作技巧/写作技巧总汇.md`：多书逐书技巧汇总，约 8 万行（~4.5MB），按书分的原始笔记，太大，**不进本仓库**，只留在本地。
- 各参考书的原文和逐书蒸馏报告。仓库**不收任何参考书原文**；`references/` 里原先较长的原文摘录已删除并改为转述，只保留章号和机制分析。

## 版权与边界

- 参考书只学写作机制，不搬角色、剧情、世界观、梗、原句和标志性句式。
- 成人内容只限成年角色、当下自愿，说停就停；禁止任何未成年人性化。详见 SKILL.md。
