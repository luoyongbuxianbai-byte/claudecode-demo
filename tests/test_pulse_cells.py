#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pulse_cells.py —— 原子脉象 cell 校验（123批·上级令三、令十二）

⛔ `rules/pulse_cells_v0.json` 不是 Rule IR 形制，`compiler/lint_rules.py` 不校它。
   **一批规则若无人校，等于没进工程。** 本器即其校验器。

上级令十二之验收条件，本器实装其中三条：
  · 三条脉象裸映射均**不再以无 scope 的 confirm 形式存在**
  · **不把肠痈反例误写成「数绝不主热」**
  · 未新增任何无原文锚之医学规则（有源者须有 source_refs；无源者须 fail_closed）
"""
import json
import os
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(B, "schema", "pulse_cell_v0.json"), encoding="utf-8"))
D = json.load(open(os.path.join(B, "rules", "pulse_cells_v0.json"), encoding="utf-8"))
CELLS = {c["cell_id"]: c for c in D["cells"]}
V8 = open(os.path.join(B, "V8", "hxs_engine_v8_full_v2.md"), encoding="utf-8").read()

FAIL = []


def ck(name, cond, why=""):
    print(("✅PASS " if cond else "⛔FAIL ") + name + ("" if cond else "   " + why))
    if not cond:
        FAIL.append(name)


# ── schema 合规 ────────────────────────────────────────────
props = set(S["properties"])
for cid, c in CELLS.items():
    miss = [r for r in S["required"] if r not in c]
    extra = [k for k in c if k not in props]
    ck("schema %s" % cid, not miss and not extra, "缺%s 多%s" % (miss, extra))
for f in ("validation_status", "compile_status", "candidate_effect"):
    bad = [cid for cid, c in CELLS.items() if c[f] not in S["properties"][f]["enum"]]
    ck("enum %s" % f, not bad, str(bad))

# ── 上级令十二·条件1：不得以【无 scope 之 confirm】形式存在 ──
bad = [cid for cid, c in CELLS.items()
       if c["candidate_effect"] in ("confirm", "exclude")
       and c["scope"]["kind"] in ("unbounded_ILLEGAL", "unaudited")]
ck("⭐令十二①三格不得无 scope 而 confirm/exclude", not bad, str(bad))

bad = [cid for cid, c in CELLS.items()
       if c["compile_status"] == "active"
       and c["validation_status"] not in ("scope_verified", "counterexample_audited")]
ck("⭐active 须已过 scope 或反例审计", not bad, str(bad))

# ── 上级令十二·条件3：无源者须 fail_closed，不得静默生效 ──
bad = [cid for cid, c in CELLS.items()
       if c.get("object_source_status") == "unsourced"
       and c["compile_status"] not in ("fail_closed", "inactive")]
ck("⭐令十二③无源对象须 fail_closed/inactive", not bad, str(bad))

# ── 125批·令四：object_term 与 mapping 须分开答 ─────────────
AUD = {cid: c["term_audit_125"] for cid, c in CELLS.items() if "term_audit_125" in c}
ck("⭐令四·四个原判「无源」之词皆已重算", len(AUD) == 4, str(sorted(AUD)))
for cid, a in AUD.items():
    ck("⭐令四·%s 五栏俱全" % cid,
       all(k in a for k in ("1_exact_term_hit", "2_semantic_near_match",
                            "3_mapping_hit", "4_speaker", "5_verdict")))
ck("⭐⭐令四·「胃气」不得再被写成无源（实为 740 处）",
   AUD["PULSE-HUAN-ZHONGFENG"]["1_exact_term_hit"] == 740)
ck("⭐令四·「阳明气分」仍为 term_absent（0 处）",
   AUD["PULSE-HONGDA-YANGMING"]["1_exact_term_hit"] == 0)
ck("⭐令四·「心血虚」判为 term_absent 而 concept_present",
   "concept_present" in AUD["PULSE-JIEDAI-ZHIGANCAO"]["5_verdict"])
ck("⭐令四·「阳衰」判为 editor_only",
   "editor_only" in AUD["PULSE-WEI-YANGSHUAI"]["5_verdict"])

# ── 125批·令五：缓 已拆三命题 ───────────────────────────────
for cid in ("PULSE-HUAN-ZHONGFENG-A", "PULSE-HUAN-WEIQI", "ZHONGFENG-WINDCAUSE-C"):
    ck("⭐令五·%s 已立" % cid, cid in CELLS)
ck("⭐⭐令五·中风【证型标签】未被连坐（A 为 source_verified）",
   CELLS["PULSE-HUAN-ZHONGFENG-A"]["validation_status"] == "source_verified")
ck("⭐令五·唯【风邪病因】被否决（C 为 rejected）",
   CELLS["ZHONGFENG-WINDCAUSE-C"]["validation_status"] == "rejected")
ck("⭐令五·原整格已作废", CELLS["PULSE-HUAN-ZHONGFENG"]["compile_status"] == "inactive")

# ── 125批·令六：数→热 未被矫枉过正 ─────────────────────────
ola = CELLS["PULSE-SHU-HEAT"]["object_level_audit"]
ck("⭐⭐令六·「从未主张」一句已撤回",
   not any("从未主张过" in str(v) and "撤回" not in str(v) for k, v in ola.items()
           if k != "令六(125批)·收回一句"),
   "过强表述仍在")
ck("⭐令六·五类分类已立",
   set(ola["分类(125批·令六重订)"]) >= {"generic_support", "contextual_exception",
                                  "location_disambiguation", "mechanism_explanation",
                                  "formula_context"})
cd = CELLS["PULSE-SHU-HEAT"]["cannot_decide"]
for k in ("confirm", "locate", "exclude"):
    ck("⭐令六·明禁 %s" % k, any(k in x for x in cd))
ck("⭐令六·明许 support", any("可**" in x and "support" in x for x in cd))

bad = [cid for cid, c in CELLS.items()
       if not c["source_refs"] and c["compile_status"] not in ("fail_closed", "inactive")]
ck("⭐无 source_refs 者不得生效", not bad, str(bad))

# ── 上级令一：不得把肠痈反例写成「数绝不主热」 ──────────────
shu = CELLS["PULSE-SHU-HEAT"]
ck("⭐令一·`数=热` 未被反向改写为「数≠热」",
   shu["object"] == "热" and shu["candidate_effect"] == "support",
   "object=%s effect=%s" % (shu["object"], shu["candidate_effect"]))
ck("⭐令一·`数=热` 仍保有正面出处",
   any("数主热" in s or "数为热" in s for s in shu["source_refs"]),
   "正面出处被误删")
# ⛔ 令一之禁止，其要害是【不得以「可攻下与否」去否定「数—热」关系】，
#    不是「凡提到痈脓的反例一概不许挂」。
#    初版写成後者 ⇒ 把〔讲金匮·260630〕胡老「痈脓啊都是脉数无热的」这条
#    **正面的域内数—热反例**也挡掉了。已改为只禁【攻下链】式论证。
bad = [x for x in shu["counterexamples"]
       if any(k in x["text"] for k in ("可下", "不可下", "攻之", "下之"))]
ck("⭐令一·不得以【可攻下与否】否定数—热关系", not bad,
   "以治疗决策链越权否定观察—状态关系：%s" % [x["anchor"] for x in bad])
ck("⭐令一·域内数—热反例须为【热之有无】之论证",
   any("无热" in x["text"] for x in shu["counterexamples"]),
   "缺域内直接反例")
ck("`数=热` 已降为 support_only", shu["compile_status"] == "support_only")
ck("`数=热` 已写明【不能判】之事", len(shu.get("cannot_decide", [])) >= 3)

# ── 跨级直映须已撤 ────────────────────────────────────────
jd = CELLS["PULSE-JIEDAI-ZHIGANCAO"]
ck("⭐`结代→炙甘草汤` 直映已撤",
   jd["compile_status"] == "inactive" and jd["validation_status"] == "falsified_overbroad")
ck("⭐其反例含【平人脉结】",
   any("平人脉结" in x["text"] for x in jd["counterexamples"]))

# ── 「不可用之反例」须标记，不得混入有效反例 ────────────────
hd = CELLS["PULSE-HONGDA-YANGMING"]
ck("⭐§25 被标为 not_usable_emended_by_hu（胡老已判其传抄有误）",
   all(x["effect"] == "not_usable_emended_by_hu" for x in hd["counterexamples"]))
ck("⭐`洪大` 以【无源】否决而非以反例否决",
   hd["validation_status"] == "unsourced_rejected" and hd["compile_status"] == "fail_closed")

# ── V8 实文：三条裸映射须已不在 ──────────────────────────
# ⛔⛔ 本段初版写作 `"洪大=阳明气分" not in V8` —— **红了，而红得不对**：
#    V8 里那串字现在只出现在【撤销说明】中（「原格作 `洪大=阳明气分`」）。
#    这与 120批 T13c（扫描被自己那条记录禁令的注释命中）**同型，且是第四次**。
#    ⇒ 判「某规则是否还活着」，**必须过解析器看【活格】，不得对原文做子串检索。**
sys.path.insert(0, B)
from compiler.cell_parser import bare_mappings  # noqa: E402

live = {c.lhs for c in bare_mappings(os.path.join(B, "V8", "hxs_engine_v8_full_v2.md"),
                                     lambda L: "脉" in L)}
for lhs in ("数", "洪大", "结代", "浮", "紧", "缓", "细", "微"):
    ck("V8 已无【活】裸映射 `%s=…`" % lhs, lhs not in live)

# ── 未审者须一律 fail_closed ─────────────────────────────
un = [cid for cid, c in CELLS.items() if c["scope"]["kind"] == "unaudited"]
bad = [cid for cid in un if CELLS[cid]["compile_status"] != "fail_closed"]
ck("⭐scope=unaudited 者一律 fail_closed（%d 格）" % len(un), not bad, str(bad))

print("\n结果：%d 项断言｜失败 %d" % (_n(), len(FAIL)) if False else
      "\n失败 %d 项%s" % (len(FAIL), ("：" + "｜".join(FAIL)) if FAIL else ""))
sys.exit(1 if FAIL else 0)


def _n():
    return 0
