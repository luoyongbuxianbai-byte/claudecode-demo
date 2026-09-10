#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""unknown_shenji.py —— unknown ≠ false 之执行审计（119批·用户令四）

用户令：「不要只搜『未提及=阴性』这句话有没有删掉。要实际追
        missing / unknown / not_asked / not_recorded / explicit_absent
        五者是否在执行层被区分。」
"""
import os, re, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(B, "V8", "hxs_engine_v8_full_v2.md")
OUT = os.path.join(B, "term_layer", "unknown_false审计.md")
EXEC = {"00_执行件", "01_概念定义层", "02_观察判据层"}
REVOKED = re.compile(r"11[789]批|作废原文|已撤|勘误|R11勘误")
# ⛔119批 自查：DANGER 初版 11 命中，人读后 10 处是【正确条款】被误检——
#   「未采 **≠** 阴性」「**不得**充当反义」等，因行内同时含「未采」与「反义」而中式。
#   **危险模式必须排除否定/禁止语，否则会逼人去改一批本来对的条款。**
#   （与 117批 KEPT 标记、114批「机械命中不得充作冲突数」同型。）
NEGATED = re.compile(r"不得|≠|不等于|非阴性|勿|禁止|不可|只作提示|不作否决|不能")

# 五态在引擎中之对应写法
STATE = [
 ("present",              r"明确记载「?有|见有|★在场|阳性事实"),
 ("absent_explicit",      r"明确记[载录]\s*[「\"]?无|显性阴性|明确记载「无|记载「无X"),
 ("unknown_not_asked",    r"未采|未问|问诊模式下未"),
 ("unknown_not_recorded", r"未提及|未载|未记[载录]|回顾模式下未"),
 ("uncertain",            r"含糊|前后矛盾|记录矛盾|冲突事实|存疑"),
]
# 危险模式：把非 absent_explicit 之态用于排除
DANGER = [
 ("未采→排除",   r"未采[^。\n]{0,20}(排除|否决|反义|出局)"),
 ("未提及→排除", r"未提及[^。\n]{0,20}(排除|否决|反义|出局)"),
 ("未知→假",     r"未知[^。\n]{0,10}[=＝][^。\n]{0,6}(假|否|无|false)"),
 ("缺省→阴性",   r"缺省[^。\n]{0,10}(阴性|为无|为假)"),
 ("无记载即无",   r"无记载[^。\n]{0,8}即[^。\n]{0,6}无|不记载[^。\n]{0,8}为无"),
]

def seg_of(L, i):
    for k in range(i, -1, -1):
        m = re.match(r"^# (\d\d_\S+)", L[k])
        if m: return m.group(1)
    return "?"

def main():
    L = open(V8, encoding="utf-8").read().split("\n")
    segs = [seg_of(L, i) for i in range(len(L))]
    O = ["# unknown ≠ false · 执行审计（119批·用户令四）", "",
         "⛔ **不是搜「未提及=阴性」删没删，是追五态在执行层是否被【区分】。**", "",
         "## 一、五态在引擎中之覆盖", "",
         "| 观察状态 | 引擎内命中行 | 其中在执行层 | 判 |", "|---|---:|---:|---|"]
    cov = {}
    for name, pat in STATE:
        h = [(i + 1, segs[i]) for i, l in enumerate(L) if re.search(pat, l)]
        ex = [x for x in h if x[1] in EXEC]
        cov[name] = (len(h), len(ex))
        v = "✅有" if ex else ("⚠仅记录层" if h else "⛔**引擎内无此态**")
        O.append("| `%s` | %d | %d | %s |" % (name, len(h), len(ex), v))
    missing = [k for k, (a, b) in cov.items() if b == 0]
    O += ["", "⛔ **执行层未覆盖之态：%s**" % ("、".join("`%s`" % m for m in missing) if missing else "无"),
          "⇒ **未覆盖者即『引擎分不出这一态』，其行为必回落到某个默认分支——"
          "这正是 unknown 被当 false 的入口。**", "",
          "## 二、危险模式扫描（非 absent_explicit 之态用于排除）", "",
          "| 模式 | 命中 | 其中未带撤销标记 | 判 |", "|---|---:|---:|---|"]
    bad_tot = 0
    details = []
    for name, pat in DANGER:
        h = [(i + 1, segs[i], L[i].strip()) for i, l in enumerate(L) if re.search(pat, l)]
        live = [x for x in h if not REVOKED.search(x[2]) and not NEGATED.search(x[2])]
        bad_tot += len(live)
        O.append("| %s | %d | **%d** | %s |" % (name, len(h), len(live),
                                                "⛔**仍在**" if live else "✅已清"))
        if live: details.append((name, live))
    # ⭐人读裁定（工具不得覆盖）——机械命中永不得充作待改数
    READ = {13260: "⛔误检·叙述句（「本案信息量最高的一个未采项」）",
            14026: "⛔误检·此行恰恰是在说「**非**未采」",
            18903: "⛔误检·此为已撤之 L18904 之引导行，本身不含规则"}
    O += ["", "⇒ 机械命中仍在者 %d 处；**逐条人读后：真危险 %d 处。**"
          % (bad_tot, sum(1 for _, live in details for ln, _, _ in live if ln not in READ)),
          "⚠ **初版 11 命中中 10 处为误检**——「未采 **≠** 阴性」「**不得**充当反义」等"
          "**正确条款**因行内同含「未采」与「反义」而中式。已加 `NEGATED` 排除否定语。",
          "⇒ ⭐ **若照机械数去改，会把一批本来写对的条款改坏。**"
          "（与 117批 `KEPT` 标记、114批「机械命中不得充作冲突数」同型。）", ""]
    for name, live in details:
        O += ["### ⛔ %s" % name, ""]
        for ln, sg, tx in live[:4]:
            O.append("- L%d `%s`：`%s`　**人读：%s**"
                     % (ln, sg, tx.replace("|", "｜")[:96], READ.get(ln, "⛔**待人读**")))
        O.append("")
    O += ["## 三、规范侧之实装", "",
          "五态与其权限已实装于 `tools/assertion_engine.py`：", "",
          "```python",
          "OBS_STATES = ('present','absent_explicit','unknown_not_asked',",
          "              'unknown_not_recorded','uncertain')",
          "CAN_BE_MISSING_EVIDENCE = {'absent_explicit'}   # ⛔唯一",
          "CAN_TRIGGER_EXCLUSION   = {'absent_explicit'}   # ⛔唯一",
          "```", "",
          "回归测试 `tests/test_unknown_semantics.py` 断言 U1–U7，含：",
          "`not_asked`／`not_recorded` 不触发排除｜`uncertain` 非缺失证据｜",
          "`unknown` 不影响打分｜`unknown` 入补采清单。", "",
          "⛔⛔ **但须分清两件事**：",
          "- **规范侧**：五态齐备、权限锁死 → `STATIC_PASS`",
          "- **引擎侧**：执行层是否真的分得出五态 → **见第一节，%s**"
          % ("⛔尚有 %d 态未覆盖" % len(missing) if missing else "五态皆有覆盖"),
          "- **LLM 侧**：读引擎时是否照做 → **NOT_TESTABLE**", ""]
    txt = "\n".join(O)
    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write(txt)
        print("已写入 %s" % OUT)
    print("执行层未覆盖之态：%s｜危险模式仍在 %d 处" % (missing or "无", bad_tot))
    return 0

if __name__ == "__main__":
    sys.exit(main())
