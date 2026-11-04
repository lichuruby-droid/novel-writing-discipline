# scripts

- `chapter_selfcheck.py`：单章硬指标自检入口（16 项，阈值见 `../skills/novel-writing-discipline/SKILL.md` 第 4.1 节、`../references/写作纪律.md` §9.1）。
- `selfcheck_metrics.py`：计量函数和词表（身体词、情绪词、比喻词、语气词等），必须和入口放在同一目录。
- `baseline_866.json`：参考书全书（1–866 章去重）统计基准，只有数字，不含原文；可选，缺了用脚本内置的同一组数字（只少了 P10/P50/P90 一列）。
- `sample_chapter.md`：自写的小样例，用来确认脚本能跑；它会故意越界几项，退出码是 1。

用法：

```
python3 scripts/chapter_selfcheck.py 章.md [更多章.md] [--start 行号] [--no-color|--color] [--json]
```

- 自动从「第N章」标题的下一行起算；段首全角空格不计字；空行忽略。所以缩进格式和「不缩进＋空一行」格式结果一样。
- 退出码：0 表示全部达标，1 表示有越界项。
- 只依赖 Python 3.8+ 标准库。
