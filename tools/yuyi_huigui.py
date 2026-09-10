#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yuyi_huigui.py —— 最小语义回归测试（118批·用户令十）

用户令：「『引擎没有测试套件可跑』不是继续无测试修改的理由。
        下一批同时建立最小的语义回归测试，**不需要病例金标准**。」

⛔⛔ **本器测的是【引擎文本之语义约束】，不是【执行器之行为】。**
   引擎是一份 Markdown 规则文本，没有可执行体；**故本器能测的只有：
   「该说的话在不在、该撤的话撤没撤、二者有没有同时在场」。**
   **它不能证明 LLM 执行时真的照做了。** 这个界限不可含糊——
   与 `case_flow.py` 之「可达性检验 ≠ 推理正确性检验」同型。

四类（用户令十）：
  A 反例单元：少阴＋发热恶寒＋脉沉，不得因「发热恶寒」被强制覆盖成太阳
  B 未知    ：unknown ≠ absent ≠ false
  C 候选传播：candidate_trigger 不得被下游读为 confirmed
  D 并存    ：人虚＋病实 须允许同时存在

用法：
    python3 tools/yuyi_huigui.py          # 跑全部
    python3 tools/yuyi_huigui.py -v       # 打印命中行
"""
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(B, "V8", "hxs_engine_v8_full_v2.md")
EXEC_SEG = {"00_执行件", "01_概念定义层", "02_观察判据层"}

# (类, 名, 种类, 正则, 期望)
#   kind="must"    该模式必须存在（否则约束缺失）
#   kind="mustnot" 该模式必须不存在【于未带撤销标记之行】（否则旧语义仍在）
REVOKED = re.compile(r"11[78]批(撤|收窄|改|降|加注)|作废原文|已撤|勘误|R11勘误|不得|禁止|⛔")

TESTS = [
 ("A", "A1 发热恶寒不得独定表阳",
  "mustnot", r"发热恶寒[^。\n]{0,8}→\s*表阳(?![^。\n]{0,20}脉浮)",
  "无限定之「发热恶寒→表阳」不得存在于执行层"),
 ("A", "A2 少阴反发热之反证须在场",
  "must", r"少阴[^。\n]{0,10}反发热|反发热[^。\n]{0,10}脉沉",
  "§301「少阴病始得之，反发热，脉沉者」须可检得"),
 ("A", "A3 脉沉不得独定里位",
  "mustnot", r"沉=里",
  "「沉=里」之裸断言不得存在"),
 ("A", "A4 脉滑不得独定热",
  "mustnot", r"滑=痰食热",
  "「滑=痰食热」之裸断言不得存在"),
 ("A", "A5 弦不得独定少阳",
  "mustnot", r"弦=少阳",
  "「弦=少阳」之裸断言不得存在"),

 ("B", "B1 未提及不得推为阴性",
  "mustnot", r"未提及\s*[=＝]\s*阴性推定(?![^。\n]{0,30}(已撤|作废|勘误))",
  "「未提及=阴性推定」不得作为现行条款"),
 ("B", "B2 未采≠阴性之条须在场",
  "must", r"未采\s*[≠不]|未采集?→未知|未提及→\*{0,2}默认未知",
  "三值语义须明文在场"),
 ("B", "B3 未知须触发补采而非否决",
  "must", r"(悬挂|补采|决定性观察清单|待采)",
  "未知之处置须是悬挂/补采，不是排除"),

 ("C", "C1 候选词法须已写入",
  "must", r"候选触发|【候选",
  "117批 之候选措辞须在场"),
 ("C", "C2 ⛔候选与确认须有类型区分",
  "must", r"\{\{at:(trigger_candidate|supporting_evidence|confirmed|exclusion|contraindication|unknown|disputed)\b",
  "⭐119批：引擎已植入机器可解析之 {{at:...}} 类型标记（docs/ASSERTION_TYPE_SPEC.md）"),

 ("D", "D1 人虚与病实须可并存",
  "must", r"虚指人虚[，,]实指病实|正虚病实|人虚[^。\n]{0,10}病实",
  "胡老「虚指人虚，实指病实」须在场"),
 ("D", "D2 正虚不得否决实纲",
  "mustnot", r"须\*{0,2}无正虚征象压倒性在场(?![^。\n]{0,40}已撤)",
  "「实纲须无正虚在场」不得作为现行必要条件"),
 ("D", "D3 阴阳不得由虚实单轴定",
  "mustnot", r"正气盛\s*[=＝]\s*阳[/／]正气虚\s*[=＝]\s*阴(?![^。\n]{0,30}(勘误|已撤))",
  "R11 已撤，须不复现"),
 ("D", "D4 阴阳＝f(寒热) 须已撤",
  "mustnot", r"阴阳\s*[＝=]\s*f\(寒热\)(?![^。\n]{0,60}(已撤|撤销|作废))",
  "117批 已撤，须不复现"),
 ("D", "D5 寒⇒阴/热⇒阳单向须保留",
  "must", r"寒者必阴[，,]?热者必阳|寒⇒阴|热⇒阳",
  "撤函数之后，单向关系须仍在"),
]


def seg_of(L, i):
    for k in range(i, -1, -1):
        m = re.match(r"^# (\d\d_\S+)", L[k])
        if m:
            return m.group(1)
    return "?"


def main():
    verbose = "-v" in sys.argv
    L = open(V8, encoding="utf-8").read().split("\n")
    segs = [seg_of(L, i) for i in range(len(L))]
    print("═══ 最小语义回归测试（118批·用户令十）═══")
    print("⛔ 本器测【引擎文本之语义约束】，**不测执行器行为**。")
    print("   引擎无可执行体；本器只能答「该说的在不在、该撤的撤没撤」，")
    print("   **不能证明 LLM 执行时照做了**。\n")
    passed = failed = 0
    fails = []
    for cls, name, kind, pat, why in TESTS:
        rex = re.compile(pat)
        hits = [(i + 1, segs[i], L[i].strip()) for i in range(len(L)) if rex.search(L[i])]
        if kind == "mustnot":
            live = [h for h in hits if not REVOKED.search(h[2])]
            ok = not live
            shown = live
        else:
            ok = bool(hits)
            shown = hits
        tag = "✅PASS" if ok else "⛔FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
            fails.append((cls, name, why, shown))
        print("%s [%s] %-28s %s（命中 %d）" % (tag, cls, name, why[:34], len(shown)))
        if verbose and shown:
            for ln, sg, tx in shown[:3]:
                print("        L%-6d [%s] %s" % (ln, sg[:12], tx[:88]))
    print("\n结果：%d/%d 通过｜⛔ 失败 %d" % (passed, len(TESTS), failed))
    if fails:
        print("\n⛔ 失败项：")
        for cls, name, why, shown in fails:
            print("  [%s] %s —— %s" % (cls, name, why))
            for ln, sg, tx in shown[:2]:
                print("        L%-6d [%s] %s" % (ln, sg[:12], tx[:84]))
    # ⛔⛔118批 自查：C2 初版以 `\[C\]|\[A\]` 为式，被 L15953「[他人C]层」「[A]层」
    #   （证据分级标记，与候选/确认无关）误命中而**假绿**。
    #   **一个因错误理由而通过的测试，比没有测试更坏**——它会让人以为缺口已补。
    #   已改为只认 `[候选]/[确认]/type:candidate` 等真类型记号。
    print("\n⚠ **C2 应为红**：它就是为暴露「引擎无候选/确认类型区分」而设，"
          "\n   与 `tools/chuanbo_shenji.py` 第三节同一结论。**C2 转绿之日，"
          "\n   才是 117批 P0 修复真正闭环之日。**")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
