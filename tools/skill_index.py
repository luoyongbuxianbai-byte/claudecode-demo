#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""八个 skill 之【入口／现行条款／历史错案】索引（126AI 立·上级令四）

**为什么是生成器，不是手写文件。**
上级 126AI 实查指出三处不一致（交接包 HEAD 前后不符｜第六章一处说未成段一处说已新增｜
skill 里的「自我否定」配额）。⭐ **三处的共同点是：同一事实被写在两个地方，然后各改各的。**
⇒ 手写一份「skill 总览」只会成为**第四处**。

本工具从各 `SKILL.md` **确定性抽取**，因此它不会与 skill 本体分叉。

抽取三样
--------
① **入口**（何时必须用它）—— 取 frontmatter 之 `description`；
② **现行条款** —— 取正文里的 ⛔／⭐ 祈使句，**保留其原有编号与限定词**；
③ **历史错案** —— 取正文里提到的**批次号**（如 `118批`、`126AC`）及其所在整句。

⛔⛔ **本工具之限度**
  ① 它**按行抽取**，⛔ 不理解语义 —— 一条跨行的条款会被截断（输出标 `⚠截断`）。
  ② 「历史错案」按**批次号**召回，⛔ 未写批次号的错案**查不到**。
  ③ ⛔ **它不判断条款是否仍然现行** —— skill 内已被后批推翻而未删的句子，本工具照抄。
  ⇒ ⛔ **不得据本索引宣称「纪律已齐备」或「某条已废」。**

用法
----
  python3 tools/skill_index.py            # 生成 docs/skill索引_自动生成.md
  python3 tools/skill_index.py --check     # 只报差异，不写（供收工核对）
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLDIR = os.path.join(ROOT, ".claude", "skills")
OUT = os.path.join(ROOT, "docs", "skill索引_自动生成.md")

BATCH = re.compile(r'(?<![0-9A-Za-z])(\d{2,3}批|126[A-Z]{1,2})(?![0-9A-Za-z])')
CLAUSE = re.compile(r'^[\s>|*\-]*(⛔⛔|⛔|⭐⭐⭐|⭐⭐|⭐)\s*(\S.*)$')
MAXLEN = 200


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def scan(name):
    path = os.path.join(SKILLDIR, name, "SKILL.md")
    if not os.path.isfile(path):
        return None
    text = open(path, encoding="utf-8").read()
    fm = frontmatter(text)
    body = text.split("\n---", 2)[-1] if text.startswith("---") else text

    clauses, cases, seen = [], [], set()
    for ln, line in enumerate(body.splitlines(), 1):
        m = CLAUSE.match(line)
        if m:
            s = m.group(2).strip()
            # ⛔ 只收**祈使／禁令**句；标题与表头不收
            if len(s) >= 8 and not s.startswith("#") and "---" not in s:
                key = s[:60]
                if key not in seen:
                    seen.add(key)
                    trunc = len(s) > MAXLEN
                    clauses.append((m.group(1), s[:MAXLEN], trunc))
        for b in BATCH.findall(line):
            sent = line.strip()
            if len(sent) >= 10:
                cases.append((b, sent[:MAXLEN], len(sent) > MAXLEN))
    return {
        "name": name,
        "desc": fm.get("description", "⛔ 无 description"),
        "lines": len(body.splitlines()),
        "clauses": clauses,
        "cases": cases,
    }


def render(skills):
    L = []
    w = L.append
    w("# skill 索引（**自动生成，勿手改**）\n")
    w("> 由 `python3 tools/skill_index.py` 从各 `SKILL.md` 确定性抽取。")
    w("> ⭐ **126AI 立（上级令四）**：整合入口、现行条款与历史错案，**保留编号与限定条件**。")
    w("> ⛔⛔ **三条限度**：①按行抽取，⛔ 不理解语义（跨行条款会截断，标 `⚠截断`）；")
    w("> ②「历史错案」按**批次号**召回，⛔ 未写批次号者查不到；")
    w("> ③ ⛔ **不判断条款是否仍然现行** —— 被后批推翻而未删者，本工具照抄。")
    w("> ⇒ ⛔ **不得据本索引宣称「纪律已齐备」或「某条已废」。**\n")

    w("## 一、入口一览（**何时必须用它**）\n")
    w("| skill | 行数 | 条款 | 错案 | 入口 |")
    w("|---|---:|---:|---:|---|")
    for s in skills:
        d = s["desc"].replace("|", "｜")
        w("| `%s` | %d | %d | %d | %s |"
          % (s["name"], s["lines"], len(s["clauses"]), len(s["cases"]),
             d[:150] + ("…" if len(d) > 150 else "")))
    w("")

    w("## 二、历史错案索引（⭐ 按批次号，⛔ 保留原句）\n")
    bybatch = {}
    for s in skills:
        for b, sent, t in s["cases"]:
            bybatch.setdefault(b, []).append((s["name"], sent, t))
    def key(b):
        m = re.match(r'^(\d+)批$', b)
        return (0, int(m.group(1)), "") if m else (1, 126, b)
    for b in sorted(bybatch, key=key):
        w("### `%s`（%d 处）\n" % (b, len(bybatch[b])))
        for nm, sent, t in bybatch[b]:
            w("- **%s** — %s%s" % (nm, sent, " ⚠截断" if t else ""))
        w("")

    w("## 三、现行条款（⭐ 逐 skill，⛔ 保留原符号与限定词）\n")
    for s in skills:
        w("### `%s`　（%d 条）\n" % (s["name"], len(s["clauses"])))
        for mark, body, t in s["clauses"]:
            w("- %s %s%s" % (mark, body, " ⚠截断" if t else ""))
        w("")
    return "\n".join(L) + "\n"


def main():
    names = sorted(d for d in os.listdir(SKILLDIR)
                   if os.path.isfile(os.path.join(SKILLDIR, d, "SKILL.md")))
    skills = [x for x in (scan(n) for n in names) if x]
    text = render(skills)
    if "--check" in sys.argv:
        old = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        print("⚠ 索引与 skill 不同步 ⇒ 须重跑" if old != text else "✅ 索引与 skill 同步")
        return 0 if old == text else 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    print("已写 %s" % OUT)
    print("  skill %d 个｜条款 %d 条｜错案句 %d 处｜批次 %d 个"
          % (len(skills), sum(len(s["clauses"]) for s in skills),
             sum(len(s["cases"]) for s in skills),
             len({b for s in skills for b, _, _ in s["cases"]})))
    print("  ⛔ 本索引不判断条款是否仍现行（限度③）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
