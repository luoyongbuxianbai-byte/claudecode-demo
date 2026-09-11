#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_text_critical_gate.py —— text-critical gate 回归（125批·上级令八、令十⑨）

⛔ 硬规则（上级令一）：
   **胡老明确判为错简、错乱、传抄误并拒绝解释之文本，
     不得作为胡老体系规则的正证或反例；只能作为 text-critical evidence 保存。**

本器实装三件：
  G1 闸门表本身之自洽（`suspected_corruption`／`rejected_by_hu` 只许 evidence_only）
  G2 已登记之文本，其 allowed_roles 须与闸门表一致
  G3 ⭐**反向回归**：§214 不得再出现在任何 cell／翻转组之【反例】或【scope_split 依据】中
     —— 这一款若变红，即说明 124批 那个错误复活了
"""
import json
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(B, "schema", "text_critical_v0.json"), encoding="utf-8"))
D = json.load(open(os.path.join(B, "rules", "text_critical_v0.json"), encoding="utf-8"))
GATE = S["GATE"]
P = {p["passage_id"]: p for p in D["passages"]}

FAIL = []


def ck(name, cond, why=""):
    print(("✅PASS " if cond else "⛔FAIL ") + name + ("" if cond else "   " + why))
    if not cond:
        FAIL.append(name)


# ── G1 闸门表自洽 ─────────────────────────────────────────
for st in ("suspected_corruption", "rejected_by_hu", "emended_by_hu"):
    ck("G1 闸门·%s 只许 evidence_only" % st,
       GATE[st] == ["text_critical_evidence_only"], str(GATE[st]))
for st in ("suspected_corruption", "rejected_by_hu", "emended_by_hu",
           "variant", "editorial_reconstruction"):
    ck("G1 闸门·%s 不得 confirm/falsify/scope_split" % st,
       not ({"confirm", "falsify", "scope_split"} & set(GATE[st])), str(GATE[st]))
ck("G1 闸门·只有 accepted 可 falsify",
   [k for k, v in GATE.items() if "falsify" in v] == ["accepted"])
ck("G1 硬规则已写入 schema", "拒绝解释" in S["HARD_RULE"])

# ── G2 已登记文本之角色须合闸 ─────────────────────────────
ck("G2 首批样本 ≥2 条（令八指定 §214、§25 洪大）", len(P) >= 2)
for pid, p in P.items():
    st = p["text_status"]
    ck("G2 %s 之 text_status 合法" % pid, st in S["definitions"]["text_status"]["enum"])
    ck("G2 %s 之 allowed_roles 合闸" % pid,
       set(p["allowed_roles"]) <= set(GATE[st]),
       "%s ⊄ %s" % (p["allowed_roles"], GATE[st]))
    ck("⭐G2 %s 之判定须有胡老原话（不得我方径判）" % pid,
       bool(p.get("verdict_source")) and bool(p.get("verdict_anchor")))

ck("⭐§214 已登记为 rejected_by_hu", P["SW-214"]["text_status"] == "rejected_by_hu")
ck("⭐§214 之判定引了『故不释』",
   "故不释" in P["SW-214"]["verdict_source"])
ck("⭐§214 留有误用记录（防复用）", bool(P["SW-214"].get("misuse_history")))

# ── G3 ⭐反向回归：§214 不得再被当反例用 ───────────────────
def _scan(path, keys=("counterexamples", "counterexample_search", "competitor_set",
                      "falsifier", "decision", "process_stage", "state_transition")):
    """在研究层与规则层里找『214』之实际【使用】，排除 text_critical 档本身。"""
    hits = []
    raw = open(path, encoding="utf-8").read()
    for m in re.finditer(r"§?21[34]\b|§214", raw):
        w = raw[max(0, m.start() - 220): m.start() + 220]
        # 只在【反例/scope_split 依据】语境中算命中
        if any(k in w for k in ("反例", "counterexample", "scope_split", "falsif")):
            hits.append((m.start(), w[:120].replace("\n", " ")))
    return hits


targets = [os.path.join(B, "rules", "pulse_cells_v0.json"),
           os.path.join(B, "tools", "jiegou_buqi_123.py"),
           os.path.join(B, "evidence", "反例攻击_四组_124批.md"),
           os.path.join(B, "evidence", "FLIP-03_FLIP-08_重编码_124批.md")]
bad = []
for t in targets:
    if not os.path.exists(t):
        continue
    raw = open(t, encoding="utf-8").read()
    # ⛔ 初版以裸 `214` 为式 ⇒ 命中锚号里的数字片段（如 `C卷·22147`）而假红。
    #   **这与 124批 我把令一断言写得过宽是同一族错误：检测器写得比要禁的东西宽。**
    #   现只认【条号形态】：§214 / 第214条 / 214条。
    for m in re.finditer(r"(?:§|第)214(?:条)?|\b214条", raw):
        w = raw[max(0, m.start() - 260): m.start() + 260]
        if any(k in w for k in ("反例", "scope_split", "counterexample")):
            # 允许出现在【撤销说明】中
            if any(k in w for k in ("撤", "已废", "不得作", "rejected_by_hu",
                                    "错乱", "故不释", "125批")):
                continue
            bad.append((os.path.basename(t), m.start(), w[:100].replace("\n", " ")))
ck("⭐⭐G3 §214 不再被当作【活】反例／scope_split 依据", not bad,
   "仍在用：%s" % bad[:3])

print("\n失败 %d 项%s" % (len(FAIL), ("：" + "｜".join(FAIL)) if FAIL else ""))
sys.exit(1 if FAIL else 0)
