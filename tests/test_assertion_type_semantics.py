#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_assertion_type_semantics.py —— T1–T10 执行语义测试（119批·用户令五 5.2）

⛔⛔ **界限（不可略）**：本套件对 `tools/assertion_engine.py`（规范之参考解析器）求解，
   **测的是【规范之实现】，不是【LLM 读引擎之实际行为】**。
   后者 **NOT_TESTABLE**——引擎是 Markdown，无可执行体。
   ⇒ 报告须分栏 `STATIC_PASS` / `EXECUTION_NOT_TESTABLE`，**不得混为 PASS**。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from assertion_engine import Resolver, parse

R = Resolver()
U = "unknown_not_asked"
P = "present"
CAND = "trigger_candidate"
SUPP = "supporting_evidence"
CONF = "confirmed"

RESULTS = []


def check(name, cond, why):
    RESULTS.append((name, bool(cond), why))
    print("%s %-34s %s" % ("✅PASS" if cond else "⛔FAIL", name, why))


def only(tok, at=CAND):
    """只有该 token 为 present，其余全 unknown"""
    return R.resolve([(tok, at, P),
                      ("其余诸项", CAND, U)])


# T1 脉沉，其余 unknown
s = only("脉沉")
check("T1a 脉沉不得confirmed里", s["final_confirmed_count"] == 0, "final_confirmed_count=%d" % s["final_confirmed_count"])
check("T1b 脉沉不得排除表", s["exclusion_count"] == 0, "exclusion_count=%d" % s["exclusion_count"])
check("T1c 脉沉不得过里证方硬门", not s["gated"], "gated=%s" % s["gated"])

# T2 脉弦
s = only("脉弦")
check("T2 脉弦不得confirmed少阳", s["final_confirmed_count"] == 0, "final_confirmed_count=%d" % s["final_confirmed_count"])

# T3 口渴
s = only("口渴")
check("T3a 口渴不得confirmed热", s["final_confirmed_count"] == 0, "=%d" % s["final_confirmed_count"])
check("T3b 口渴不得排除寒/饮", s["exclusion_count"] == 0, "=%d" % s["exclusion_count"])

# T4 发热+恶寒（规范标 supporting_evidence）
s = R.resolve([("发热恶寒", SUPP, P), ("其余", CAND, U)])
check("T4a 发热恶寒可提表位候选", "发热恶寒" in s["candidates"], "candidates=%s" % s["candidates"])
check("T4b 不得单独confirmed太阳", s["final_confirmed_count"] == 0, "=%d" % s["final_confirmed_count"])
check("T4c 不得单独confirmed阳", s["final_confirmed_count"] == 0, "单一 supporting 不足以 confirm")

# T5 下利
s = only("下利")
check("T5a 下利不得confirmed寒/虚/太阴", s["final_confirmed_count"] == 0, "=%d" % s["final_confirmed_count"])
check("T5b 下利不得排除实", s["exclusion_count"] == 0, "=%d" % s["exclusion_count"])

# T6 大便溏泄 + 心下硬拒按 + 干厚苔
s = R.resolve([("大便溏泄", SUPP, P), ("心下硬拒按", CONF, P), ("干厚苔", SUPP, P)])
check("T6 溏泄不得把实证清零", s["final_confirmed_count"] >= 1, "confirmed=%s" % s["confirmed"])

# T7 四肢厥冷 + 口苦咽干
s = R.resolve([("四肢厥冷", CAND, P), ("口苦咽干", CAND, P)])
check("T7 厥冷不得自动排除热/寒热错杂", s["exclusion_count"] == 0, "=%d" % s["exclusion_count"])

# T8 仅 trigger_candidate
s = R.resolve([("单候选", CAND, P)])
check("T8 仅候选则 final_confirmed=0", s["final_confirmed_count"] == 0, "=%d" % s["final_confirmed_count"])

# T9 unknown symptom
s = R.resolve([("某未采症", CAND, U)])
check("T9 unknown 不产生排除", s["exclusion_count"] == 0, "exclusion_count_due_to_unknown=%d" % s["exclusion_count"])

# T10 病实 confirmed + 人虚 confirmed 并存
s = R.resolve([("病实", CONF, P), ("人虚", CONF, P)])
check("T10 病实与人虚可并存", "病实" in s["confirmed"] and "人虚" in s["confirmed"], "confirmed=%s" % s["confirmed"])

# 规范六不等式之直接断言
from assertion_engine import LATTICE
check("INEQ1 candidate!=confirmed",
      LATTICE["六经判定"]["trigger_candidate"] != LATTICE["六经判定"]["confirmed"], "六经判定层动作不同")
check("INEQ2 support!=confirmed",
      LATTICE["方证硬门"]["supporting_evidence"] != LATTICE["方证硬门"]["confirmed"], "方证硬门层动作不同")
check("INEQ3 unknown!=false(不参与排除)",
      LATTICE["竞争排除"]["unknown"] == "forbidden", "unknown 于竞争排除层为 forbidden")
check("INEQ4 contraindication!=diagnostic_false",
      LATTICE["六经判定"]["contraindication"] == "none", "禁忌不参与六经判定")
check("INEQ5 disputed!=false",
      LATTICE["六经判定"]["disputed"] == "suspend", "disputed 为悬挂非否定")

ok = sum(1 for _, c, _ in RESULTS if c)
print("\n结果：%d/%d 通过" % (ok, len(RESULTS)))
print("⛔ 本套件为 EXECUTION-vs-SPEC；LLM 实际行为仍 NOT_TESTABLE。")
sys.exit(0 if ok == len(RESULTS) else 1)
