#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_provenance_gate.py —— GATE_4 provenance/attribution 回归（126B·上级令五）

⛔ 上级令五指定之三条回归：
  P1 C卷 `uncertain`        → 不得表述「胡老本人说」
  P2 解读／传真系 `editor_compiled` → 不得自动表述「胡老本人改变观点」
  P3 讲伤寒 `hu_lecture`    → 可表述为直接讲课文本，**但仍保留【整理记录】之媒介属性**

⛔ 并钉住令五之硬约束：`editor_compiled` **不得计入** `speaker_unresolved`。
"""
import json
import os
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, B)
from tools.audit_population_census import gate_provenance, ST_ISSUE, ST_OK  # noqa: E402
from tools.retrieval_integrity_audit import SPEAKER  # noqa: E402

G4 = json.load(open(os.path.join(B, "schema", "retrieval_gates_v0.json"),
                   encoding="utf-8"))["GATE_4_provenance_attribution"]
FAIL = []


def ck(n, c, w=""):
    print(("✅PASS " if c else "⛔FAIL ") + n + ("" if c else "   " + w))
    if not c:
        FAIL.append(n)


def probe(payload):
    st, notes, sub = gate_provenance({"payload": payload, "object_id": "X"})
    return st, sub


# ── 闸四之形制 ──
ck("G4 已正式立闸", bool(G4))
for k in ("D1_speaker_identity_unresolved", "D2_attribution_overreach",
          "D3_source_version_unresolved", "D4_passage_authorship_unresolved"):
    ck("G4 子类 %s 已立" % k, k in G4["subtypes"])
ck("G4 六项检查俱全", len(G4["checks"]) == 6)
for h in ("uncertain", "editor_compiled", "publication_date", "same_style_family"):
    ck("G4 硬约束含 `%s`" % h, any(h in x for x in G4["hard_constraints"]))

# ── P1：C卷 uncertain 不得作胡老本人归因 ──
st, sub = probe({"src": "A·C卷·145454", "text": "**胡老说**血不足以荣脉则脉结代"})
ck("⭐P1 C卷＋「胡老说」 ⇒ D2 attribution_overreach", "D2_attribution_overreach" in sub, str(sub))
ck("⭐P1 且同时记 D1（C卷 speaker 未知）", "D1_speaker_identity_unresolved" in sub, str(sub))

st, sub = probe({"src": "A·C卷·145454", "text": "C卷（注解本，speaker 未定）作：血不足以荣脉则脉结代"})
ck("⭐P1b 改为合规措辞后，D2 不再命中", "D2_attribution_overreach" not in sub, str(sub))

# ── P2：editor_compiled 不得自动升为 hu_direct ──
st, sub = probe({"src": "A·解读·100487", "text": "这是**胡老自身**版本变化，晚年改说"})
ck("⭐P2 「胡老自身版本变化」 ⇒ D2", "D2_attribution_overreach" in sub, str(sub))
ck("⛔P2 且 editor_compiled **不得**计入 D1",
   "D1_speaker_identity_unresolved" not in sub, "editor 被错计为 speaker 未知：%s" % sub)
ck("⭐P2 但须记 D4（该段执笔人未标）", "D4_passage_authorship_unresolved" in sub, str(sub))

# ── P3：hu_lecture 可作直接讲课文本 ──
st, sub = probe({"src": "A·讲伤寒·112879", "text": "**胡老说**：不能光凭脉，必须脉证结合起来看"})
ck("⭐P3 讲伤寒＋胡老归因 ⇒ 不判 overreach", "D2_attribution_overreach" not in sub, str(sub))
ck("⭐P3 亦不判 D1／D4", not ({"D1_speaker_identity_unresolved",
                              "D4_passage_authorship_unresolved"} & set(sub)), str(sub))
ck("⭐P3 媒介属性已在 schema 中保留",
   "整理媒介" in G4["attribution_levels"]["hu_direct"] or
   "整理" in G4["attribution_levels"]["hu_direct"])

# ── 谱系自身 ──
ck("⛔ `带教` 标为冯世纶本人（非胡老）", SPEAKER["带教"] == "editor_compiled_feng")
ck("⛔ C卷 仍为 uncertain", SPEAKER["C卷"] == "uncertain")
ck("⛔ 十二书皆已定或显式 unknown", len(SPEAKER) == 12 and all(SPEAKER.values()))

print("\n失败 %d 项%s" % (len(FAIL), ("：" + "｜".join(FAIL)) if FAIL else ""))
sys.exit(1 if FAIL else 0)
