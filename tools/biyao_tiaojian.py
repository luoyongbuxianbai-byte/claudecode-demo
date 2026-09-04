#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""biyao_tiaojian.py —— 【必要条件表】抽取（102批·用户裁撤「通读期间不建表」令后第一件）

## 立表之由（101批实测）
全库十二书语式计量：**必要条件式 600 处｜充分条件式 24 处，比 25:1**。
→ 引擎此前一直在找「见X用Y」（充分条件），而语料主体是「无X则非Y」（必要条件）。**方向错了一百批。**

## 三栏之逻辑（上级 102批 立·对应用户三问）
| 用户之问 | 逻辑形式 | 语料形态 | 量 |
|---|---|---|---|
| 为什么是这样 | **充分条件**（见X即断） | 即可确断为／便不会错／凡…者即 | 24 |
| 为什么不能是那样 | **必要条件之逆**（无X则非） | 必…／非…不／无X则非／知不在 | 600 |
| 为什么只能是这样 | **充分必要** | ⛔**非第三类原文，乃前两类之运算结果**：以必要条件排除一切他选，余项唯一 |

⭐ 胡老排除法之所以是「简易之法」，正因其手上有 600 条必要条件而仅 24 条充分条件——**他别无他法。**

## ⛔ 本工具只做抽取，不做判定
600 为**语式计量之上界**：「必」字亦有非必要条件用法（「必须治疗」「很有必要」「必然」）。
**每条须人读判其是否真必要条件**，本工具输出候选与上下文供人读，**产出表中之「已判」栏由人填。**
⛔ **不得以语式计量之数充作必要条件之数。**

用法：python3 tools/biyao_tiaojian.py            # 抽候选，写 term_layer/必要条件表.md
     python3 tools/biyao_tiaojian.py --tier A   # 只出高精度族（供优先人读）
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus_guard import load_one, BOOKS          # 闸门9 第六款：统一入口

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "term_layer", "必要条件表.md")

WEI = r"(?:太阳|阳明|少阳|太阴|少阴|厥阴|表证|里证|半表半里|在表|在里|表位|里位|表实|表虚|里实|里虚)"

# ── 族群：A 高精度（否定式，几乎全是真必要条件）｜B 中｜C 低（须重筛）──
FAM = [
    ("A1·无X则非Y", r"无[^。，,；;]{1,12}则[^。，,；;]{0,10}(?:非|不|未)", "A"),
    ("A2·知不在",   r"知不在[^。，,；;]{0,6}", "A"),
    ("A3·则未传",   r"则未传[^。，,；;]{0,8}", "A"),
    ("A4·已罢",     r"[^。，,；;]{0,12}已罢", "A"),
    ("B1·某位必X",  WEI + r"[^。，,；;]{0,10}必[^。，,；;]{1,12}", "B"),
    ("B2·非X不Y",   r"非[^。，,；;]{1,10}不[^。，,；;]{1,10}", "B"),
    ("C1·必+主症",  r"必[^。，,；;]{0,6}(?:恶寒|发热|渴|呕|下利|烦|汗出|无汗|厥|喘)", "C"),
    ("C2·若无",     r"若无[^。，,；;]{1,12}", "C"),
]

# 充分条件族（第一栏·量小，可全列）
SUF = [
    ("S1·即可确断为", r"[^。，,；;]{0,26}即可确断为[^。，,；;]{0,10}"),
    ("S2·即可诊断为", r"[^。，,；;]{0,26}即可诊断为[^。，,；;]{0,10}"),
    ("S3·亦可确诊为", r"[^。，,；;]{0,26}亦可确诊为[^。，,；;]{0,10}"),
    ("S4·便不会错",   r"[^。，,；;]{0,30}便不会错[^。，,；;]{0,6}"),
    ("S5·凡…者即",   r"凡[^。，,；;]{2,24}者[^。，,；;]{0,4}即[^。，,；;]{0,12}"),
]

# ⛔ 排除：「必」之非必要条件用法（人读前先机械剔一层，降低人读负担）
# 103批增三类：①方名被切断（「桂枝去芍药汤」被切成「去芍药／汤中」——上级 103批 之误由此而生）
#             ②「若有若无」被 C2「若无」式切中　③叮嘱语（必须精心观察／必须明确）非判据
NOISE = re.compile(
    r"必须治疗|很有必要|必然会|不必|未必|何必|必要性|必得|势必|必至|必致|必使|必令|"
    r"若有若无|必须精心|必须明确|必须强调|必须辨|必须注意")
# 方名切断闸门：命中即弃（「去X」之后紧跟「汤」者，X 是方名的一部分，不是被去之药）
FANGMING = re.compile(r"去(?:桂|芍药|桂枝|生姜|大枣|人参)[^。，,；;]{0,4}汤")


