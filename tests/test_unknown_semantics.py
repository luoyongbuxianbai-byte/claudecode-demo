#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_unknown_semantics.py —— unknown ≠ false 之五态回归（119批·用户令四）

用户令：「不要只搜『未提及=阴性』这句话有没有删掉。要实际追
        missing / unknown / not_asked / not_recorded / explicit_absent 五者
        是否在执行层被区分。」
⛔ 界限同 T 套件：测规范之实现，非 LLM 行为。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from assertion_engine import (Resolver, OBS_STATES, CAN_BE_MISSING_EVIDENCE,
                              CAN_TRIGGER_EXCLUSION)

R = Resolver()
RES = []
def check(n, c, w):
    RES.append((n, bool(c), w)); print("%s %-40s %s" % ("✅PASS" if c else "⛔FAIL", n, w))

# U1 五态齐备且互异
check("U1 五态齐备", len(set(OBS_STATES)) == 5, "OBS_STATES=%s" % (OBS_STATES,))

# U2 unknown_not_asked 不得触发排除
s = R.resolve([("恶寒", "exclusion", "unknown_not_asked")])
check("U2 not_asked 不触发排除", s["exclusion_count"] == 0, "=%d" % s["exclusion_count"])

# U3 unknown_not_recorded 不得触发排除
s = R.resolve([("恶寒", "exclusion", "unknown_not_recorded")])
check("U3 not_recorded 不触发排除", s["exclusion_count"] == 0, "=%d" % s["exclusion_count"])

# U4 uncertain 不得当 absent
check("U4 uncertain 非缺失证据", "uncertain" not in CAN_BE_MISSING_EVIDENCE,
      "CAN_BE_MISSING_EVIDENCE=%s" % (CAN_BE_MISSING_EVIDENCE,))

# U5 只有 absent_explicit 可作缺失证据 / 可触发排除
check("U5a 唯 absent_explicit 可作缺失证据",
      CAN_BE_MISSING_EVIDENCE == {"absent_explicit"}, "=%s" % (CAN_BE_MISSING_EVIDENCE,))
check("U5b 唯 absent_explicit 可触发排除",
      CAN_TRIGGER_EXCLUSION == {"absent_explicit"}, "=%s" % (CAN_TRIGGER_EXCLUSION,))
s = R.resolve([("明确无恶寒", "exclusion", "absent_explicit")])
check("U5c absent_explicit 确可排除", s["exclusion_count"] == 1, "=%d" % s["exclusion_count"])

# U6 unknown 不加不减分
s0 = R.resolve([("x", "trigger_candidate", "present")])
s1 = R.resolve([("x", "trigger_candidate", "present"), ("y", "trigger_candidate", "unknown_not_asked")])
check("U6 unknown 不影响打分", s0["score"] == s1["score"], "%d == %d" % (s0["score"], s1["score"]))

# U7 unknown 入补采清单
check("U7 unknown 入补采清单", "y" in s1["to_ask"], "to_ask=%s" % s1["to_ask"])

ok = sum(1 for _, c, _ in RES if c)
print("\n结果：%d/%d 通过" % (ok, len(RES)))
sys.exit(0 if ok == len(RES) else 1)
