#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jiegou_buqi_123.py —— 11 组候选翻转组·结构补齐（123批·上级令五、令九）

令九：每组补齐 14 栏，且「决定变量」**必须写明竞争对象**——
      「渴」本身不是决定变量；「在黄汗 scope 下，为区分 S1 与 S2，渴/不渴具有分野作用」才是。

令五：Stage 拆为三栏——**拆数据语义，不新建医学本体**：
      process_stage    ：脓未成熟→将成→已成；燥屎形成阶段
      treatment_history：发汗后／误下后／服柴胡汤后（**已发生之历史事实**）
      state_transition ：少阳→阳明；肺中冷→转为消渴；表未解→入里
      ⛔ treatment_history ≠ Intervention：前者是历史，后者是**当前辨识过程中主动施加、
        且【预设了鉴别分支】**之操作。

令十：本批不动药物映射、二味方、三毒、六经本体。
"""
import os

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "evidence", "翻转组_结构补齐_123批.md")

FIELDS = ["observable", "competitor_set", "latent_state",
          "process_stage", "treatment_history", "diagnostic_intervention",
          "state_transition", "decision", "source_layer", "source_scope",
          "minimality_status", "identifiability_status",
          "counterexample_search", "falsifier"]

# 决定变量之合法写法：必须含 scope 与竞争对象
G = [
{"id": "FLIP-01", "题": "肠痈·脉迟紧/洪数",
 "observable": "脉（迟紧／洪数）",
 "competitor_set": "{脓未成熟, 脓已成}｜⛔竞争解释另有：脉之寒热读法、脉之虚实读法",
 "latent_state": "痈脓成熟程度（`ordinal`：immature→maturing→mature）",
 "process_stage": "⭐**有**：脓之成熟过程",
 "treatment_history": "无",
 "diagnostic_intervention": "无（无须施治即可测）",
 "state_transition": "无（是同一过程之推进，非转属他证）",
 "decision": "脓未成→`escalate`（可下，大黄牡丹汤）／脓已成→`contraindicate`（不可下）＋`switch`（排脓）",
 "source_layer": "L1_fact（条文）＋L2_hu_behavior（胡老注「当指脓未成熟，不定是无脓」）",
 "source_scope": "formula_pattern·肠痈",
 "minimality_status": "✅**最小**：单一观察项（脉），无须施治",
 "identifiability_status": "✅identifiable：入口＝脉",
 "counterexample_search": "⛔**本批未做**。检索式未拟，检索范围未定 ⇒ 依令十不得入 runtime",
 "falsifier": "⭐**能证伪本组者**：同为肠痈、脉迟紧而胡老不下；或脉洪数而胡老仍下。**未查**",
 "决定变量": "**在【肠痈】scope 下，为区分{脓未成熟, 脓已成}，脉之迟紧/洪数具有分野作用。**"
             "⛔不得写作「脉洪数＝热」，亦不得写作「脉洪数⇒不可下」之无 scope 规则"},

{"id": "FLIP-02", "题": "肺痈·脓成未成",
 "observable": "⭐**时时振寒**／**吐如米粥**〔讲金匮·85483〕——"
               "⛔122批 我误填「脓之成否」（那是潜状态不是观察项），且误判为无入口，已改",
 "competitor_set": "{脓未成, 脓已成}｜竞争解释：痰饮壅盛之量",
 "latent_state": "脓之成熟程度（`ordinal`，与 FLIP-01 同型）",
 "process_stage": "⭐**有**，且胡老自道其为时间序：「就是一个脓已成、脓未成，**就是前后的关系**」〔讲金匮·101489〕",
 "treatment_history": "无",
 "diagnostic_intervention": "无",
 "state_transition": "无",
 "decision": "脓未成→泻肺逐痰（葶苈大枣泻肺汤）／脓已成→`stop`「**这个药不能用**」＋`switch`（排脓）",
 "source_layer": "L1_fact＋L2_hu_behavior（讲金匮 95384／101489／85533 三处）",
 "source_scope": "formula_pattern·肺痈",
 "minimality_status": "⚠**非最小**：入口为【振寒】与【吐如米粥】两项，且分处异段",
 "identifiability_status": "✅identifiable（**122批 曾误判 unidentifiable，已撤**）",
 "counterexample_search": "⛔未做",
 "falsifier": "肺痈见振寒/吐米粥而胡老仍用葶苈大枣；或脓未成而胡老径排脓。**未查**",
 "决定变量": "**在【肺痈】scope 下，为区分{脓未成, 脓已成}，振寒＋吐如米粥具有分野作用。**"
             "⭐与 FLIP-01 共用同一 `process_stage` 类型而**入口不同**（彼脉、此振寒/吐脓）"
             "⇒ **阶段变量可跨部位复用，其观察入口却随部位而变。**"},

{"id": "FLIP-03", "题": "§209·转矢气",
 "observable": "矢气（转／不转）",
 "competitor_set": "{有燥屎, 但初头硬后必溏}｜⛔原文明说此时【大便硬否】无从证明",
 "latent_state": "燥屎之有无与结成程度",
 "process_stage": "⭐**有**：燥屎形成阶段",
 "treatment_history": "不大便六七日",
 "diagnostic_intervention": "⭐⭐**是**：少与小承气汤。**治疗前已预先规定两种结果各自意味什么**"
                            "⇒ 鉴别力强于一般疗效反推",
 "state_transition": "无",
 "decision": "转矢气→`escalate`（大承气）／不转→`contraindicate`（慎不可攻）＋小承气和之",
 "source_layer": "L1_fact＋L2_hu_behavior〔讲伤寒·218076「**不是大承气汤专攻硬便，大便硬是用大承气汤的火候**」〕",
 "source_scope": "stage_conditional·诊断性试治",
 "minimality_status": "⚠单一观察项，**但须先施治方得**——与「无须施治即可测」之最小性不同类",
 "identifiability_status": "✅identifiable·**须先施治**",
 "counterexample_search": "⛔未做",
 "falsifier": "转矢气而无燥屎；或不转矢气而大承气有效。**未查**",
 "决定变量": "**在【阳明·不大便六七日且大便硬否无从证明】scope 下，"
             "为区分{有燥屎, 初头硬后必溏}，服小承气后之转矢气与否具有分野作用。**"
             "⛔『大便硬』是**火候**（`process_stage`），不是大承气之治疗对象"},

{"id": "FLIP-04", "题": "伤寒有停水·渴/呕",
 "observable": "渴／呕／小便利否（**三项纠缠**）",
 "competitor_set": "{里有停水·表不解, 停水而不渴而呕}",
 "latent_state": "停水之部位",
 "process_stage": "无",
 "treatment_history": "无",
 "diagnostic_intervention": "无",
 "state_transition": "无",
 "decision": "`switch`（五苓散 ↔ 茯苓甘草汤）",
 "source_layer": "⛔**L1 疑脱漏**：胡老注「原条文『伤寒汗出』后，**似脱漏『脉浮数，小便不利』七字**，"
                 "『不渴』后**似脱漏『而呕』二字**，不然则无法理解」⇒ text_status=**emended_by_hu**",
 "source_scope": "formula_pattern·伤寒有停水",
 "minimality_status": "⛔**非最小**，且其成对性**由校勘支撑，非原文自明**",
 "identifiability_status": "⚠存疑",
 "counterexample_search": "⛔未做",
 "falsifier": "若他本无此脱漏而文义自足，则胡老之补字不成立，本组瓦解。**未查异本**",
 "决定变量": "⛔**本组现不得提出决定变量**——底本未定，谈分野项无意义"},

{"id": "FLIP-05", "题": "黄汗·渴/不渴",
 "observable": "渴（有／无）",
 "competitor_set": "{津液亡失已甚, 表虚气水外郁而津未大伤}",
 "latent_state": "津液亡失程度（`ordinal`）",
 "process_stage": "无",
 "treatment_history": "无",
 "diagnostic_intervention": "无",
 "state_transition": "无",
 "decision": "`switch`（黄芪芍药桂枝苦酒汤 ↔ 桂枝加黄芪汤）",
 "source_layer": "L1_fact＋L2_hu_behavior",
 "source_scope": "formula_pattern·黄汗",
 "minimality_status": "✅**最小**：单一观察项，无须施治",
 "identifiability_status": "✅identifiable",
 "counterexample_search": "⛔未做",
 "falsifier": "黄汗而渴却用桂枝加黄芪；或不渴而用芪芍桂酒。**未查**",
 "决定变量": "**在【黄汗】scope 下，为区分{津液亡失已甚, 未大伤}，渴/不渴具有分野作用。**"
             "⛔⛔**「渴」本身不是决定变量**——同一个渴，在 FLIP-11 之阳明误下域"
             "映射到{热盛津枯, 水停不化}，在 FLIP-09 映射到{转属阳明}。"
             "⇒ **脱离 scope 与竞争集，「渴」不指任何状态。**"},

{"id": "FLIP-06", "题": "霍乱·欲饮水否",
 "observable": "欲饮水否",
 "competitor_set": "{热多, 寒多}",
 "latent_state": "寒热（`ordinal`：less/more——⭐原文以【多少】分方，非以有无分方）",
 "process_stage": "无",
 "treatment_history": "无",
 "diagnostic_intervention": "无",
 "state_transition": "无",
 "decision": "`switch`（五苓散 ↔ 理中丸）",
 "source_layer": "L1_fact",
 "source_scope": "formula_pattern·霍乱",
 "minimality_status": "⚠**分野语即是结论**：原文直书「热多欲饮水」「寒多不用水」，"
                      "观察项与状态名捆在一句里 ⇒ 不可用作「八纲装不下」之证",
 "identifiability_status": "✅identifiable",
 "counterexample_search": "⛔未做",
 "falsifier": "霍乱而欲饮水却用理中。**未查**",
 "决定变量": "**在【霍乱·头痛发热身疼痛】scope 下，为区分{热多, 寒多}，欲饮水与否具有分野作用。**"
             "⛔不得编译为全局规则「欲饮水⇒热」"},

{"id": "FLIP-07", "题": "太阳下后·去芍药/加附子",
 "observable": "脉＋恶寒（**两项**）",
 "competitor_set": "{误下后表未罢·腹虚气冲, 已由阳转阴}",
 "latent_state": "是否陷于阴证",
 "process_stage": "无",
 "treatment_history": "⭐**有**：太阳病**下之后**（⛔此为历史事实，非诊断性干预——原文未把下法当作试治）",
 "diagnostic_intervention": "无",
 "state_transition": "⭐**有**：阳→阴（胡老解为「病已由阳转阴」）",
 "decision": "`switch`（桂枝去芍药汤 → 加附子），形式上为**加一味**",
 "source_layer": "L1_fact＋L2_hu_behavior",
 "source_scope": "formula_pattern·太阳下后",
 "minimality_status": "⛔**非最小**：脉与恶寒两项同变",
 "identifiability_status": "⚠**弱**：原文未明示因果",
 "counterexample_search": "⛔未做",
 "falsifier": "脉微恶寒而不加附子仍效。**未查**",
 "决定变量": "**在【太阳病下之后】scope 下，为区分{表未罢, 转阴}，脉微＋恶寒之并见具有分野作用。**"
             "⚠ 上级所提『ΔFormula ↔ ΔState』（加附子 ↔ 转阴）**本批只记为待验证假说**，"
             "⛔不得先验成立，且**令十明禁本批开药物反演**"},

{"id": "FLIP-08", "题": "§100·小建中→小柴胡",
 "observable": "服小建中汤后之差／不差",
 "competitor_set": "⭐**胡老明言二者共存**：「**根本这个脉呀既有建中证，也有柴胡证**」〔讲伤寒·123110〕"
                   "⇒ {中虚有寒, 柴胡证}",
 "latent_state": "中虚有寒 ／ 少阳",
 "process_stage": "无",
 "treatment_history": "无",
 "diagnostic_intervention": "⭐⭐**是**：先与小建中汤",
 "state_transition": "⭐**有**：中虚有寒 → 转属少阳",
 "decision": "差→`stop`／不差→`switch`，⛔**但非直通**：胡老诫「『不差者，小柴胡汤主之』，"
             "是**强调有小柴胡汤方证时**才可用」⇒ 正链为【不差→柴胡证候选升高→**重验小柴胡方证**→成立方 switch】",
 "source_layer": "L1_fact＋L2_hu_behavior（讲伤寒·123035／123110；经方传真系·33354）",
 "source_scope": "stage_conditional·诊断性试治",
 "minimality_status": "⚠单一观察项，须先施治",
 "identifiability_status": "✅identifiable·须先施治",
 "counterexample_search": "⛔未做",
 "falsifier": "服小建中不差而柴胡证不见、用小柴胡无效。**未查**",
 "决定变量": "**在【阳脉涩阴脉弦·腹中急痛】scope 下，为区分{中虚有寒, 柴胡证}，"
             "服小建中后之差/不差具有分野作用。**"
             "⛔⛔**并须记【治疗次序律】——它不是分野项，是选哪一支先试之规则**："
             "〔A·讲伤寒·123035〕「**得先温里。这个里需温需补都得从里治，这个里需攻需下，"
             "那就先从外治，这是定法**」⇒ **首选试治由定法选定，不由概率选定**（令六：仅记为原文规则候选，不得晋升为全局排序器）"},

{"id": "FLIP-09", "题": "服柴胡汤已·渴者属阳明",
 "observable": "服小柴胡汤后之渴",
 "competitor_set": "{药后津伤, 转属阳明}",
 "latent_state": "阳明",
 "process_stage": "无",
 "treatment_history": "⭐**有**：服柴胡汤已",
 "diagnostic_intervention": "⛔**否**——原文**未预先规定「渴则如何」**，是事后归因。"
                            "⇒ 鉴别力弱于 FLIP-03/08，**不得与之并列计数**",
 "state_transition": "⭐**有**：少阳 → 阳明。⇒ **六经在此是动态状态分类变量，不是永久病名**",
 "decision": "`switch`（以法治之·阳明法，**未具名**）",
 "source_layer": "L1_fact＋L2_hu_behavior",
 "source_scope": "stage_conditional·服后转属",
 "minimality_status": "⚠单一观察项，**但须服药后**方得——不属「无须施治即可测」",
 "identifiability_status": "⚠**弱**：B 支未具方",
 "counterexample_search": "⛔未做",
 "falsifier": "服柴胡后渴而非阳明（如药后一时津伤，不治自复）。**未查**",
 "决定变量": "**在【服小柴胡汤已】scope 下，为区分{药后津伤, 转属阳明}，渴具有分野作用。**"
             "⚠ 而原文只给了结论未给分野判据 ⇒ **本组之『分野』实由胡老径断，非由观察推得**"},

{"id": "FLIP-10", "题": "甘草干姜汤后·渴者属消渴",
 "observable": "服甘草干姜汤后之渴",
 "competitor_set": "{药后津伤, 转为消渴}",
 "latent_state": "消渴",
 "process_stage": "无",
 "treatment_history": "⭐**有**：服汤已",
 "diagnostic_intervention": "⛔否（同 FLIP-09，事后归因）",
 "state_transition": "⭐**有**：肺中冷（胃虚有饮）→ 转为**消渴病**（转为另一【病】）",
 "decision": "⭐`stop`：「**非本方所能治了**」——**只止方，不给替代方**",
 "source_layer": "L1_fact＋L2_hu_behavior",
 "source_scope": "stage_conditional·服后转属",
 "minimality_status": "⚠单一观察项，**但须服药后**方得——不属「无须施治即可测」",
 "identifiability_status": "⚠弱",
 "counterexample_search": "⛔未做",
 "falsifier": "服甘草干姜后渴而本方续用仍效。**未查**",
 "决定变量": "**在【肺痿·服甘草干姜汤已】scope 下，为区分{药后津伤, 转为消渴}，渴具有分野作用。**"
             "⛔121批 我把『止方』列为 residual（无出口之状态变量）——**层级错**，"
             "它是 `decision` 之一个取值，已归丙组"},

{"id": "FLIP-11", "题": "阳明误下后·白虎加人参/猪苓",
 "observable": "口舌干燥／小便不利／汗出（**须组合**）",
 "competitor_set": "⭐**三支非两支**：{热盛津枯（白虎加人参）, 水停不化（猪苓）, "
                   "烦而**不渴**之栀子豉汤证}",
 "latent_state": "热盛津枯 ／ 水停不化",
 "process_stage": "无",
 "treatment_history": "⭐**有**：阳明**误下后**",
 "diagnostic_intervention": "无",
 "state_transition": "无",
 "decision": "`switch`（白虎加人参 ↔ 猪苓汤）",
 "source_layer": "L1_fact＋L2_hu_behavior（胡老明给分野：「口舌干燥」vs「小便不利」）",
 "source_scope": "differential·阳明误下后烦热",
 "minimality_status": "⛔**非最小**：两项以上同变",
 "identifiability_status": "✅identifiable：胡老明给二者之别",
 "counterexample_search": "⛔未做",
 "falsifier": "渴＋口舌干燥而猪苓汤效；或渴＋小便不利而白虎加人参效。**未查**",
 "决定变量": "⛔⛔**单一之『渴』不是决定变量**——三支皆可见渴（栀子豉汤支则不渴）。"
             "**在【阳明误下后·烦热】scope 下，为区分{热盛津枯, 水停不化}，"
             "{渴,口舌干燥,汗出} 对 {渴,小便不利} 之组合具有分野作用。**"
             "⇒ ⭐**决定变量可以是【组合】，且其基数须与竞争集基数一并记——"
             "否则会把三选一伪装成二选一**（121批 我即如此）"},
]


def main():
    L = []
    w = L.append
    w("# 11 组候选翻转组 · 结构补齐（123批·上级令五、令九）\n")
    w("> ⛔ 研究层。⛔ 令十：本批不动药物映射、二味方、三毒扩展、六经本体。\n")

    w("## 〇、Stage 已按令五拆为三栏（拆数据语义，不新建医学本体）\n")
    w("| 栏 | 装什么 | 本表命中 |")
    w("|---|---|---|")
    ps = [g["id"] for g in G if g["process_stage"].startswith("⭐")]
    th = [g["id"] for g in G if g["treatment_history"].startswith("⭐")]
    st = [g["id"] for g in G if g["state_transition"].startswith("⭐")]
    di = [g["id"] for g in G if g["diagnostic_intervention"].startswith("⭐")]
    w("| `process_stage` | 脓成熟度、燥屎形成阶段 | %s |" % "、".join(ps))
    w("| `treatment_history` | 发汗后／误下后／服某汤后（**已发生之历史事实**） | %s |" % "、".join(th))
    w("| `state_transition` | 少阳→阳明；肺中冷→消渴；阳→阴 | %s |" % "、".join(st))
    w("")
    w("⛔ **`treatment_history` ≠ `Intervention`**，本表以 FLIP-07 与 FLIP-03 对照即明：")
    w("- FLIP-07「太阳病**下之后**」：下法是**已发生之误治**，原文未把它当作试治 ⇒ `treatment_history`")
    w("- FLIP-03「**少与**小承气汤」：**当前辨识过程中主动施加，且治疗前已预设两种结果之含义** ⇒ `Intervention`")
    w("")
    w("⇒ 真正带**预设鉴别分支**之诊断性干预，全表只有 **%s** 两组（%d/11）。" % ("、".join(di), len(di)))
    w("　FLIP-09／FLIP-10 虽亦「服药后观察」，但原文**未预先规定结果之含义**，是事后归因，")
    w("　⛔**不得与 FLIP-03/08 并列计数**。\n")

    w("---\n")
    w("## 一、最小性与可辨识性总账\n")
    # ⛔ 分类须穷尽：初版四行只覆盖 8/11，FLIP-02/09/10 被静默漏掉。
    #   **一个不穷尽的分类表比没有表更坏**——它看起来已经把 11 组都安置了。
    #   故改为按序归档并在末尾断言总数。
    def _bucket(g):
        m = g["minimality_status"]
        if m.startswith("✅"):
            return "A"
        if "须先施治" in m:
            return "B"
        if "须服药后" in m:
            return "C"
        if "分野语即是结论" in m:
            return "D"
        return "E"
    BK = {k: [g["id"] for g in G if _bucket(g) == k] for k in "ABCDE"}
    mini = BK["A"]
    w("| 判 | 组 | 数 |")
    w("|---|---|---:|")
    w("| ✅ **最小**：单一观察项且**无须施治** | **%s** | %d |" % ("、".join(BK["A"]), len(BK["A"])))
    w("| ⚠ 单项，但须**先施治**（诊断性干预） | %s | %d |" % ("、".join(BK["B"]), len(BK["B"])))
    w("| ⚠ 单项，但须**服药后**方得（事后归因） | %s | %d |" % ("、".join(BK["C"]), len(BK["C"])))
    w("| ⚠ **分野语即是结论**（观察项与状态名捆在一句） | %s | %d |" % ("、".join(BK["D"]), len(BK["D"])))
    w("| ⛔ **非最小**（多项同变／底本未定） | %s | %d |" % ("、".join(BK["E"]), len(BK["E"])))
    w("| — | **合计** | **%d/11** |" % sum(len(v) for v in BK.values()))
    w("")
    assert sum(len(v) for v in BK.values()) == len(G), "分类未穷尽"
    w("⛔ **反例检索：11 组【全部未做】。** 依令十，研究层证据未经反例攻击**不得入 Typed IR runtime**。")
    w("⇒ 故本表 `falsifier` 一栏写的是「**什么东西能推翻本组**」，**不是「已经找过没有」**。\n")

    w("---\n")
    w("## 二、逐组十四栏\n")
    for g in G:
        w("### %s　%s\n" % (g["id"], g["题"]))
        w("| 栏 | 值 |")
        w("|---|---|")
        for f in FIELDS:
            w("| `%s` | %s |" % (f, g[f]))
        w("")
        w("> ⭐ **决定变量（令九·须写明竞争对象与 scope）**：%s\n" % g["决定变量"])

    w("---\n")
    w("## 三、⛔ 本表不能回答的\n")
    w("1. **反例检索一组未做**——`counterexample_search` 十一栏全是「未做」，不是「查过没有」。")
    w("2. **63 组机器候选仍未人读**（121批 扫出 74 组，只编码 11 组）。")
    w("3. **`ordinal` 之取值只覆盖三个变量**（脓成熟度、寒热程度、疼痛程度），"
      "其中**疼痛程度之原文锚本批未查**，为占位。")
    w("4. **FLIP-04 底本未定**（胡老补字），故其决定变量本批不提出。")
    w("5. ⛔ **上级所提『ΔFormula ↔ ΔState』（FLIP-07 加附子 ↔ 转阴）本批只记为待验证假说**——"
      "令十明禁本批开药物反演。\n")
    return L


if __name__ == "__main__":
    lines = main()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("已写 %s（%d 行）" % (OUT, len(lines)))
    print("组 %d｜栏 %d" % (len(G), len(FIELDS)))
    miss = [(g["id"], f) for g in G for f in FIELDS if not g.get(f)]
    print("缺栏：%s" % (miss or "无"))
