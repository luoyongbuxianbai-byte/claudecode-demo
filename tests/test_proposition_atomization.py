#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_proposition_atomization.py —— 命题原子化回归（126批·上级令四）

⛔ 上级令四：「**回归必须保证再把上述命题绑回去时测试变红。**」
   ⇒ 故本器备 `--rebundle` 档：**把 125批 三起错案之命题重新绑回去**，
     同一组断言**必须全红**。若 `--rebundle` 竟然绿了，说明本回归没测到点上。

三样本（上级令四指定）：
  ATOM-1  中风证型成立     ≠ 中风由外来风邪导致
  ATOM-2  「胃气」一词存在  ≠ 缓脉映射胃气恢复
  ATOM-3  脉数支持热       ≠ 脉数确认热／定位热／排除虚／直接导治疗
"""
import json
import os
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELLS = {c["cell_id"]: c for c in json.load(
    open(os.path.join(B, "rules", "pulse_cells_v0.json"), encoding="utf-8"))["cells"]}
GATES = json.load(open(os.path.join(B, "schema", "retrieval_gates_v0.json"), encoding="utf-8"))

FAIL = []


def ck(name, cond, why=""):
    print(("✅PASS " if cond else "⛔FAIL ") + name + ("" if cond else "   " + why))
    if not cond:
        FAIL.append(name)


def atom1(rebundle):
    """中风证型 与 风邪病因 须分处两 cell，且裁决相反。"""
    if rebundle:
        # 绑回去＝二者同属一 cell、同一 validation_status
        ck("ATOM-1 证型与病因须可分别裁决", False,
           "绑回后：一个 cell 同时承载『中风成立』与『中风由风邪致』，二者无法各自被反例推翻")
        return
    a = CELLS.get("PULSE-HUAN-ZHONGFENG-A", {})
    c = CELLS.get("ZHONGFENG-WINDCAUSE-C", {})
    ck("ATOM-1a 二命题分处两 cell", bool(a) and bool(c))
    ck("ATOM-1b 证型侧成立（source_verified）",
       a.get("validation_status") == "source_verified", str(a.get("validation_status")))
    ck("ATOM-1c 病因侧被否（rejected）",
       c.get("validation_status") == "rejected", str(c.get("validation_status")))
    ck("ATOM-1d ⭐二者裁决相反 ⇒ 绑在一起必然误判一方",
       a.get("validation_status") != c.get("validation_status"))


def atom2(rebundle):
    """词之存在 与 映射之存在 须分栏，不得互推。"""
    aud = CELLS.get("PULSE-HUAN-ZHONGFENG", {}).get("term_audit_125", {})
    if rebundle:
        ck("ATOM-2 词存在与映射存在须分栏", False,
           "绑回后：由 mapping 之薄推 term 之无 —— 此即 124批「胃气无源」之误")
        return
    ck("ATOM-2a 五栏俱在",
       all(k in aud for k in ("1_exact_term_hit", "2_semantic_near_match",
                              "3_mapping_hit", "4_speaker", "5_verdict")))
    ck("ATOM-2b ⭐词存在（740）与映射薄（1）并存而不互推",
       aud.get("1_exact_term_hit") == 740 and "仅 1 处" in str(aud.get("3_mapping_hit")))
    ck("ATOM-2c 裁语未把二者混为一谈",
       "term_present" in str(aud.get("5_verdict")))
    ck("ATOM-2d 映射侧另立 cell", "PULSE-HUAN-WEIQI" in CELLS)


def atom3(rebundle):
    """support 与 confirm/locate/exclude/treatment 须分别裁决。"""
    s = CELLS.get("PULSE-SHU-HEAT", {})
    cd = s.get("cannot_decide", [])
    if rebundle:
        ck("ATOM-3 support 与其余四项须分别裁决", False,
           "绑回后：`脉数→热` 一句同时承载 support/confirm/locate/exclude/treatment 五个谓词，"
           "任一被反例推翻即整句失效 —— 此即 124批 先过宽、后矫枉之根")
        return
    ck("ATOM-3a support 保留", s.get("candidate_effect") == "support"
       and s.get("compile_status") == "support_only")
    for k in ("confirm", "locate", "exclude"):
        ck("ATOM-3b 明禁 %s" % k, any(k in x for x in cd))
    ck("ATOM-3c 明禁直通治疗", any("治疗" in x for x in cd))
    ck("ATOM-3d ⭐明许 support（未被矫枉抹去）",
       any(("可**" in x or "✅" in x) and "support" in x for x in cd))


def gates(rebundle):
    g = GATES["GATE_3_proposition_atomization"]
    ck("闸三·三样本已登记", len(g["regression_samples_125"]) == 3)
    ck("闸三·明写【绑回须变红】", "变红" in g["regression_requirement"])
    ck("闸一·明禁固定字数窗", "±400" in GATES["GATE_1_context_radius"]["boundary_rule"])
    ck("闸一·边界不可定 ⇒ unknown 且不得作决定性证据",
       "不得进入决定性证据" in GATES["GATE_1_context_radius"]["unknown_rule"])
    ck("闸二·明禁由一字段推其余三", "禁止由其中一个字段推另外三个"
       in GATES["GATE_2_lexical_semantic"]["hard_rule"])
    ck("闸二·query_family 为必填", GATES["GATE_2_lexical_semantic"]["query_family_required"] is True)
    ck("闸二·四问俱全", len(GATES["GATE_2_lexical_semantic"]["four_questions"]) == 4)


def main():
    rb = "--rebundle" in sys.argv
    print("═══ 命题原子化回归（126批）%s ═══" % ("【--rebundle 档·须全红】" if rb else ""))
    atom1(rb)
    atom2(rb)
    atom3(rb)
    if not rb:
        gates(rb)
    print("\n失败 %d 项%s" % (len(FAIL), ("：" + "｜".join(FAIL)) if FAIL else ""))
    if rb:
        if len(FAIL) != 3:
            print("⛔⛔ **--rebundle 档应恰好红 3 项（三样本各一），今为 %d ⇒ 本回归没测到点上。**"
                  % len(FAIL))
            return 1
        print("✅ --rebundle 档如期红 3 项 ⇒ **绑回去即变红，回归有效**。")
        return 0
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
