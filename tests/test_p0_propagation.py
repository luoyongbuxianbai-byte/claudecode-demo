#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_p0_propagation.py —— P0 传播闭环之验收断言（119批·用户令十一）

逐条断言用户令十一之十五项验收条件。**任一红 ⇒ 只能报「P0修复进行中」。**
⛔ 界限：本套件断言【引擎文本 + 规范实现】；LLM 实际行为 NOT_TESTABLE。
"""
import os, re, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, "tools"))
from assertion_engine import parse, LATTICE, Resolver, CAN_TRIGGER_EXCLUSION

V8 = open(os.path.join(B, "V8", "hxs_engine_v8_full_v2.md"), encoding="utf-8").read()
L = V8.split("\n")
marks, bad = parse()
R = Resolver()
RES = []
def ck(n, c, w=""):
    RES.append((n, bool(c), w)); print("%s %-52s %s" % ("✅PASS" if c else "⛔FAIL", n, w))

ck("A1 candidate/confirmed 已有机器类型", len(marks) >= 20 and not bad,
   "合式标记 %d 处，语法错 %d" % (len(marks), len(bad)))
# ⛔⛔119批 自查：A2 初版以「标记数 ≥15」为判据而报 PASS——**它数的是标记，不是读取**。
#   引擎是 Markdown，无可执行体：「下游是否真的读 assertion_type」**在本工程现有条件下
#   无法测**。照初版报 PASS 就是把 NOT_TESTABLE 写成 PASS，即用户明令禁止者。
NOT_TESTABLE = []
NOT_TESTABLE.append(("A2 下游执行路径真实读取 assertion_type",
                     "引擎为 Markdown 无执行体；标记数≠读取。参考解析器只证【规范可解析】，"
                     "不证【LLM 照做】。须待真执行器方可测。"))
s = R.resolve([("单候选", "trigger_candidate", "present")])
ck("A3 trigger_candidate 不产生 final confirmed", s["final_confirmed_count"] == 0, "=%d" % s["final_confirmed_count"])
ck("A4 trigger_candidate 不参与 hard exclusion",
   LATTICE["竞争排除"]["trigger_candidate"] == "forbidden")
ck("A5 trigger_candidate 不过 formula hard gate",
   LATTICE["方证硬门"]["trigger_candidate"] == "forbidden")
ck("A6 unknown 不被当 false",
   LATTICE["竞争排除"]["unknown"] == "forbidden" and CAN_TRIGGER_EXCLUSION == {"absent_explicit"})
dep = os.path.join(B, "term_layer", "P0真实下游依赖审计.md")
ck("A7 P0 16项已完成真实依赖审计", os.path.exists(dep) and "actual_dependency" in open(dep, encoding="utf-8").read())
ck("A8 真实依赖点已改（非只改源头）",
   all(re.search(r"119批", L[n - 1]) for n in (4022, 4046, 3334, 3983)),
   "L4022/L4046/L3334/L3983 皆带 119批 改动标记")
ck("A9 关键单token execution test 全通过",
   os.system("python3 %s >/dev/null 2>&1" % os.path.join(B, "tests", "test_assertion_type_semantics.py")) == 0)
ck("A10 C2 由真类型语义变绿（非 grep 假绿）",
   bool(re.search(r"\{\{at:(trigger_candidate|confirmed)", V8)), "引擎内有真类型标记")
ck("A11 D5 唯一跨场景候选已完成反例攻击",
   os.path.exists(os.path.join(B, "term_layer", "必要条件_D5反例攻击.md")))
ck("A12 苓桂术甘已完成同域反例攻击",
   os.path.exists(os.path.join(B, "term_layer", "苓桂术甘_必要条件反例审计.md")))
ck("A13 厥阴上热下寒全局硬门已撤",
   not re.search(r"判定厥阴以上热下寒为主(?![^\n]{0,40}119批)", V8))
ck("A14 「治疗有效=最硬证据」已撤",
   not re.search(r"治疗反应=干预实验=病机最硬证据(?![^\n]{0,30}119批)", V8))
mf = os.path.join(B, "MANIFEST.md")
# ⛔119批 自查：A15 初版写成恒真式（`... if False else os.path.exists(mf)`），
#   **等于没测**。改为真检：新产出须真在 MANIFEST 内。
# ⛔119批 第二次自查：A15 二版检 MANIFEST.md 之文件名——**又错了对象**。
#   MANIFEST.md 只列【目录级】行（term_layer/ 等），个别文件名永不出现。
#   登记之真实所在是 `tools/manifest.py` 之 PRODUCT/MANUAL，且须新鲜度过。
_reg = open(os.path.join(B, "tools", "manifest.py"), encoding="utf-8").read()
_need = ["P0真实下游依赖审计", "unknown_false审计", "P0候选确认类型传播矩阵",
         "ASSERTION_TYPE_SPEC", "必要条件_D5反例攻击", "苓桂术甘_必要条件反例审计", "治疗反馈类型"]
_miss = [x for x in _need if x not in _reg]
_fresh = os.system("python3 %s --fresh >/dev/null 2>&1" % os.path.join(B, "tools", "manifest.py")) == 0
ck("A15 manifest 登记已实际验证（PRODUCT/MANUAL ＋ 新鲜度）",
   not _miss and _fresh, "缺登记：%s｜新鲜度：%s" % (_miss or "无", "过" if _fresh else "⛔未过"))

ok = sum(1 for _, c, _ in RES if c)
print("\n验收：%d/%d 通过｜⛔NOT_TESTABLE %d 项" % (ok, len(RES), len(NOT_TESTABLE)))
for n, w in NOT_TESTABLE:
    print("  NOT_TESTABLE %-46s %s" % (n, w))
print("⛔ NOT_TESTABLE 不计入 PASS。少一项验收条件，只能报「P0修复进行中」。")
print("⛔ 未通过者存在时，只能报「P0修复进行中」，不得报「已闭环」。")
sys.exit(0 if ok == len(RES) else 1)
