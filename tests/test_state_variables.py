#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_state_variables.py —— 状态变量取值校验（124批·上级令一、二、三）

实装三条验收：
  ① ordinal 值域**变量绑定**——不得跨变量互填（`pus_maturity=mild` 须不可能）
  ② `continuous_unknown_scale` 已撤，只余 `graded_unscaled`
  ③ 无锚实例不得存在；`raw_value` 必填，normalized 不得顶替原文
"""
import json
import os
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(B, "schema", "state_value_v0.json"), encoding="utf-8"))
D = json.load(open(os.path.join(B, "rules", "state_variables_v0.json"), encoding="utf-8"))
V = {v["state_variable"]: v for v in D["variables"]}

FAIL = []


def ck(name, cond, why=""):
    print(("✅PASS " if cond else "⛔FAIL ") + name + ("" if cond else "   " + why))
    if not cond:
        FAIL.append(name)


# ── 令二：continuous_unknown_scale 须已撤 ──────────────────
enum = S["definitions"]["value_type"]["enum"]
ck("⭐令二·`continuous_unknown_scale` 已撤", "continuous_unknown_scale" not in enum)
ck("⭐令二·`graded_unscaled` 已立", "graded_unscaled" in enum)
ck("⭐令二·其定义明写【量尺性质不能由现有原文确定】",
   "量尺性质" in S["definitions"]["value_type"]["description"])

# ── 令一：值域变量绑定 ────────────────────────────────────
ck("⭐令一·schema 无全局 ordinal enum",
   "ordinal_token" not in S.get("definitions", {}),
   "全局枚举仍在 ⇒ 跨变量互填仍合法")
ck("⭐令一·allowed_values 为必填", "allowed_values" in S["required"])

# 逐变量：取值须 ∈ 自己的 allowed_values
for name, v in V.items():
    allowed = set(v["allowed_values"])
    bad = [o for o in v.get("observations", [])
           if o.get("normalized_value") and o["normalized_value"] not in allowed]
    ck("值域绑定 %s" % name, not bad,
       "越域取值：%s" % [o.get("normalized_value") for o in bad])

# ⭐ 关键：不同变量之值域须互不相交（否则「绑定」形同虚设）
names = list(V)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = set(V[names[i]]["allowed_values"]), set(V[names[j]]["allowed_values"])
        ck("⭐值域互不相交 %s ∩ %s" % (names[i], names[j]), not (a & b), str(a & b))

# ── 令三：无锚实例不得存在 ────────────────────────────────
ck("⭐令三·「疼痛程度」占位实例已删",
   not any("疼痛" in n for n in V),
   "无锚之医学变量仍在 evidence registry 中")

for name, v in V.items():
    ck("有锚 %s" % name, bool(v.get("source_refs")))
    bad = [o for o in v.get("observations", []) if not o.get("raw_value")]
    ck("⭐raw_value 必填 %s" % name, not bad, "normalized 顶替了原文")
    # 序关系每条须各自有锚
    bad = [r for r in v.get("ordering_relation", []) if not r.get("source_ref")]
    ck("序关系逐条有锚 %s" % name, not bad)
    # graded_unscaled 者不得填序
    if v["value_type"] == "graded_unscaled":
        ck("graded_unscaled 不得填序 %s" % name, not v.get("ordering_relation"))
    ck("numeric_scale_forbidden 恒真 %s" % name,
       v.get("numeric_scale_forbidden") is True)
    # ⛔ 不得出现数值量表
    bad = [o for o in v.get("observations", [])
           if any(ch.isdigit() for ch in str(o.get("normalized_value") or ""))]
    ck("⛔无编造数值 %s" % name, not bad)

# ── 三值 pus_maturity（反例攻击所得）───────────────────────
pm = V.get("pus_maturity", {})
ck("⭐`pus_maturity` 已由二值改三值（124批 反例攻击所得）",
   len(pm.get("allowed_values", [])) == 3,
   "仍为 %s" % pm.get("allowed_values"))
ck("⭐其中间档有胡老逐字锚",
   any("没全化脓" in r.get("source_ref", "") for r in pm.get("ordering_relation", [])))

print("\n失败 %d 项%s" % (len(FAIL), ("：" + "｜".join(FAIL)) if FAIL else ""))
sys.exit(1 if FAIL else 0)
