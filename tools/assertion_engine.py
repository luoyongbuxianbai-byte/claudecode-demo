#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assertion_engine.py —— 断言类型之【参考解析器】（119批·用户令一）

⛔⛔ **界限声明（不可略，写在最前）**：
   本器实现的是 `docs/ASSERTION_TYPE_SPEC.md` 之传播格，
   **它测的是【本规范之实现】，不是【LLM 读引擎时的实际行为】。**
   后者在本工程现有条件下 **NOT_TESTABLE**——引擎是 Markdown，无可执行体。
   ⇒ **不得把本器通过写成「执行语义已验证」。**
   （与 `case_flow.py`「可达性 ≠ 推理正确性」、`yuyi_huigui.py`「文本语义 ≠ 执行语义」同一条界限。）

本器提供两件事：
  ① 解析 V8 执行层之 `{{at:type|obj=..|src=..|scope=..}}` 标记 → 得 token→assertion_type 表；
  ② 按规范之传播格，对「只含某 token、其余全 unknown」之输入求解，
     回答 T1–T10 之验收问题（can_confirm / can_exclude / can_gate / final_confirmed_count）。
"""
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(B, "V8", "hxs_engine_v8_full_v2.md")

TYPES = ("trigger_candidate", "supporting_evidence", "confirmed",
         "exclusion", "contraindication", "unknown", "disputed")

OBS_STATES = ("present", "absent_explicit", "unknown_not_asked",
              "unknown_not_recorded", "uncertain")

# ⛔ 规范第四节：只有 absent_explicit 可作缺失证据、可触发排除
CAN_BE_MISSING_EVIDENCE = {"absent_explicit"}
CAN_TRIGGER_EXCLUSION = {"absent_explicit"}

# ⛔ 规范第五节之传播格：每层对各类型之动作，三者不得走同一分支
LATTICE = {
    #                      candidate  support  confirmed  unknown
    "候选生成":  {"trigger_candidate": "gen_low", "supporting_evidence": "gen_mid",
                "confirmed": "gen_high", "unknown": "hold", "disputed": "gen_both",
                "exclusion": "none", "contraindication": "none"},
    "证据累计":  {"trigger_candidate": "partial", "supporting_evidence": "partial",
                "confirmed": "full", "unknown": "noop", "disputed": "noop",
                "exclusion": "neg", "contraindication": "none"},
    "竞争排除":  {"trigger_candidate": "forbidden", "supporting_evidence": "forbidden",
                "confirmed": "allowed", "unknown": "forbidden", "disputed": "forbidden",
                "exclusion": "allowed", "contraindication": "forbidden"},
    "六经判定":  {"trigger_candidate": "forbidden", "supporting_evidence": "forbidden",
                "confirmed": "allowed", "unknown": "suspend", "disputed": "suspend",
                "exclusion": "none", "contraindication": "none"},
    "寒热虚实":  {"trigger_candidate": "forbidden", "supporting_evidence": "forbidden",
                "confirmed": "allowed", "unknown": "undetermined", "disputed": "suspend",
                "exclusion": "none", "contraindication": "none"},
    "方证硬门":  {"trigger_candidate": "forbidden", "supporting_evidence": "forbidden",
                "confirmed": "allowed", "unknown": "forbidden", "disputed": "forbidden",
                "exclusion": "none", "contraindication": "block"},
    "打分":     {"trigger_candidate": "w_low", "supporting_evidence": "w_mid",
                "confirmed": "w_high", "unknown": "w_zero", "disputed": "w_zero",
                "exclusion": "w_neg", "contraindication": "w_zero"},
    "禁忌":     {"trigger_candidate": "forbidden", "supporting_evidence": "forbidden",
                "confirmed": "allowed", "unknown": "forbidden", "disputed": "forbidden",
                "exclusion": "none", "contraindication": "allowed"},
}

MARK = re.compile(r"\{\{at:(?P<t>[a-z_]+)"
                  r"(?:\|obj=(?P<obj>[^|}]*))?"
                  r"(?:\|src=(?P<src>[^|}]*))?"
                  r"(?:\|scope=(?P<scope>[^|}]*))?\}\}")


def parse(path=V8):
    """扫引擎，得 [(行, 类型, obj, src, scope, 原行)]；并报语法错"""
    L = open(path, encoding="utf-8").read().split("\n")
    out, bad = [], []
    for i, ln in enumerate(L):
        for m in MARK.finditer(ln):
            t = m.group("t")
            rec = (i + 1, t, m.group("obj") or "", m.group("src") or "",
                   m.group("scope") or "", ln.strip())
            if t not in TYPES:
                bad.append(rec)
            else:
                out.append(rec)
        # 语法错：写了 {{at 但不合式
        if "{{at" in ln and not MARK.search(ln):
            bad.append((i + 1, "SYNTAX", "", "", "", ln.strip()))
    return out, bad


class Resolver:
    """规范之传播格参考实现。⛔只解规范，不解 LLM。"""

    def __init__(self, marks=None):
        self.marks = marks if marks is not None else parse()[0]
        # token（由 obj 与行文推出）→ 类型
        self.by_line = {r[0]: r for r in self.marks}

    def resolve(self, inputs):
        """inputs: [(token, assertion_type, observation_state)]
        其余一律视为 unknown_not_asked。
        返回 dict：confirmed / excluded / gated / scored / candidates / to_ask
        """
        st = {"confirmed": [], "excluded": [], "gated": [], "candidates": [],
              "to_ask": [], "score": 0, "notes": []}
        # 分离有效输入
        actives = [(tok, at, obs) for tok, at, obs in inputs
                   if obs == "present" or obs == "absent_explicit"]
        unknowns = [(tok, at, obs) for tok, at, obs in inputs
                    if obs not in ("present", "absent_explicit")]
        for tok, at, obs in unknowns:
            st["to_ask"].append(tok)
            # ⛔ unknown 不加不减、不排除
            st["notes"].append("%s: %s → 悬挂，不参与排除/打分" % (tok, obs))

        n_conf_inputs = sum(1 for _, at, _ in actives if at == "confirmed")
        n_supp = sum(1 for _, at, _ in actives if at == "supporting_evidence")

        for tok, at, obs in actives:
            act_gen = LATTICE["候选生成"].get(at, "none")
            if act_gen.startswith("gen"):
                st["candidates"].append(tok)
            # 六经/寒热虚实：只有 confirmed 可定
            if LATTICE["六经判定"].get(at) == "allowed":
                st["confirmed"].append(tok)
            # 排除
            if LATTICE["竞争排除"].get(at) == "allowed":
                # ⛔ exclusion 须来自独立阳性证据；absence 不构成 exclusion
                if at == "exclusion" and obs != "absent_explicit":
                    st["notes"].append("%s: exclusion 须 absent_explicit，此处不成立" % tok)
                else:
                    st["excluded"].append(tok)
            # 方证硬门
            if LATTICE["方证硬门"].get(at) == "allowed":
                st["gated"].append(tok)
            # 打分
            st["score"] += {"w_low": 1, "w_mid": 3, "w_high": 9,
                            "w_zero": 0, "w_neg": -3}.get(LATTICE["打分"].get(at, "w_zero"), 0)

        # ⭐ 组合规则（规范第三节「单独」之定义）：
        #   若无 confirmed 且 supporting_evidence < 2，则不得产生任何 final confirmed
        if n_conf_inputs == 0 and n_supp < 2:
            if st["confirmed"]:
                st["notes"].append("⛔违规：无 confirmed 输入而产生了 confirmed 输出")
            st["confirmed"] = []
            st["gated"] = []
        st["final_confirmed_count"] = len(st["confirmed"])
        st["exclusion_count"] = len(st["excluded"])
        return st


def main():
    marks, bad = parse()
    print("═══ assertion_type 参考解析器（119批）═══")
    print("⛔ 本器只解【规范】，不解【LLM 行为】；后者 NOT_TESTABLE。\n")
    print("引擎内合式标记：%d 处" % len(marks))
    from collections import Counter
    c = Counter(r[1] for r in marks)
    for k, v in c.most_common():
        print("   %-22s %d" % (k, v))
    if bad:
        print("\n⛔ 语法错 %d 处：" % len(bad))
        for r in bad[:5]:
            print("   L%-6d %s" % (r[0], r[5][:90]))
        return 1
    # 无锚而标 confirmed 者
    noanchor = [r for r in marks if r[1] == "confirmed" and not r[3]]
    if noanchor:
        print("\n⛔ 标 confirmed 而无 src 锚者 %d 处（规范第二节禁）：" % len(noanchor))
        for r in noanchor[:5]:
            print("   L%d" % r[0])
        return 1
    print("\n✅ 语法与锚检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
