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
for st in ("suspected_corruption", "rejected_by_hu", "emended_by_hu", "disputed_cross_source"):
    ck("G1 闸门·%s 只许 evidence_only" % st,
       GATE[st] == ["text_critical_evidence_only"], str(GATE[st]))
for st in ("suspected_corruption", "rejected_by_hu", "emended_by_hu", "disputed_cross_source",
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
    # ⚠ 126L 订正命名：本项**只证字段存在**，⛔ 不证归属。归属由 G4 查。
    ck("G2 %s 之 verdict_source／verdict_anchor 字段非空（⛔ 只证字段存在，不证归属）" % pid,
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

# ── G4 ⭐⭐ HARD_RULE_2 之**实执行**（126L·上级令一）────────────────
#   ⛔ 126K 只把 HARD_RULE_2 写成 schema 里的说明字符串，**没有任何代码执行它**。
#   本节做两件事：①用**一对正负控样本**证明检查器本身能判真伪；
#                ②把检查器跑在**真实数据**上，机器判不出者**必须带 attribution_review 明报**。
SPEAKER = {"讲伤寒": "hu_lecture", "讲金匮": "hu_lecture", "C卷": "uncertain",
           "解读": "editor_compiled", "传真系": "editor_compiled",
           "病位类方解": "editor_compiled", "汤液经方系": "editor_compiled",
           "中国汤液方证": "editor_compiled", "伤寒论传真": "editor_compiled",
           "金匮要略传真": "editor_compiled", "临床家": "editor_compiled",
           "带教": "editor_compiled_feng"}
# 这三个值**断言了「胡老本人」作过文本裁决**；disputed_cross_source 不作此断言。
ASSERTS_HU = {"emended_by_hu", "rejected_by_hu", "suspected_corruption"}


def anchor_books(anchor):
    return [b for b in SPEAKER if b in (anchor or "")]


def attribution_machine_verifiable(passage):
    """HARD_RULE_2 之可执行形式。
    返回 (ok, why)：ok=True 仅当【不作胡老归因】或【锚中至少一本为 hu_lecture】。
    ⛔ 本函数**不判孰正**，只判「该归因能否由机器证成」。"""
    st = passage.get("text_status")
    if st not in ASSERTS_HU:
        return True, "本值不断言胡老本人之裁决"
    bs = anchor_books(passage.get("verdict_anchor"))
    if not bs:
        return False, "锚中未识出任何已知书名"
    if any(SPEAKER[b] == "hu_lecture" for b in bs):
        return True, "锚含 hu_lecture：%s" % bs
    return False, "锚所涉之书无一为 hu_lecture：%s" % {b: SPEAKER[b] for b in bs}


# ⭐ 正负控：同一份证据，只改 text_status，检查器必须给出相反结论
_NEG = {"passage_id": "_CTRL_NEG", "text_status": "emended_by_hu",
        "verdict_anchor": "A·C卷·29360"}          # 归属未定而仍标 emended_by_hu
_POS = {"passage_id": "_CTRL_POS", "text_status": "disputed_cross_source",
        "verdict_anchor": "A·C卷·29360"}          # 同一证据，撤下确定归因
_HU  = {"passage_id": "_CTRL_HU", "text_status": "suspected_corruption",
        "verdict_anchor": "A·讲伤寒·156700"}      # 锚在 hu_lecture
ck("⭐⭐G4-负控 归属未定而标 emended_by_hu ⇒ 检查器必须判【不可证成】",
   attribution_machine_verifiable(_NEG)[0] is False, attribution_machine_verifiable(_NEG)[1])
ck("⭐⭐G4-正控 同一证据撤下确定归因后 ⇒ 检查器必须判【通过】",
   attribution_machine_verifiable(_POS)[0] is True, attribution_machine_verifiable(_POS)[1])
ck("⭐G4-正控2 锚在 hu_lecture 之胡老归因 ⇒ 通过",
   attribution_machine_verifiable(_HU)[0] is True, attribution_machine_verifiable(_HU)[1])

# ⭐ 跑在真实数据上：机器判不出者，**必须**带 attribution_review 明报
_pending = []
for pid, p in sorted(P.items()):
    ok, why = attribution_machine_verifiable(p)
    if ok:
        continue
    _pending.append(pid)
    ck("⭐G4 %s 机器判不出归因 ⇒ 须带 attribution_review 明报（⛔ 不得静默）" % pid,
       isinstance(p.get("attribution_review"), dict)
       and p["attribution_review"].get("status") == "pending_manual_review",
       why)
print("\n⚠ G4：机器可证成之胡老归因 %d 条；**待人工核验** %d 条 ⇒ %s"
      % (len([1 for p in P.values() if attribution_machine_verifiable(p)[0]
              and p["text_status"] in ASSERTS_HU]),
         len(_pending), "｜".join(_pending) or "无"))
print("⛔ 『待人工核验』**不是已验证**，也**不是已否证**——它是明报的缺口。")


print("\n失败 %d 项%s" % (len(FAIL), ("：" + "｜".join(FAIL)) if FAIL else ""))
sys.exit(1 if FAIL else 0)
