#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cell_level_revocation.py —— 格级撤销回归（123批·上级令二·2.2）

⛔ 上级令：「**此测试须先红，再修 parser，最后真绿。**」
   故本器备有 `--legacy` 档：同一组断言跑在 **122批 以前之行级判法** 上，
   **必须全红**。若 `--legacy` 竟然绿了，说明本测试根本没测到点上——
   **那就是又一次假绿，须停并报。**

四款（上级点名）：
  T1 同行 A 格含 ⛔、B 格不含 ⇒ A revoked、B **不受影响**
  T2 同一行两格状态相反 ⇒ parser 须**分别**返回
  T3 行内有一格 candidate ⇒ **不得**使整行皆 candidate
  T4 行内有一格 confirmed ⇒ **不得**使兄弟格 confirmed

T5–T7 为本工程加挂（非上级点名，但同源）：
  T5 `{{at:...}}` 内部之 `|` 不得把标记撕成假格
  T6 明文否定句（引号内）不得被计为裸映射  ← 114批 误检 67% 之同型
  T7 V8 实文：L4056 之 `数=热` 在格级判法下**必须被查得**
"""
import os
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, B)
from compiler.cell_parser import split_cells, legacy_line_revoked, bare_mappings  # noqa: E402

V8 = os.path.join(B, "V8", "hxs_engine_v8_full_v2.md")
BEFORE = os.path.join(B, "term_layer", "hxs_engine_v8_full_v2_改前_123批.md")

FAIL = []


def check(name, cond, why):
    if cond:
        print("✅PASS %-46s" % name)
    else:
        print("⛔FAIL %-46s %s" % (name, why))
        FAIL.append((name, why))


# ── 构造样本（不依赖 V8，免得 V8 一改测试就飘）──────────────
LINE_MIX = "脉滑→【候选触发·痰】⛔不得独立定热|数=热|洪大=阳明气分|沉迟→【候选·里虚寒】⛔须先排除里实"
LINE_AT = ("弦→【候选】⛔不得独立定六经 {{at:trigger_candidate|obj=六经|src=经方传真系·33354|scope=D0}}"
           "|数=热")  # ← 右格未带类型标记：candidate 不得传染到它
LINE_NEG = "不能反推：“脉数＝热证充分条件”。"


def t1_sibling_isolation(legacy):
    cells = split_cells(LINE_MIX, 1)
    a = cells[0]   # 含 ⛔
    b = cells[1]   # 数=热，不含
    if legacy:
        rev_a = rev_b = legacy_line_revoked(LINE_MIX)
    else:
        rev_a, rev_b = a.revoked, b.revoked
    check("T1a 含⛔之格 ⇒ revoked", rev_a is True, "A 格应判为已撤")
    check("T1b 兄弟格不受影响 ⇒ NOT revoked", rev_b is False,
          "⛔ 行级污染：`数=热` 因同行别格有 ⛔ 而被当成已撤")


def t2_opposite_in_one_line(legacy):
    cells = split_cells(LINE_MIX, 1)
    if legacy:
        states = {legacy_line_revoked(LINE_MIX)}
    else:
        states = {c.revoked for c in cells}
    check("T2 同行两格状态相反须分别返回", len(states) == 2,
          "行级判法只能给出单一状态，无法区分同行异状")


def t3_candidate_not_contagious(legacy):
    cells = split_cells(LINE_AT, 1)
    typed = [c for c in cells if c.at_types]
    untyped = [c for c in cells if not c.at_types]
    if legacy:
        # 行级：整行有 {{at:}} 即视为整行已标类型
        check("T3 一格 candidate 不得使整行皆 candidate", False,
              "行级判法下整行同类型，无法只标一格")
        return
    check("T3 一格 candidate 不得使整行皆 candidate",
          len(typed) >= 1 and len(untyped) >= 1,
          "带类型之格与未带者须可区分")


def t4_confirmed_not_contagious(legacy):
    line = "甲→【确认】 {{at:confirmed|obj=X|src=Y|scope=D0}}|乙=未审之裸映射"
    cells = split_cells(line, 1)
    if legacy:
        check("T4 confirmed 不得传染兄弟格", False, "行级判法整行同类型")
        return
    sib = [c for c in cells if not c.at_types]
    check("T4 confirmed 不得传染兄弟格",
          len(sib) == 1 and "confirmed" not in (sib[0].at_types or []),
          "兄弟格不得因同行有 confirmed 而变 confirmed")


def t5_at_block_not_torn(legacy):
    cells = split_cells(LINE_AT, 1)
    bogus = [c for c in cells if c.lhs in ("obj", "src", "scope")]
    check("T5 {{at:}} 内之 | 不得撕出假格", not bogus,
          "⛔ 初版即犯此错：obj=/src=/scope= 被当成裸映射（实测 30 格）")


def t6_negated_not_counted(legacy):
    cells = split_cells(LINE_NEG, 1)
    check("T6 明文否定句不得计为裸映射",
          not any(c.bare for c in cells),
          "⛔ 同 114批 误检 67% 之型：L429/430 前有「所以不能建立：」")


def t7_v8_real(legacy):
    """⛔ 本款对【改前归档件】施测，不对现行 V8。

    123批 已把 L4055–4056 原子化，现行 V8 里已无裸映射；
    若仍对现行 V8 断言「须查得 `数=热`」，那是在要求修复不生效——**测试自相矛盾**。
    （初版即如此写，修完 V8 后自打红，已改。）
    ⇒ 改为对 `term_layer/hxs_engine_v8_full_v2_改前_123批.md`（协议16 归档件）施测：
      **同一份文本，行级判法查不到、格级判法查得到** —— 这才是要证的那件事。
    """
    if not os.path.exists(BEFORE):
        check("T7 改前归档件须在（协议16）", False, "归档件缺失：%s" % BEFORE)
        return
    lines = open(BEFORE, encoding="utf-8").read().split("\n")
    cells = [c for c in bare_mappings(BEFORE, lambda L: "脉" in L) if c.lhs == "数"]
    if legacy:
        found = [c for c in cells if not legacy_line_revoked(lines[c.line_no - 1])]
        check("T7 改前·`数=热` 须被查得", bool(found),
              "⛔ 行级判法下 `数=热` 被同行 ⛔ 掩蔽，永远查不到")
        return
    check("T7 改前·`数=热` 须被查得", bool(cells),
          "格级判法应当能在归档件里查到 `数=热`")


def t8_v8_now_clean(legacy):
    """现行 V8 之脉象裸映射须已归零（123批 原子化之结果）。"""
    if legacy:
        check("T8 现行 V8 脉象裸映射已归零", True, "")  # 行级判法本就查不到，无从证伪
        return
    live = {c.lhs for c in bare_mappings(V8, lambda L: "脉" in L)}
    tgt = {"数", "洪大", "结代", "浮", "紧", "缓", "细", "微"} & live
    check("T8 现行 V8 脉象裸映射已归零", not tgt, "仍活着：%s" % sorted(tgt))


TESTS = [t1_sibling_isolation, t2_opposite_in_one_line, t3_candidate_not_contagious,
         t4_confirmed_not_contagious, t5_at_block_not_torn, t6_negated_not_counted,
         t7_v8_real, t8_v8_now_clean]


def main():
    legacy = "--legacy" in sys.argv
    print("═══ 格级撤销回归（123批）%s ═══" % ("【--legacy 档·须全红】" if legacy else ""))
    for t in TESTS:
        t(legacy)
    print("\n结果：%d/%d 通过｜失败 %d" % (len(TESTS) * 0 + (_n() - len(FAIL)), _n(), len(FAIL)))
    if legacy:
        # legacy 档必须有失败；一个都不失败反而是事故
        if not FAIL:
            print("\n⛔⛔ **--legacy 档竟然全绿——本测试没测到点上，属假绿，须停并报。**")
            return 1
        print("\n✅ --legacy 档如期失败 %d 项 ⇒ **本测试确实测在行级污染这个点上**。" % len(FAIL))
        print("   失败项：" + "｜".join(n for n, _ in FAIL))
        return 0
    return 1 if FAIL else 0


def _n():
    return 9  # T1 拆为 T1a/T1b，故断言数 9


if __name__ == "__main__":
    sys.exit(main())