def grab():
    T = {b: load_one(b) for b, _ in BOOKS}
    nec, suf = {}, {}
    for name, pat, tier in FAM:
        rows, seen = [], set()
        for b in T:
            for m in re.finditer(pat, T[b]):
                s = m.group(0)
                if NOISE.search(s) or FANGMING.search(s):
                    continue
                key = re.sub(r"[^一-鿿]", "", s)
                if len(key) < 4 or key in seen:
                    continue
                seen.add(key)
                ctx = T[b][max(0, m.start() - 60):m.end() + 40]
                rows.append((b, m.start(), s, ctx))
        nec[(name, tier)] = rows
    for name, pat in SUF:
        rows, seen = [], set()
        for b in T:
            for m in re.finditer(pat, T[b]):
                key = re.sub(r"[^一-鿿]", "", m.group(0))
                if key in seen:
                    continue
                seen.add(key)
                rows.append((b, m.start(), m.group(0)))
        suf[name] = rows
    return nec, suf


def main():
    nec, suf = grab()
    only = None
    if "--tier" in sys.argv:
        only = sys.argv[sys.argv.index("--tier") + 1]

    L = ["# 必要条件表（102批立·用户裁撤「不建表」令后第一件）", "",
         "> **立表之由**：101批实测 **必要条件式 600 ｜ 充分条件式 24，比 25:1**。",
         "> 引擎此前一直在找「见X用Y」，而语料主体是「无X则非Y」。",
         "> **三栏对应用户三问**：为什么是这样（充分）｜为什么不能是那样（必要之逆）｜"
         "为什么只能是这样（**前两栏之运算结果**：排除一切他选，余项唯一）。",
         "",
         "⛔ **本表为工具产出之候选池，每次重跑全量覆盖。**",
         "⭐ **人读判定不在本表，在 `term_layer/必要条件表_人读判定.md`**"
         "（103批分离；102批曾把判定写在本表内，工具一重跑即被覆盖——乙类事故同型）。",
         "⛔ **不得以语式计量之数充作必要条件之数。**",
         "⛔ **「未采 ≠ 缺失」**〔(51) 缺省不得推定〕：必要条件未见记载者入「未知」，不得据以排除。",
         ""]

    L += ["## 第一栏 · 充分条件（为什么是这样）——量小，全列", ""]
    tot_s = 0
    for name, _ in SUF:
        rows = suf[name]
        tot_s += len(rows)
        if not rows:
            continue
        L.append("### %s（%d 条）" % (name, len(rows)))
        for b, p, s in rows:
            L.append("- 〔%s·%d〕%s" % (b, p, re.sub(r"\s", "", s)))
        L.append("")
    L.insert(len(L) - 1, "**充分条件合计 %d 条。**" % tot_s)

    L += ["", "## 第二栏 · 必要条件（为什么不能是那样）", "",
          "**格式**：`〔书·字位〕原文` ｜ **违反之后果**由人读填（排除／降级／禁忌）。", ""]
    tot_n = 0
    for (name, tier), rows in nec.items():
        if only and tier != only:
            continue
        tot_n += len(rows)
        L.append("### %s · %d 条（族 %s）" % (name, len(rows), tier))
        cap = 60 if tier == "A" else 40
        for b, p, s, ctx in rows[:cap]:
            L.append("- 〔%s·%d〕**%s**　｜　…%s…"
                     % (b, p, re.sub(r"\s", "", s), re.sub(r"\s", "", ctx)[:96]))
        if len(rows) > cap:
            L.append("- …另 %d 条未列（见工具复跑）" % (len(rows) - cap))
        L.append("")

    L += ["## 第三栏 · 充分必要（为什么只能是这样）", "",
          "⛔ **本栏无原文可抄——它是第一、二栏之运算结果。**",
          "**运算规则**：以第二栏之必要条件逐项排除他选；**余项唯一者，即「只能」之判。**",
          "**此即胡老排除法之实质**〔C卷·12711〕「凡阴证除外表里者，当然即属半表半里的阴证」——",
          "**而他之所以用排除法，正因其手上有 600 条必要条件而仅 24 条充分条件。**", "",
          "⚠ **本栏须待第二栏人读判定完成后方可运算，现为空。**", ""]

    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("充分条件 %d 条｜必要条件候选 %d 条（去重后·机械剔噪后）" % (tot_s, tot_n))
    for (name, tier), rows in nec.items():
        print("   %-14s %4d  (族%s)" % (name, len(rows), tier))
    # ── 自检（闸门9 第九款：机械核验之结果须先验其漏检）──
    T = {b: load_one(b) for b, _ in BOOKS}
    gold = "所以太阳病啊必须要恶寒"           # 101批人读确认之硬必要条件，须能被抽到
    hit = any(gold[:8] in re.sub(r"\s", "", r[3]) for rows in nec.values() for r in rows)
    fake = any("虚构必恶寒之句" in r[2] for rows in nec.values() for r in rows)
    print("\n[自检] 金标准「太阳病必须要恶寒」召回：%s ｜ 虚构句零命中：%s"
          % ("✅" if hit else "⛔漏检", "✅" if not fake else "⛔"))
    assert hit, "⛔自检失败：101批人读确认之金标准未被抽到，抽取式有漏"
    print("→ %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
