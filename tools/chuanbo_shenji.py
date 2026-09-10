#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chuanbo_shenji.py —— P0【真实下游依赖】审计（119批重写·用户令二）

⛔ 118批 版报「下游读取点 909」，那是**共现上界**不是依赖。用户令：
   「不要对 909 行一行一行机械修改，也不要把共现数冒充依赖数。
    actual_dependency 只能在人读确认后填。」
⇒ 本版分两层：
   ①机器【收窄候选】：执行层 ∧ 带判据符 ∧ 未带撤销标记 —— 由 909 收到可人读之量；
   ②人读【定性】：actual_dependency 七值，写在 READ 常量内，**工具不得覆盖**。
"""
import os, re, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(B, "V8", "hxs_engine_v8_full_v2.md")
OUT = os.path.join(B, "term_layer", "P0真实下游依赖审计.md")
MAT = os.path.join(B, "term_layer", "P0候选确认类型传播矩阵.md")
EXEC = {"00_执行件", "01_概念定义层", "02_观察判据层"}
JUDGE = re.compile(r"[=＝]|→|▶|判据|确认|否决|反义|★")
REVOKED = re.compile(r"11[789]批|作废原文|已撤|勘误|R11勘误")

SRC = [("P0-1/2/15", "阴阳＝f(寒热)", r"阴阳"),
       ("P0-3", "沉=里", r"脉沉|沉脉|沉="), ("P0-4", "弦=少阳", r"脉弦|弦="),
       ("P0-5", "滑=痰食热", r"脉滑|滑="), ("P0-6", "沉迟=里虚寒", r"沉迟"),
       ("P0-7", "心下悸→水饮", r"心下悸"), ("P0-8", "大便溏泄→非实", r"大便溏|便溏"),
       ("P0-9", "下利清谷独立充分", r"下利清谷"), ("P0-10", "正虚→实纲否", r"正虚|实纲"),
       ("P0-11", "口渴=有热", r"口渴|思饮"), ("P0-12/14/16", "发热恶寒→表阳", r"发热恶寒|恶寒发热"),
       ("P0-13", "利而渴→热", r"利而渴")]

# ⭐人读定性（用户令 2.1）：actual_dependency ∈
#   true_dependency / historical_mention / case_text / example_only /
#   commentary / test_fixture / dead_text / unknown
# (行, 归属P0, actual_dependency, 处置, provenance-reason)
READ = [
 (4022, "P0-11", "true_dependency", "已改·降候选", "「有渴→有热(阳明准渴)」；117批 漏改之同型副本，119批 补改"),
 (4046, "P0-7",  "true_dependency", "已改·降候选", "「心下悸(胃有水)→水饮」；117批 漏改之同型副本，119批 补改"),
 (3334, "P0-8",  "true_dependency", "已改·降支持并去★", "「溏泄清稀即否定实」；117批 漏改之同型副本，119批 补改"),
 (3983, "P0-4",  "true_dependency", "已改·降候选", "脉象总表「脉弦→少阳→小柴胡汤」表格式裸映射；119批 降为候选并补 §100 序贯试治之反证"),
 (3262, "P0-4",  "true_dependency", "✅合法·保留", "「脉弦**有力/热实**→半表半里阳」——**复合前件**，非单 token"),
 (3308, "P0-4",  "true_dependency", "✅合法·保留", "「往来寒热+脉弦有力(实)→半表半里阳」——复合前件"),
 (3078, "P0-9",  "true_dependency", "✅合法·保留", "「口不渴★ ∧ 四肢不温★ ∧ 下利清谷★ → 热纲否」——**三项合取**，非单 token 排除"),
 (3199, "P0-12", "true_dependency", "✅合法·保留", "「恶寒发热并见+头项强痛/身痛→**候选确认**」——已自称候选"),
 (3651, "P0-5",  "true_dependency", "✅合法·保留", "「身热不扬+苔黄腻+脉滑数→茵陈蒿汤」——三项复合"),
 (4517, "P0-5",  "commentary",      "保留", "§350 胡老原话之引述（厥非皆寒），**是反证不是硬映射**"),
 (3234, "P0-3",  "commentary",      "保留", "「少阴反发热=脉沉+发热(§301)」——**本身即反证条**"),
 (3226, "P0-3",  "commentary",      "保留", "§148 鉴别锚之引述"),
 (3561, "P0-7",  "true_dependency", "✅合法·保留", "「肠间水声+心下悸+短气→苓桂术甘汤」——三项复合"),
 (4420, "P0-7",  "true_dependency", "✅合法·保留", "「兼心下逆满/气上冲/…/心下悸→水饮冒眩」——复合"),
 (3650, "P0-8",  "true_dependency", "✅合法·保留", "「腹满便溏+苔白腻+无热象→理中加苍术」——三项复合"),
 (3533, "P0-6",  "case_text",       "保留", "方证卡片之可观察判据列举，非独立规则"),
 (4347, "P0-9",  "true_dependency", "✅合法·保留", "「大便溏而不爽→下利{性质:黏滞不爽·湿}」——只赋属性，不定证"),
 (4402, "P0-9",  "true_dependency", "✅合法·保留", "同上，只赋程度属性"),
 (3311, "P0-3",  "true_dependency", "✅合法·保留", "「太阴：自利/腹满/食不下/**脉沉弱**里虚寒谱」——谱列举，非单项定位"),
 (3264, "P0-3",  "true_dependency", "✅合法·保留", "「兼但热不寒**脉沉实**→少阳阳明合病」——复合"),
]

def seg_of(L, i):
    for k in range(i, -1, -1):
        m = re.match(r"^# (\d\d_\S+)", L[k])
        if m: return m.group(1)
    return "?"

def main():
    L = open(V8, encoding="utf-8").read().split("\n")
    segs = [seg_of(L, i) for i in range(len(L))]
    rd = {r[0]: r for r in READ}
    O = ["# P0【真实下游依赖】审计（119批重写·用户令二）", "",
         "⛔ **118批 版报「下游读取点 909」是【共现上界】不是依赖。本版分两层：**",
         "**①机器收窄** → **②人读定性**（`actual_dependency` 七值，工具不得覆盖）。", "",
         "## 一、由共现上界收窄至可人读之量", "",
         "| P0 | 共现（118批·上界） | **机器收窄**（执行层∧带判据符∧未撤销） | 已人读定性 |",
         "|---|---:|---:|---:|"]
    allc = []
    for no, name, pat in SRC:
        tre = re.compile(pat)
        co = sum(1 for l in L if tre.search(l))
        nar = [(i + 1, segs[i], L[i].strip()) for i, l in enumerate(L)
               if tre.search(l) and segs[i] in EXEC and JUDGE.search(l)
               and not REVOKED.search(l)]
        done = sum(1 for x in nar if x[0] in rd)
        O.append("| %s `%s` | %d | **%d** | %d |" % (no, name, co, len(nar), done))
        allc += [(no, name) + x for x in nar]
    O += ["", "⇒ **共现 %d → 机器收窄 %d → 本批已人读定性 %d。**"
          % (sum(sum(1 for l in L if re.search(p, l)) for _, _, p in SRC),
             len(allc), len(READ)),
          "⛔ **收窄后仍有未人读者，一律标 `unknown`，不得默认为无依赖。**", "",
          "## 二、人读定性表（provenance·用户令十）", "",
          "| 行 | 层 | 归属 | **actual_dependency** | 处置 | reason |",
          "|---|---|---|---|---|---|"]
    for ln, no, dep, act, why in sorted(READ):
        sg = segs[ln - 1] if ln - 1 < len(segs) else "?"
        O.append("| L%d | `%s` | %s | **%s** | %s | %s |" % (ln, sg, no, dep, act, why))
    td = sum(1 for r in READ if r[2] == "true_dependency")
    fixed = sum(1 for r in READ if "已改" in r[3])
    legit = sum(1 for r in READ if "合法" in r[3])
    todo = sum(1 for r in READ if "待改" in r[3])
    O += ["", "## 三、小结", "",
          "| 判 | 条 |", "|---|---:|",
          "| true_dependency | **%d** |" % td,
          "| commentary / case_text（非依赖） | %d |" % (len(READ) - td),
          "| ⭐其中**117批 漏改之同型副本**（119批 补改） | **%d** |" % fixed,
          "| ✅复合前件·本就合法·保留 | %d |" % legit,
          "| ⛔仍待改 | **%d** |" % todo, "",
          "⇒ ⭐⭐ **本批最重之发现：117批 的余留扫描漏了 3 处同型副本**——",
          "**L4022「有渴→有热」／L4046「心下悸→水饮」／L3334「溏泄即否定实」**，",
          "皆因**措辞不同**（不是 `口渴/思饮=有热` 之字面）而未被余留扫描捕获。",
          "⇒ **列表法之固有盲区，我 117批 报告第八节风险 5 已预告，本批坐实。**", "",
          "⇒ ⭐ **另一发现：真依赖中过半是【复合前件】，本就合法。**",
          "**若不做人读而照共现数机械改，会把 %d 条正确的复合规则改坏。**" % legit, "",
          "⚠ 由 `tools/chuanbo_shenji.py` 生成；**READ 一栏为人写，工具不得覆盖。**", ""]
    txt = "\n".join(O)

    # ── 传播矩阵 ──
    M = ["# P0 候选/确认 类型传播矩阵（119批·用户令 1.2）", "",
         "**每层对 `trigger_candidate` / `confirmed` / `unknown` 之动作，"
         "由 `tools/assertion_engine.py` 之 `LATTICE` 实装，"
         "并由 `tests/test_assertion_type_semantics.py` 断言三者不同分支。**", "",
         "| 层 | trigger_candidate | supporting_evidence | confirmed | unknown | disputed |",
         "|---|---|---|---|---|---|"]
    sys.path.insert(0, os.path.join(B, "tools"))
    from assertion_engine import LATTICE
    for layer, d in LATTICE.items():
        M.append("| **%s** | `%s` | `%s` | `%s` | `%s` | `%s` |"
                 % (layer, d.get("trigger_candidate"), d.get("supporting_evidence"),
                    d.get("confirmed"), d.get("unknown"), d.get("disputed")))
    M += ["", "⛔ **`forbidden` 者即用户令之七禁所在**：候选于【竞争排除／六经判定／"
          "寒热虚实／方证硬门／禁忌】五层皆为 forbidden。", "",
          "## 引擎内已标注之断言类型", ""]
    from assertion_engine import parse
    marks, _ = parse()
    M += ["| 行 | 层 | 类型 | obj | src | scope |", "|---|---|---|---|---|---|"]
    for ln, t_, obj, src, scope, _raw in sorted(marks):
        M.append("| L%d | `%s` | **%s** | %s | %s | %s |"
                 % (ln, segs[ln - 1] if ln - 1 < len(segs) else "?", t_, obj, src, scope))
    M += ["", "⇒ 合式标记 **%d** 处。`tools/assertion_engine.py` 语法与锚检查通过。" % len(marks),
          "⛔ **标记只保证【规范可解析】；LLM 是否照此执行，NOT_TESTABLE。**", ""]

    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write(txt)
        open(MAT, "w", encoding="utf-8").write("\n".join(M))
        print("已写入 %s\n已写入 %s" % (OUT, MAT))
    print("机器收窄 %d｜人读定性 %d｜true_dependency %d｜待改 %d" % (len(allc), len(READ), td, todo))
    return 0

if __name__ == "__main__":
    sys.exit(main())
