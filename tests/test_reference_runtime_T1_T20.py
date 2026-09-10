#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_reference_runtime_T1_T20.py —— T1–T20（120批·用户令十三）
⛔ 测 reference runtime 语义闭环；LLM 读 Markdown 之行为仍 NOT_TESTABLE。"""
import json, os, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, "runtime")); sys.path.insert(0, os.path.join(B, "compiler"))
from reference_evaluator import Evaluator, Case, NEUTRAL, EXEC_THRESHOLD
from lint_rules import load_all, lint

EV = Evaluator()
ALL = {r["rule_id"]: r for r in load_all()}
R = []
def ck(n, c, w=""):
    R.append((n, bool(c), w)); print("%s %-46s %s" % ("✅PASS" if c else "⛔FAIL", n, w))

def run(obs, composite=False, tx=None, rules=None):
    return (Evaluator(rules) if rules is not None else EV).run(Case(obs, composite, tx))

# ── T1–T10（119批之十项，在新 runtime 上重跑）──────────────
for tok, nm in [("脉沉","T1 脉沉"), ("脉弦","T2 脉弦"), ("口渴","T3 口渴"), ("下利","T5 下利")]:
    r = run({tok: "present"})
    ck("%s 不 confirmed" % nm, r["final_confirmed_count"] == 0, "=%d" % r["final_confirmed_count"])
    ck("%s 不排除" % nm, r["exclusion_count"] == 0, "=%d" % r["exclusion_count"])
r = run({"恶寒": "present", "发热": "present"})
ck("T4a 发热恶寒 → support 表位", "表位候选" in r["supports"], "supports=%s" % r["supports"])
ck("T4b 不单独 confirmed 太阳", r["final_confirmed_count"] == 0)
r = run({"大便溏泄": "present", "心下硬拒按": "present", "干厚苔": "present"})
ck("T6 溏泄不清零实证", r["exclusion_count"] == 0)
r = run({"四肢厥冷": "present", "口苦咽干": "present"})
ck("T7 厥冷不自动排除热", r["exclusion_count"] == 0)
r = run({"某候选": "present"})
ck("T8 仅候选 final_confirmed=0", r["final_confirmed_count"] == 0)
r = run({"某未采症": "unknown_not_asked"})
ck("T9 unknown 不产生排除", r["exclusion_count"] == 0)
ck("T10 病实与人虚可并存（无互斥规则）",
   not any(x["object"] == "实纲" and x["rule_effect"] == "exclude" for x in ALL.values()))

# ── T11 §172 太阳少阳合病反例 ─────────────────────────
r = run({"脉浮": "present", "发热": "present", "恶寒": "absent_explicit",
         "口苦咽干": "present"}, composite=True)
ck("T11 无恶寒不得排除太阳成分",
   "太阳病之归属判定" not in r["excluded"] and r["exclusion_count"] == 0,
   "excluded=%s" % r["excluded"])
ck("T11b 被撤规则未进 runtime",
   "NEC-TAIYANG-WUHAN" not in {x["rule_id"] for x in EV.rules})

# ── T12 standalone 不自动作用于 composite ─────────────
SA = [{"rule_id":"TMP-SA","proposition":"p","object":"O","scope":{"kind":"standalone_pattern"},
       "antecedent":[{"observation":"X","required_state":"present"}],"rule_effect":"confirm",
       "validation_status":"scope_verified","source_layer":"L4_hu_theory",
       "speaker_status":"hu_direct","text_status":"accepted","compile_status":"active"}]
ck("T12 standalone 不作用于 composite",
   Evaluator(SA).run(Case({"X":"present"}, composite=True))["final_confirmed_count"] == 0)
ck("T12b standalone 于非 composite 可作用",
   Evaluator(SA).run(Case({"X":"present"}, composite=False))["final_confirmed_count"] == 1)

# ── T13 support 永不自动确认 ──────────────────────────
def supports(n):
    return [{"rule_id":"S%d"%i,"proposition":"p","object":"O","scope":{"kind":"cross_scenario"},
             "antecedent":[{"observation":"X%d"%i,"required_state":"present"}],
             "rule_effect":"support","validation_status":"source_verified",
             "source_layer":"L4_hu_theory","speaker_status":"hu_direct",
             "text_status":"accepted","compile_status":"support_only"} for i in range(n)]
for n in (2, 100):
    rr = Evaluator(supports(n)).run(Case({"X%d"%i:"present" for i in range(n)}))
    ck("T13 support×%d confirm×0 → 不 confirmed" % n,
       rr["final_confirmed_count"] == 0, "support_count=%d" % rr["support_count"])
# ⛔120批 自查：T13c 初版直接扫源码文本，被【声明该禁令的注释本身】命中而假红——
#   注释里写着「不存在 support_count >= N → confirmed」。**须先剥注释再扫。**
_raw = open(os.path.join(B,"runtime","reference_evaluator.py"), encoding="utf-8").read()
src = "\n".join(l.split("#")[0] for l in _raw.split("\n"))
ck("T13c evaluator 【代码内】无 support_count>=N 升级式",
   "support_count >=" not in src and 'len(out["supports"]) >=' not in src
   and "len(supports) >=" not in src)

# ── T14 absent_explicit 本身不排除 ────────────────────
ck("T14 无 validated necessary rule 时 absent_explicit 不排除",
   run({"X": "absent_explicit"})["exclusion_count"] == 0)
EXC = [{"rule_id":"TMP-EXC","proposition":"Y⇒X","object":"Y","scope":{"kind":"cross_scenario"},
        "antecedent":[{"observation":"X","required_state":"absent_explicit"}],
        "rule_effect":"exclude","validation_status":"counterexample_audited",
        "source_layer":"L4_hu_theory","speaker_status":"hu_direct",
        "text_status":"accepted","compile_status":"active"}]
ck("T14b 有 validated scoped necessary rule 时方可排除",
   Evaluator(EXC).run(Case({"X":"absent_explicit"}))["exclusion_count"] == 1)

# ── T15 §70 scope ────────────────────────────────────
r = run({"恶寒": "absent_explicit", "但热": "present"})
ck("T15 无发汗史 → 不得调用 §70", r["final_confirmed_count"] == 0, "trace 见 skip")
r = run({"恶寒": "absent_explicit", "但热": "present"}, tx=["发汗"])
ck("T15b 有发汗史 → §70 方可确认", "实纲/阳明里实" in r["confirmed"], "confirmed=%s" % r["confirmed"])

# ── T16 legacy fail closed ───────────────────────────
ids = {x["rule_id"] for x in EV.rules}
ck("T16 未合式 IR 者不进 evaluator",
   "NEC-LGZG-QICHONG" not in ids and "JUEYIN-SHANGREXIAHAN" not in ids)
v8 = open(os.path.join(B,"V8","hxs_engine_v8_full_v2.md"), encoding="utf-8").read()
ck("T16b legacy「脉弦→少阳」不进 runtime",
   not any("少阳" in r.get("effect","") and "弦" in r.get("proposition","") for r in EV.rules))

# ── T17 validation / runtime 正交 ────────────────────
SV = [{"rule_id":"TMP-SV","proposition":"p","object":"O","scope":{"kind":"cross_scenario"},
       "antecedent":[{"observation":"X","required_state":"present"}],"rule_effect":"confirm",
       "validation_status":"source_verified","source_layer":"L4_hu_theory",
       "speaker_status":"hu_direct","text_status":"accepted","compile_status":"support_only"}]
ck("T17 source_verified 不自动 runtime confirmed",
   Evaluator(SV).run(Case({"X":"present"}))["final_confirmed_count"] == 0)
ck("T17b IR 内不得携带 runtime_status",
   all("runtime_status" not in r for r in ALL.values()))

# ── T18 compound != valid ────────────────────────────
CMP = [{"rule_id":"TMP-CMP","proposition":"A∧B∧C→Y","object":"Y","scope":{"kind":"cross_scenario"},
        "antecedent":[{"observation":x,"required_state":"present"} for x in "ABC"],
        "rule_effect":"confirm","validation_status":"candidate","source_layer":"L4_hu_theory",
        "speaker_status":"hu_direct","text_status":"accepted","compile_status":"support_only"}]
ck("T18 三项合取而 validation=candidate → 不 confirm",
   Evaluator(CMP).run(Case({x:"present" for x in "ABC"}))["final_confirmed_count"] == 0)

# ── T19 L5 不得覆盖 L4 ───────────────────────────────
j = ALL["JUEYIN-SHANGREXIAHAN"]
ck("T19 L5 与 L4 冲突 → disputed 且不 active",
   j["text_status"] == "disputed" and j["compile_status"] != "active",
   "text_status=%s compile=%s" % (j["text_status"], j["compile_status"]))
ck("T19b 两造皆保留（未删其一）",
   any("C卷·12662" in c["ref"] for c in j["counterexamples"]) and "解读·261497" in j["source_refs"])

# ── T20 unknown 始终中性 ─────────────────────────────
base = run({"恶寒": "present", "发热": "present"})
for st in ("unknown_not_recorded", "unknown_not_asked", "uncertain"):
    rr = run({"恶寒": "present", "发热": "present", "Z": st})
    ck("T20 %s 中性（不加不减不排除）" % st,
       rr["support_count"] == base["support_count"] and rr["exclusion_count"] == 0
       and rr["final_confirmed_count"] == base["final_confirmed_count"])

ok = sum(1 for _, c, _ in R if c)
print("\nT1–T20：%d/%d 通过" % (ok, len(R)))
print("⛔ 本套件为 reference-runtime；LLM 读 Markdown 之行为 NOT_TESTABLE。")
sys.exit(0 if ok == len(R) else 1)
