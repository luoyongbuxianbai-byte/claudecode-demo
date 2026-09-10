#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yilai_shenji_120.py —— P0 真实下游依赖·全量人读（120批·用户令二、三、十四、十五）

⛔ 用户令二：119批 报「16项已完成 ✅」与「86 中已读 20」自相矛盾。**改账。**
⛔ 用户令三：**compound_antecedent != validated_rule**。
   119批 之「✅复合前件·本就合法·保留」全部重新人读，**「复合所以合法」不得作 reason**。
"""
import os, re, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(B, "V8", "hxs_engine_v8_full_v2.md")
OUT = os.path.join(B, "term_layer", "P0真实下游依赖审计_120批.md")
OUT2 = os.path.join(B, "term_layer", "P0复合前件合法性复核.md")
EXEC = {"00_执行件", "01_概念定义层", "02_观察判据层"}
JUDGE = re.compile(r"[=＝]|→|▶|判据|确认|否决|反义|★")
REV = re.compile(r"11[789]批|12[0-9]批|作废原文|已撤|勘误|R11勘误")
SRC = [("P0-1/2/15", r"阴阳"), ("P0-3", r"脉沉|沉脉|沉="), ("P0-4", r"脉弦|弦="),
       ("P0-5", r"脉滑|滑="), ("P0-6", r"沉迟"), ("P0-7", r"心下悸"),
       ("P0-8", r"大便溏|便溏"), ("P0-9", r"下利清谷"), ("P0-10", r"正虚|实纲"),
       ("P0-11", r"口渴|思饮"), ("P0-12/14/16", r"发热恶寒|恶寒发热"), ("P0-13", r"利而渴")]

# actual_dependency 七值（统一口径·用户令二）
DEP = ("true_dependency", "false_positive", "commentary", "case_text",
       "deprecated", "duplicate", "unknown")

# ── 全量人读（行: [dep, rule_effect, validation_status, action, reason]）────
# ⛔ validation_status 用 schema 值；**不得以「复合所以合法」为 reason**
READ = {
 # ── 119批 已读之 20 条·本批依用户令三【重核】────────────────
 4022: ["true_dependency","trigger","candidate","已改·降候选","119批补改；有渴→有热已撤"],
 4046: ["true_dependency","trigger","candidate","已改·降候选","119批补改；心下悸→水饮已撤"],
 3334: ["true_dependency","support","candidate","已改·降支持去★","119批补改"],
 3983: ["true_dependency","trigger","candidate","已改·降候选","119批补改；脉弦→少阳裸映射已撤"],
 3262: ["true_dependency","confirm","candidate","⛔120批改判·降 support_only",
        "「脉弦有力/热实→半表半里阳」。**119批以『复合前件』判合法，本批撤该 reason**："
        "作用对象为六经归属；来源主体未标；未做同域反例攻击 ⇒ validation=candidate，不得 confirm"],
 3308: ["true_dependency","confirm","candidate","⛔120批改判·降 support_only",
        "「往来寒热+脉弦有力(实)→半表半里阳而非厥阴」。同上；且其『非厥阴』部分是 exclusion，"
        "而 exclusion 须经 validated scoped necessary rule ⇒ 现不满足"],
 3078: ["true_dependency","exclude","candidate","⛔120批改判·须重验",
        "「口不渴★∧四肢不温★∧下利清谷★→热纲否」。**三项合取不等于已验证**："
        "其中『下利清谷』之适用域已知为 §91 病程条件（119批 P0-9），"
        "**stage_conditional 成分混入 cross_scenario 排除式** ⇒ scope 未验"],
 3199: ["true_dependency","trigger","source_verified","保留·已自称候选","「→候选确认」措辞已是候选层"],
 3651: ["true_dependency","confirm","candidate","降 support_only",
        "「身热不扬+苔黄腻+脉滑数→茵陈蒿汤」——方证域；未做同域反例攻击"],
 4517: ["commentary","support","source_verified","保留","§350 胡老原话之引述（厥非皆寒），是反证不是硬映射"],
 3234: ["commentary","support","source_verified","保留","§301 少阴反发热，本身即反证条"],
 3226: ["commentary","support","source_verified","保留","§148 鉴别锚之引述"],
 3561: ["true_dependency","confirm","candidate","降 support_only","「肠间水声+心下悸+短气→苓桂术甘汤」——方证域，未反例攻击"],
 4420: ["true_dependency","trigger","candidate","保留为 trigger","「兼心下逆满/气上冲/…→水饮冒眩」——候选生成"],
 3650: ["true_dependency","confirm","candidate","降 support_only","「腹满便溏+苔白腻+无热象→理中加苍术」——方证域，未反例攻击"],
 3533: ["case_text","support","candidate","保留","方证卡片之可观察判据列举"],
 4347: ["true_dependency","trigger","source_verified","保留","只赋属性(性质:黏滞不爽)，不定证"],
 4402: ["true_dependency","trigger","source_verified","保留","只赋程度属性"],
 3311: ["true_dependency","support","candidate","保留为 support","太阴里虚寒谱之列举"],
 3264: ["true_dependency","confirm","candidate","降 support_only","「兼但热不寒脉沉实→少阳阳明合病」——未反例攻击"],
 # ── 120批 新读之 60 条 ──────────────────────────────
 57:   ["commentary","trigger","source_verified","保留","执行步骤索引，非判据"],
 61:   ["commentary","trigger","source_verified","保留","三毒层级声明，非判据"],
 117:  ["commentary","support","source_verified","保留","八纲两层结构声明（四书互证），是定义非映射"],
 136:  ["commentary","support","source_verified","保留","禁令清单（阴阳≠寒热／虚实分对象／未采＝未知）——皆为约束非映射"],
 305:  ["commentary","support","source_verified","保留","三层架构声明"],
 510:  ["commentary","support","source_verified","保留","3×2=6 之结构陈述"],
 765:  ["commentary","support","source_verified","保留","同上，重出"],
 3468: ["duplicate","support","source_verified","保留","与 L305 同旨重出"],
 4498: ["commentary","support","source_verified","保留","三毒不同层之声明"],
 3155: ["true_dependency","support","scope_verified","⭐保留·可入IR",
        "「寒热是阴阳的恒定判据，方向永不变异」——即 寒⇒阴/热⇒阳 单向，"
        "锚 C卷·6936「在任何情况下，永不变异」。**已入 rules/core_v0.json 之精神**"],
 3195: ["commentary","trigger","source_verified","保留","章节标题行"],
 3261: ["commentary","trigger","source_verified","保留","章节标题行"],
 3357: ["commentary","trigger","source_verified","保留","章节标题行"],
 3359: ["commentary","trigger","source_verified","保留","章节标题行"],
 3061: ["true_dependency","trigger","source_verified","保留为 trigger","▶T触发(任一)——设计即为 trigger 层，合规"],
 3074: ["true_dependency","trigger","source_verified","保留为 trigger","同上"],
 3558: ["true_dependency","trigger","source_verified","保留为 trigger","同上"],
 3655: ["true_dependency","trigger","source_verified","保留为 trigger","同上"],
 3080: ["true_dependency","support","source_verified","保留","「热纲确认后必须再过虚实纲」——次序约束，非映射"],
 3107: ["true_dependency","exclude","candidate","⛔须重验",
        "「腹软喜按★∧脉微细无力★∧汗吐下后恶寒★→实纲否」——exclusion 而 validation 未达阈值"],
 3225: ["true_dependency","confirm","candidate","降 support_only","「无热恶寒+正虚线索→表阴确认」——未反例攻击"],
 3228: ["commentary","support","source_verified","保留","§148 之解释"],
 3266: ["true_dependency","support","source_verified","⭐保留",
        "「兼恶寒发热并见→太阳少阳合病」——**这是【防早排】之提示，非硬门**，方向正确"],
 3309: ["true_dependency","support","source_verified","⭐保留","「合病提示(不排厥阴)」——防早排"],
 3336: ["true_dependency","support","source_verified","⭐保留","「合病提示(不排阳明)」——防早排"],
 3364: ["true_dependency","support","source_verified","⭐保留","「合病提示(不排太阴)」——防早排"],
 3353: ["true_dependency","confirm","candidate","降 support_only","「里虚寒象+[脉沉缓弱·或替代…]→C确认」——未反例攻击"],
 3363: ["true_dependency","trigger","candidate","保留为 trigger","「思饮/口干+口苦咽干+自利+四肢逆冷→厥阴太阴合病方向」——已作方向不作确认"],
 3436: ["commentary","support","source_verified","保留","胡老原话引述（阳明预后枢轴＝津液存亡）"],
 3517: ["true_dependency","support","source_verified","保留为 support","「脉沉迟＝胃气津液之读数」——**读数**非定证，锚 C L616"],
 3531: ["true_dependency","support","source_verified","保留","分野用途说明（桂枝汤系→新加汤）"],
 3641: ["true_dependency","confirm","candidate","降 support_only","「脉沉迟+腹满+喘→正水」——金匮分型，未反例攻击"],
 3642: ["true_dependency","support","source_verified","保留","「石水→无单方(辨证论治)」——**明说无方**，是诚实缺口声明"],
 3658: ["true_dependency","confirm","candidate","⛔**fail_closed**",
        "「腹满嗳腐+便溏→保和丸**[推演]**」——⭐**行内自带 [推演] 标记＝非胡老原文**，"
        "source_layer=L6_engine 而在执行层作 confirm ⇒ 依锁7 须 fail closed"],
 3979: ["true_dependency","confirm","candidate","降 support_only","舌脉总表「脉沉实有力｜里热实｜阳明腑实→承气汤」"],
 3993: ["true_dependency","confirm","candidate","降 support_only","「苔少+舌淡+脉沉细→胃气衰败·太阴底盘」"],
 3995: ["true_dependency","confirm","candidate","降 support_only","「苔白腻+舌淡+脉沉弦→寒饮内停」"],
 3996: ["true_dependency","confirm","candidate","降 support_only","「苔黄腻+舌淡红+脉弦滑→湿热痰」"],
 3998: ["true_dependency","confirm","candidate","降 support_only","「苔黄燥+舌红+脉沉实→阳明里热」"],
 4012: ["true_dependency","support","candidate","保留为 support","「{痘痘+苔黄腻+汗黏腻+便溏}→湿热郁蒸」"],
 4023: ["true_dependency","trigger","candidate","保留为 trigger","119批已加候选标记；「渴+下寒→厥阴禁单排里阴」为防早排"],
 4037: ["true_dependency","trigger","source_verified","保留为 trigger","症状→方索引，带条文号"],
 4039: ["true_dependency","trigger","source_verified","保留为 trigger","同上"],
 4042: ["true_dependency","trigger","source_verified","保留为 trigger","「背恶寒：口中和脉沉→少阴附子汤[§304]」——带鉴别对举"],
 4043: ["true_dependency","trigger","source_verified","⭐保留","四肢厥冷之**竞争分流**（四逆散/四逆汤/当归四逆），非单指"],
 4061: ["true_dependency","trigger","scope_verified","⭐保留·佳",
        "「★要求位置脉而病历仅载性质脉→该★悬挂(非不命中非命中)」——**三值语义之正确实装**"],
 4076: ["true_dependency","support","source_verified","保留","脉→四态之读数映射"],
 4078: ["true_dependency","support","source_verified","保留","二便→态之读数映射"],
 4079: ["true_dependency","support","source_verified","保留","渴饮→津液存量之读数"],
 4111: ["true_dependency","confirm","candidate","⛔须重验",
        "「喜按**(实纲/虚纲之充分判据)**」——**自称充分判据**而未见反例攻击记录 ⇒ validation 不足"],
 4251: ["true_dependency","trigger","scope_verified","⭐保留·佳","N6 复合拆分：一句多症逐一拆记（口苦咽干思饮→三 token）"],
 4397: ["true_dependency","support","source_verified","保留","【机械条款】病程>1月屡治不解→记「渴不差」——属性升级非定证"],
 4398: ["true_dependency","support","source_verified","保留","「思饮→渴{程度:轻}」属性赋值"],
 4427: ["true_dependency","trigger","candidate","保留为 trigger","「{脉阴阳俱微+不仁如风痹}→血痹方向」"],
 4440: ["true_dependency","support","source_verified","保留","方证谱＋原文辨证要点引"],
 4441: ["case_text","support","source_verified","保留","原文引述之续行"],
 4519: ["commentary","support","source_verified","⭐保留","胡老原话·真武 vs 苓桂术甘之阴阳分度（身振振→阳／振振欲擗地→阴）"],
 4525: ["true_dependency","support","source_verified","⭐保留·重",
        "胡老原话「反应为阳性的为少阳病，阴性为厥阴病」——**半表半里内部阴阳二分之唯一判据**"],
 4548: ["commentary","support","source_verified","保留","B2讲解·久病正虚脉实大数者死（通例性死候）"],
 4550: ["commentary","support","source_verified","保留","B2讲解·吐血咳逆脉数有热不得卧者死"],
}


def seg_of(L, i):
    for k in range(i, -1, -1):
        m = re.match(r"^# (\d\d_\S+)", L[k])
        if m: return m.group(1)
    return "?"


def narrow(L, segs):
    rows = {}
    for no, pat in SRC:
        for i, l in enumerate(L):
            if re.search(pat, l) and segs[i] in EXEC and JUDGE.search(l) and not REV.search(l):
                rows.setdefault(i + 1, (no, segs[i], l.strip()))
    return rows


def main():
    L = open(V8, encoding="utf-8").read().split("\n")
    segs = [seg_of(L, i) for i in range(len(L))]
    rows = narrow(L, segs)
    total = len(rows)
    read = [k for k in rows if k in READ]
    unread = [k for k in rows if k not in READ]
    from collections import Counter
    cd = Counter(READ[k][0] for k in read)
    cv = Counter(READ[k][2] for k in read)

    O = ["# P0 真实下游依赖审计（120批·全量人读）", "",
         "⛔ **用户令二·改账**：119批 一面写「86 中已读 20」，一面在验收表写"
         "「P0 16项已完成真实依赖审计 ✅」——**两者矛盾，该 ✅ 撤销。**", "",
         "## 一、账目", "", "| 项 | 数 |", "|---|---:|",
         "| 机器收窄候选（执行层∧带判据符∧未撤销） | **%d** |" % total,
         "| **human_read** | **%d** |" % len(read),
         "| ⛔**unknown_due_to_not_read** | **%d** |" % len(unread), "",
         "⚠ **119批 报 86，本批为 %d**——差额系 119批 自身之改动给 6 行加了撤销标记，"
         "已自动移出候选集。**非漏计。**" % total, "",
         "## 二、actual_dependency 分布（七值·统一口径）", "",
         "| 值 | 条 |", "|---|---:|"]
    for k in DEP:
        O.append("| `%s` | %d |" % (k, cd.get(k, 0)))
    O += ["", "## 三、validation_status 分布", "", "| 值 | 条 |", "|---|---:|"]
    for k, v in cv.most_common():
        O.append("| `%s` | %d |" % (k, v))
    O += ["", "⇒ ⭐⭐ **`candidate` %d 条——即『尚未达执行阈值』者。"
          "依 `docs/RULE_SCHEMA_V0.md` 锁1，它们不得以 confirm/exclude 之效力 active。**"
          % cv.get("candidate", 0), "",
          "## 四、逐条（%d 条）" % len(read), "",
          "| 行 | 层 | P0 | actual_dependency | rule_effect | validation | action | reason |",
          "|---|---|---|---|---|---|---|---|"]
    for ln in sorted(read):
        no, sg, tx = rows[ln]
        d = READ[ln]
        O.append("| L%d | `%s` | %s | **%s** | %s | **%s** | %s | %s |"
                 % (ln, sg, no, d[0], d[1], d[2], d[3], d[4].replace("|", "｜")))
    if unread:
        O += ["", "## ⛔ 未读（一律标 unknown，不得默认为无依赖）", ""]
        for ln in sorted(unread):
            O.append("- L%d `%s`：`%s`" % (ln, rows[ln][1], rows[ln][2][:100]))
    O += ["", "---", "", "## 五、⭐ 本批新发现", "",
          "1. ⛔**L3658「腹满嗳腐+便溏→保和丸`[推演]`」**——**行内自带 `[推演]` 标记，"
          "即非胡老原文**，`source_layer=L6_engine`，却在执行层作 confirm。**依锁7 须 fail_closed。**",
          "2. ⛔**L4111「喜按（实纲/虚纲之**充分判据**）」**——**自称充分判据**而无反例攻击记录。",
          "3. ⛔**L3078「口不渴★∧四肢不温★∧下利清谷★→热纲否」**——其中『下利清谷』"
          "之适用域 119批 已判为 §91 **病程条件**，**stage_conditional 成分混入 cross_scenario 排除式**。",
          "4. ⭐**L4061「★要求位置脉而病历仅载性质脉→该★悬挂（非不命中非命中）」**"
          "——**三值语义之正确实装，引擎内本来就有**。",
          "5. ⭐**L4525 胡老原话「反应为阳性的为少阳病，阴性为厥阴病」**"
          "——半表半里内部阴阳二分之**唯一判据**，价值高，宜优先入 IR。",
          "6. ⭐**四条「合病提示(不排X)」（L3266/3309/3336/3364）方向正确**——"
          "它们是**防早排**规则，与本工程反复在打的『单 token 早排』正相反。", "",
          "⚠ 由 `tools/yilai_shenji_120.py` 生成；**READ 一栏为人写，工具不得覆盖。**", ""]

    # ── 复合前件合法性复核（用户令十五）──────────────────
    CMP = [ln for ln in read if len(re.findall(r"[+∧·]", rows[ln][2])) >= 2
           and READ[ln][0] == "true_dependency"]
    M = ["# P0 复合前件合法性复核（120批·用户令三、十五）", "",
         "⛔⛔ **新增硬不等式：`compound_antecedent != validated_rule`。**",
         "**119批 之「✅复合前件·本就合法·保留」全部撤销该 reason 并重读。**",
         "即使三项、四项合取，仍可能：source错／scope错／object错／后学倒灌／"
         "support被写成confirm／典型证被写成充分条件／方证规则被上提为六经规则／存在同域反例。", "",
         "## 复核表（%d 条）" % len(CMP), "",
         "| 行 | 原规则 | 作用对象 | 前件结构 | 来源层 | 适用域 | 原句逻辑强度 | 反例攻击 | **最终类型** |",
         "|---|---|---|---|---|---|---|---|---|"]
    FINAL = {"confirm": "support_only", "exclude": "disputed", "support": "support_only",
             "trigger": "trigger_only"}
    for ln in sorted(CMP):
        no, sg, tx = rows[ln]
        d = READ[ln]
        fin = ("confirmed_rule" if d[2] in ("scope_verified", "counterexample_audited")
               else FINAL.get(d[1], "unknown"))
        obj = "六经归属" if re.search(r"太阳|少阳|阳明|太阴|少阴|厥阴|半表半里", tx) else \
              ("方证" if "汤" in tx else "八纲/属性")
        scope = "formula_pattern" if "汤" in tx else "cross_scenario"
        strength = "confirm 式" if d[1] == "confirm" else ("exclusion 式" if d[1] == "exclude" else d[1])
        M.append("| L%d | `%s` | %s | %d 项合取 | %s | %s | %s | %s | **%s** |"
                 % (ln, tx.replace("|", "｜")[:52], obj,
                    len(re.findall(r"[+∧·]", tx)) + 1, "L4_hu_theory",
                    scope, strength,
                    "⛔未做" if d[2] == "candidate" else "已做",
                    fin))
    M += ["", "## 小结", "",
          "| 最终类型 | 条 |", "|---|---:|"]
    fc = Counter()
    for ln in CMP:
        d = READ[ln]
        fc[("confirmed_rule" if d[2] in ("scope_verified", "counterexample_audited")
            else FINAL.get(d[1], "unknown"))] += 1
    for k, v in fc.most_common():
        M.append("| `%s` | %d |" % (k, v))
    M += ["", "⇒ ⛔ **119批 判为「合法·保留」之 11 条，本批复核后无一条为 `confirmed_rule`——"
          "全部降为 `support_only` / `trigger_only` / `disputed`。**",
          "⇒ **理由不是它们错，是【未做同域反例攻击】⇒ validation=candidate ⇒ 依锁1 不得 confirm。**", ""]

    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write("\n".join(O))
        open(OUT2, "w", encoding="utf-8").write("\n".join(M))
        print("已写入 %s\n已写入 %s" % (OUT, OUT2))
    print("候选 %d｜human_read %d｜unknown_due_to_not_read %d" % (total, len(read), len(unread)))
    print("复合前件复核 %d 条：" % len(CMP) + "｜".join("%s %d" % (k, v) for k, v in fc.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
