#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交接包生成器（126D）——给【不能读仓库】的协作线用。

用户痛点：上级线（claude.ai 对话）读不到仓库，每批都要人工复制粘贴；
而人工复制会**丢限定词**，这正是「C卷同族」硬化成断言、「63组」变成幽灵的机制。

⇒ 本工具从仓库**确定性地**生成一份可直接粘贴的现状摘要，并附每份资产的
   raw URL（本仓库为 public，`private=false` 实测），使对方能自取原文而非听转述。

用法：
    python3 tools/handoff_pack.py            # 写 docs/交接包_给上级线.md
    python3 tools/handoff_pack.py --stdout   # 只打印
"""
import json
import os
import subprocess
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "docs", "交接包_给上级线.md")
REPO = "luoyongbuxianbai-byte/claudecode-demo"

# 对方最可能需要自取的资产。⛔ 只列**现行**件，作废件不列。
KEY_ASSETS = [
    ("schema/retrieval_gates_v0.json", "四闸权威定义（GATE_1–4）"),
    ("rules/text_critical_v0.json", "text-critical 登记（胡老判错简／补字之条）"),
    ("rules/pulse_cells_v0.json", "脉象映射格（格级状态）"),
    ("rules/state_variables_v0.json", "状态变量（ordinal／graded_unscaled）"),
    ("docs/说话主体与版本_十二书体例_125批.md", "十二书 speaker map（卷首实查）"),
    ("docs/C卷_provenance调查_126批.md", "C卷 身份调查（结论：uncertain）"),
    ("docs/取证协议_source_layer_v0.md", "source_layer 命名与检索阶段"),
    ("docs/故障源计数口径_v0.md", "故障源计数口径"),
    ("evidence/审计全集普查与分母修复_126B.md", "全集普查＋四闸分母（现行统计之唯一出处）"),
    ("evidence/下游引用链审计_126B.md", "下游引用链"),
    ("evidence/翻转组_结构补齐_123批.md", "11 组翻转对 × 15 栏"),
    ("evidence/组合判定元规则_125批.md", "M1–M14 元规则"),
    ("MANIFEST.md", "资产清单（每批核一次）"),
]

SPEAKER = [
    ("讲伤寒／讲金匮", "hu_lecture", "可 hu_direct（仍须保留【讲课记录之整理媒介】属性）"),
    ("传真系／解读／病位类方解／汤液经方系／伤寒论传真／金匮要略传真／中国汤液方证／临床家",
     "editor_compiled", "只可 hu_via_editor，表述作「某整理本作……」"),
    ("带教", "editor_compiled_feng", "同上"),
    ("C卷", "uncertain（P0）", "只可 source_unattributed；⛔ 本工程引用最多的一本"),
]

HARD = [
    "speaker_status = uncertain       → ⛔ 禁 hu_direct attribution",
    "speaker_status = editor_compiled → ⛔ 禁自动升级为 hu_direct",
    "publication_date ≠ text_composition_date（⛔ 不得据出版先后论「晚年改说」）",
    "same_style_family ≠ same_book ≠ same_author",
    "⛔ 不允许仅根据文件名推作者",
    "⛔ 未采 ≠ 阴性（协议51）；unknown 不进分子，not_applicable／无锚 不进分母",
    "⛔ 闸门9⑦：不得以检索宣称「全库无此规则」",
    "⛔ 胡老判为错简／错乱／传抄误并拒绝解释之文本，不得作正证或反例，只可作 text-critical evidence",
    "⛔ 测试全绿不作为完成证明（测试只能证明已编码之错误模型未违反自己）",
]


def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, cwd=B,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "?"


def census_numbers():
    """从普查册**读回**数字，不重算——避免交接包与证据册各说各话。"""
    p = os.path.join(B, "evidence", "审计全集普查与分母修复_126B.md")
    if not os.path.exists(p):
        return None
    rows, final = [], []
    for ln in open(p, encoding="utf-8"):
        s = ln.strip()
        if s.startswith("| 闸") and "issue_found" in s:
            continue
        if s.startswith("| 闸") and s.count("|") >= 6:
            rows.append(s)
        if s.startswith("| `survives`") or s.startswith("| `downgraded`") \
           or s.startswith("| `partially_retracted`") or s.startswith("| `retracted`") \
           or s.startswith("| `unknown_pending_audit`"):
            final.append(s)
    return rows, final


def jcount(rel, key=None):
    p = os.path.join(B, rel)
    if not os.path.exists(p):
        return "?"
    d = json.load(open(p, encoding="utf-8"))
    if key and isinstance(d, dict):
        return len(d.get(key, []))
    if isinstance(d, dict):
        for k in ("passages", "cells", "variables", "rules"):
            if k in d:
                return len(d[k])
        return len(d)
    return len(d)


def main():
    head = sh("git rev-parse --short HEAD")
    branch = sh("git rev-parse --abbrev-ref HEAD")
    dirty = sh("git status --porcelain")
    raw = "https://raw.githubusercontent.com/%s/%s" % (REPO, branch)

    L = []
    w = L.append
    w("# 交接包 · 给上级线（自动生成，勿手改）\n")
    w("> ⛔ 本册由 `python3 tools/handoff_pack.py` 从仓库**确定性生成**。")
    w("> 手工转述会丢限定词——「C卷同族」硬化成断言、「63组」变成幽灵，都是这么来的。")
    w("> **凡本册与任何报告叙述冲突，以本册与其所指向之原文为准。**\n")

    w("## 〇、怎么直接取原文（不必再复制粘贴）\n")
    w("本仓库为 **public**（实测 `private=false`）。以下两条路任一可通：\n")
    w("1. **网页抓取**：下列 raw 链接是**纯文本**，任何能联网抓取的对话都可直接取。")
    w("   ⚠ 「代码沙箱无网络」与「对话能否抓网页」是两件事——前者关闭不表示后者关闭，**请先试一次**。")
    w("2. **Claude Code on the web**（claude.ai/code）开一个本仓库的会话，可直接读文件，")
    w("   无需任何粘贴。\n")
    w("```")
    w("仓库    https://github.com/%s" % REPO)
    w("分支    %s" % branch)
    w("raw 前缀 %s/<路径>" % raw)
    w("```\n")

    w("## 一、开工报账\n")
    w("| 项 | 值 |")
    w("|---|---|")
    w("| HEAD | `%s` |" % head)
    w("| 分支 | `%s` |" % branch)
    w("| 工作区 | %s |" % ("⚠ 有未提交改动" if dirty else "干净"))
    w("| 冻结件 | `V8/`／`rules/core_v0.json`／`runtime/`——126批起冻结，diff 须为 0 |")
    w("")

    w("## 二、现行裁决状态（读自普查册，非重算）\n")
    cn = census_numbers()
    if cn:
        rows, final = cn
        w("| 闸 | issue_found | eligible 分母 | 比率 | 无锚 | n/a | unknown |")
        w("|---|---|---|---|---|---|---|")
        for r in rows:
            w(r)
        w("")
        w("| 对象级裁决 | 数 |")
        w("|---|---|")
        for f in final:
            w("|".join(f.split("|")[:3]) + "|")
    else:
        w("⛔ 普查册缺失——先跑 `python3 tools/audit_population_census.py`。")
    w("")
    w("⛔ **分母纪律**：每闸各自算；`not_applicable`／无锚**不进分母**；`unknown`**不进分子**。")
    w("⛔ **对象级只可**：`survives`／`downgraded`／`partially_retracted`／`retracted`／`unknown_pending_audit`；同一对象不得重复计数。\n")

    w("## 三、十二书说话主体（卷首实查，非推定）\n")
    w("| 书 | speaker_status | 可用归因 |")
    w("|---|---|---|")
    for b, s, u in SPEAKER:
        w("| %s | `%s` | %s |" % (b, s, u))
    w("")

    w("## 四、硬约束（违反即不得入库）\n")
    w("```")
    for h in HARD:
        w(h)
    w("```\n")

    w("## 五、现行资产计数\n")
    w("| 件 | 条目 |")
    w("|---|---|")
    w("| `rules/text_critical_v0.json` | %s |" % jcount("rules/text_critical_v0.json"))
    w("| `rules/pulse_cells_v0.json` | %s |" % jcount("rules/pulse_cells_v0.json"))
    w("| `rules/state_variables_v0.json` | %s |" % jcount("rules/state_variables_v0.json"))
    w("| `tests/` | %s |" % len([f for f in os.listdir(os.path.join(B, "tests"))
                                 if f.startswith("test_") and f.endswith(".py")]))
    w("")

    w("## 六、可自取之关键资产\n")
    w("| 资产 | 是什么 | raw |")
    w("|---|---|---|")
    for rel, what in KEY_ASSETS:
        ok = "" if os.path.exists(os.path.join(B, rel)) else " ⛔缺"
        w("| `%s`%s | %s | %s/%s |" % (rel, ok, what, raw, rel))
    w("")

    w("## 七、⛔ 已知为【幽灵】者——请勿据以布置任务\n")
    w("| 名 | 实情 |")
    w("|---|---|")
    w("| 「63 组机器候选」 | ⛔ **不存在**。曾被五份报告引用，仓库内枚举不出 ⇒ 记 `PHANTOM-63FLIP` |")
    w("| 「28 条 `validation=candidate`」 | ⛔ 现行 `rules/*.json` 中 `candidate` 为 **0** 条；出自 119–120批叙述，从未落为带 ID 之资产 |")
    w("")
    w("⛔ **常设**：凡报告中称引之对象集合，须能在 repository 中被枚举出来；")
    w("枚举不出者记 `population_gap`，**不得作为待办计数**——不制造不存在的债务。\n")

    txt = "\n".join(L) + "\n"
    if "--stdout" in sys.argv:
        print(txt)
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(txt)
    print("已写 %s（%d 行）" % (OUT, txt.count("\n")))
    print("⇒ 把它整份粘给上级线，或直接给对方这一条：")
    print("   %s/docs/交接包_给上级线.md" % raw)


if __name__ == "__main__":
    main()
