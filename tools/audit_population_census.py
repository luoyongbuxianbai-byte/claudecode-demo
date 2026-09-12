#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_population_census.py —— 审计全集普查＋分母修复（126B·上级令一〜七、九）

⛔⛔ 本器**取代** `tools/retrieval_integrity_audit.py` 之统计部分（该器之 A 类扫描仍复用）。
   126批 之三处统计污染，本器逐一修：

   ① **N=43 未经证明是全集** ⇒ 本器先做 population census：
      repository universe → discovery query → inclusion/exclusion criteria → object IDs。
      **N 由枚举产生，不得先写后审。**
   ② **0 锚被当成「未命中」** ⇒ 新增 `not_auditable_missing_anchor`，
      ⛔ **unknown／not_auditable 不得进入「未命中」分子**（未采 ≠ 阴性·协议51）。
   ③ **四闸共用分母 43** ⇒ 每闸各有 `eligible denominator`。

⛔ 令四：**撤销「A 类是个案」之总体结论。** 本器只报
   `confirmed_new` / `reviewed_flagged` / `unresolved`，**不推全工程发生率**。
"""
import importlib.util
import json
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, B)
sys.path.insert(0, os.path.join(B, "tools"))
from tools.retrieval_integrity_audit import (  # noqa: E402
    SPEAKER, anchors_in, scan_anchor, NEG_CLAIM, DUALTRACK, HAND_VERDICT)

OUT = os.path.join(B, "evidence", "审计全集普查与分母修复_126B.md")

# ══ 令九补读：126批 未决之锚，本批逐一人读 ══
HAND_126B = {
 "PULSE-SHU-HEAT|讲伤寒·156700": ("TP", "与 155445 同一单元（§134），即 `SW-134-PULSE4` 之王叔和之疑。已处理"),
 "SW-134-PULSE4|讲伤寒·155445": ("REGISTERED", "本条即该登记本身之 verdict_anchor，非污染"),
 "SW-134-PULSE4|讲伤寒·156700": ("REGISTERED", "同上"),
 "SW-176-BAIHU|C卷·74704": ("REGISTERED", "已人读全文：「此其中**必有错简，待考**」⇒ 登记无误"),
 "FLIP-03|C卷·70744": ("KNOWN", "§214 之注，125批 已据以撤销 scope_split；本锚现只出现在撤销说明中"),
 "FLIP-03|讲伤寒·262358": ("FP", "⛔**假命中**：该处「只要是燥屎就可以用它，**是不对的**」——"
   "胡老所否者是【读者之误会】，**不是文本本身**。"
   "⇒ ⚠**扫描器之已知歧义**：`是不对的` 兼指【此文有误】与【此解有误】两义，机器不能分。"),
 "NEC-TAIYANG-WUHAN|讲伤寒·196476": ("NO_ISSUE", "已人读：胡老讲太阳病两类型与温病，**无文本裁决**。"
   "⭐并顺带得一正面语「**所以太阳病啊必须要恶寒**」——与该规则之 `falsified_overbroad` 并不冲突"
   "（该规则被证伪者是【三项合取式】，非【太阳⇒恶寒】单项），本批不据以改状态。"),

 # ── 令九·本批补读之三锚 ──
 "META-M4|讲伤寒·44752": ("FP", "⛔假命中：单元为 §30 之长段，「这是错的」不在所引句之论域。"
   "⚠ 但须留一问：**§30 为问答体，其文本地位（是否王叔和所加）本批未审**，已记入待办。"),
 "META-M5|讲伤寒·45536": ("FP", "同上，同一 §30 单元。"),
 "SW-NUE-CHAIHUGUIJIANG|C卷·115389": ("REGISTERED", "本条即该登记本身之 verdict_anchor，非污染"),
 "META-M9|C卷·115389": ("TP", "⭐⭐**令九补读所得之第二起**：所引之句本身嵌在胡老之校勘疑问里——"
   "「不过只凭寒多热少而用本方，则与其后诸方的应用难以区别，**其中可能有错简**，"
   "用时仍宜参照上条所论为妥」。⇒ 该条已登记 `SW-NUE-CHAIHUGUIJIANG` = `suspected_corruption`。"
   "⚠ M9 之**方法论内容**（只凭单项则难以区别）仍可留作元规则；"
   "但**不得用它论该方之 scope**——那正是被疑有错简的部分。"),
}
HAND = dict(HAND_VERDICT)
HAND.update(HAND_126B)

# ══ 令一：population census ══
CENSUS_SPEC = {
  "repository_universe": ["rules/*.json", "evidence/*.md", "tools/*.py（含常量表之研究资产）",
                          "term_layer/*.md（审计册）", "docs/*.md（规范与调查）"],
  "discovery_query": [
     "D1 `rules/*.json` 之顶层条目（cells／variables／passages／list）",
     "D2 研究层工具之常量表（`fanzhuandui.PAIRS/COUNTER/TWO_HERB`、`jiegou_buqi_123.G`）",
     "D3 `evidence/*.md` 中**带 ID 之断言块**（R1–R5 residual、M1–M14 元规则）",
     "D4 `term_layer/*.md` 审计册之逐格裁决（已归入 D1 之 pulse_cells）",
     "D5 报告中被引而**无持久化资产**者（⇒ 记 population_gap，不入 N）",
  ],
  "inclusion": "凡①有稳定 ID、②有现行状态或断言、③可被四闸之任一评价者，入 N。",
  "exclusion": [
     ("原文抽取中间件（`term_layer/_*.json`、附录E 等）",
      "其内容是**被引之原文**，不是我方裁决 ⇒ 不入 N；其下游引用链另审（令八）"),
     ("已作废/归档件（`*改前*`、`*作废*`）", "非现行"),
     ("报告本身（`reports/*.md`）", "是叙述，不是资产；其结论已落在 D1–D3 之对象上"),
  ],
}


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(B, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def census():
    """返回 [(source_file, object_id, object_type, active, included, exclusion_reason, payload)]"""
    rows = []

    def add(src, oid, typ, payload, active=True, inc=True, why=""):
        rows.append(dict(source_file=src, object_id=oid, object_type=typ,
                         active_status="active" if active else "inactive",
                         included=inc, exclusion_reason=why, payload=payload))

    # D1
    for f, key, typ in [("rules/pulse_cells_v0.json", "cells", "term_mapping_cell"),
                        ("rules/state_variables_v0.json", "variables", "state_variable"),
                        ("rules/text_critical_v0.json", "passages", "text_critical_passage")]:
        d = json.load(open(os.path.join(B, f), encoding="utf-8"))
        for it in d[key]:
            oid = it.get("cell_id") or it.get("state_variable") or it.get("passage_id")
            add(f, oid, typ, it)
    for it in json.load(open(os.path.join(B, "rules", "core_v0.json"), encoding="utf-8")):
        add("rules/core_v0.json", it["rule_id"], "typed_ir_rule", it)

    # D2
    jb = _mod("jb", "tools/jiegou_buqi_123.py")
    for g in jb.G:
        add("tools/jiegou_buqi_123.py", g["id"], "FLIP", g)
    fz = _mod("fz", "tools/fanzhuandui.py")
    for c in fz.COUNTER:
        add("tools/fanzhuandui.py", c[0], "CE", {"row": list(c)})
    for th in fz.TWO_HERB:
        add("tools/fanzhuandui.py", th[0], "two_herb_formula", {"row": list(th)})

    # D3 ⭐126批 遗漏者，本批补入
    RES = {"R1": "脓成未成 → process_stage（122批 归位）",
           "R2": "干预产生之观察项 → Intervention（122批 归位）",
           "R3": "服后转属／止方 → state_transition＋decision（123批 再拆）",
           "R4": "SCHEMA-GAP-ORDINAL（124批 更名）",
           "R5": "条文观察集 ⊊ 胡老所用观察集 → source_layer（122批 归位）"}
    for k, v in RES.items():
        add("evidence/residual_台账_123批修订.md", "RESIDUAL-" + k, "residual_claim", {"text": v})
    META = {  # 125批 组合判定元规则 M1–M14（126批 漏入 N，本批补）
     "M1": ("讲伤寒·112879", "不能光凭脉，必须脉证结合起来看", "hu_lecture"),
     "M2": ("讲伤寒·70066", "不能片面的看问题……你还要看看脉", "hu_lecture"),
     "M3": ("讲伤寒·23463", "不能片面看问题……必须要全面观察", "hu_lecture"),
     "M4": ("讲伤寒·44752", "不能片面看问题……都得全面看问题", "hu_lecture"),
     "M5": ("讲伤寒·45536", "不是只凭脑子想……不能片面看问题，更不能主观", "hu_lecture"),
     "M6": ("讲伤寒·215689", "临床看问题要全面，不能片面", "hu_lecture"),
     "M7": ("临床家·109240", "单凭切脉断病是极端偏面的", "editor_compiled"),
     "M8": ("C卷·23806", "必须扶里之虚，才可解外之邪；若只着眼表不解", "uncertain"),
     "M9": ("C卷·115389", "不过只凭寒多热少而用本方，则难以区别", "uncertain"),
     "M10": ("伤寒论传真·117604", "不得只着眼于大便硬，应细审致硬之因", "editor_compiled"),
     "M11": ("病位类方解·15995", "一定要结合临床，不能只是以理推理", "editor_compiled"),
     "M12": ("病位类方解·99483", "必须熟悉大承气汤的方证，不能只记方药", "editor_compiled"),
     "M13": ("临床家·68267", "整个病的治疗要综合分析", "editor_compiled"),
     "M14": ("临床家·15293", "治病不能只有治疗大法", "editor_compiled"),
    }
    for k, (anc, txt, spk) in META.items():
        add("evidence/组合判定元规则_125批.md", "META-" + k, "meta_rule_evidence",
            {"anchor": anc, "quoted": txt, "speaker_declared": spk})

    # D5 ⛔ population_gap —— 有称引而无资产者，**不入 N**，单列
    add("reports/报告_第121批.md", "PHANTOM-63FLIP", "population_gap",
        {"note": "121批 称「机器扫出 74 组候选，只编码 11 组，其余 63 组标 unknown」。"
                 "⛔ **全 repository 查无该 74/63 组之任何持久化清单**，"
                 "`tools/fanzhuandui.py` 亦**无扫描代码**（只有人手录入之常量表）。"
                 "⇒ 该扫描**未落盘、工具未入库**，63 组**不存在为可审对象**。"},
        active=False, inc=False,
        why="⛔ 无持久化资产、无可重跑工具 ⇒ 不可审、不入 N；须重新扫描方能存在")
    return rows


# ══ 令二＋令三：每闸各自之可评价性与分母 ══
ST_NA = "not_applicable"
ST_NOANCHOR = "not_auditable_missing_anchor"
ST_UNKNOWN = "unknown_pending_review"
ST_OK = "audited_no_issue"
ST_ISSUE = "issue_found"


# ⛔⛔ 126C 自查：`not_auditable_missing_anchor` 一名，把两件不同的事又并成了一类——
#    (a) **作了文本断言而锚丢了** ⇒ 真缺锚，须补
#    (b) **根本不作文本断言**（否定性结果／分类裁决）⇒ 本闸 `not_applicable`
#    这与上级两次纠正我的 D 类混义、词/映射混义**同形**。故本批再拆一次。
NO_TEXTUAL_CLAIM = {
    "CE-04": "**否定性结果**（「本型反例未查得」）——`not_found` 之记录**按定义无锚**，"
             "其可审性属闸二（检索式是否单轨），不属闸一",
    "RESIDUAL-R1": "**分类裁决**（某 residual 归入哪一栏）——其证据在被指向之对象上，本身不作文本断言",
    "RESIDUAL-R2": "同上", "RESIDUAL-R3": "同上", "RESIDUAL-R4": "同上", "RESIDUAL-R5": "同上",
}


def gate_context(row):
    anc = anchors_in(row["payload"])
    if not anc:
        why = NO_TEXTUAL_CLAIM.get(row["object_id"])
        if why:
            return ST_NA, ["⛔ 本对象**不作文本断言** ⇒ 本闸不适用：%s" % why]
        return ST_NOANCHOR, ["⛔ 作了文本断言而**无可定位锚** ⇒ **本闸不可评价**（未采≠阴性），**须补锚**"]
    notes, unresolved, issue = [], False, False
    for bk, pos in anc:
        s = scan_anchor(bk, pos)
        key = "%s|%s·%d" % (row["object_id"], bk, pos)
        if s["status"] != "ok":
            notes.append("%s·%d %s" % (bk, pos, s["status"]))
            if HAND.get(key, ("", ""))[0] not in ("FP", "NO_ISSUE", "KNOWN", "REGISTERED"):
                unresolved = True
            continue
        if s["textcrit_hits"]:
            v = HAND.get(key, ("UNREAD", ""))[0]
            notes.append("%s·%d 机器报警[%s] ⇒ 人读=%s"
                         % (bk, pos, "／".join(s["textcrit_hits"][:3]), v))
            if v == "TP":
                issue = True
            elif v == "UNREAD":
                unresolved = True
    if issue:
        return ST_ISSUE, notes
    if unresolved:
        return ST_UNKNOWN, notes
    return ST_OK, notes or ["锚 %d，机器无报警" % len(anc)]


def gate_lexical(row):
    blob = json.dumps(row["payload"], ensure_ascii=False)
    if not NEG_CLAIM.search(blob):
        return ST_NA, ["⛔ 本对象**不含否定性检索结论** ⇒ 本闸不适用"]
    if DUALTRACK.search(blob):
        return ST_OK, ["含否定性结论，且已有双轨记录"]
    return ST_ISSUE, ["含否定性结论而**无双轨（语义近邻／映射）记录**"]


def gate_atomization(row):
    p = row["payload"]
    if not isinstance(p, dict) or "object" not in p:
        return ST_NA, ["⛔ 本对象无 `object` 栏 ⇒ 本闸不适用"]
    o = str(p["object"])
    hits = []
    if re.search(r"[／/]|＋|、", o):
        hits.append("object 并列多谓词：%s" % o[:40])
    if re.search(r"汤$|散$|丸$|六经|少阴|太阳|阳明|少阳|厥阴|太阴", o.strip()):
        hits.append("object 跨级：%s" % o[:40])
    return (ST_ISSUE, hits) if hits else (ST_OK, ["object 为单谓词且不跨级"])


# ══ 令五：GATE_4 provenance/attribution（D 类拆四）══
HU_DIRECT = re.compile(r"胡老(明|自|说|注|判|认|诫|言|曰)|胡老之(说|言|语|注)|胡老原话|hu_verbatim")
HU_CHANGE = re.compile(r"胡老自身|改变观点|晚年改|自身版本变化")


def gate_provenance(row):
    anc = anchors_in(row["payload"])
    declared = row["payload"].get("speaker_declared") if isinstance(row["payload"], dict) else None
    books = sorted({b for b, _ in anc})
    if not books and not declared:
        if row["object_id"] in NO_TEXTUAL_CLAIM:
            return ST_NA, ["⛔ 本对象不作文本断言，无来源可归 ⇒ 本闸不适用"], {}
        return ST_NOANCHOR, ["⛔ 作了文本断言而无锚、且未声明 speaker ⇒ **本闸不可评价**"], {}
    spk = {b: SPEAKER.get(b, "unknown_book") for b in books}
    if declared:
        spk.setdefault("(declared)", declared)
    blob = json.dumps(row["payload"], ensure_ascii=False)
    sub = {}
    # D1 speaker_identity_unresolved —— ⛔ 只算 uncertain，不算 editor_compiled
    d1 = [b for b, s in spk.items() if s == "uncertain"]
    if d1:
        sub["D1_speaker_identity_unresolved"] = d1
    # D2 attribution_overreach —— 以 editor_compiled／uncertain 之材料作胡老本人归因
    over = [b for b, s in spk.items()
            if s in ("editor_compiled", "editor_compiled_feng", "uncertain")]
    if over and HU_DIRECT.search(blob):
        sub["D2_attribution_overreach"] = over
    if HU_CHANGE.search(blob):
        sub.setdefault("D2_attribution_overreach", []).append("(胡老自身版本变化之措辞)")
    # D3 source_version_unresolved —— 同一命题两本异说
    if re.search(r"两本|注解本|讲课本|source_version|disputed", blob):
        sub["D3_source_version_unresolved"] = ["文中已述版本差异"]
    # D4 passage_authorship_unresolved —— 整理本之具体执笔人
    d4 = [b for b, s in spk.items() if s in ("editor_compiled", "editor_compiled_feng")]
    if d4:
        sub["D4_passage_authorship_unresolved"] = d4
    st = ST_ISSUE if sub else ST_OK
    return st, ["｜".join("%s:%s" % (k, "／".join(map(str, v))) for k, v in sub.items())
                or "speaker 皆已定且无越级归因"], sub


# ══ 令七：对象级最终裁决 ══
FINAL = ["survives", "downgraded", "partially_retracted", "retracted", "unknown_pending_audit"]


def final_verdict(gs, sub):
    """一个对象只出一个主裁决；字段级明细另存。"""
    vals = set(gs.values())
    if ST_ISSUE == gs["context"]:
        return "partially_retracted", "闸一命中真污染 ⇒ 该对象之某条证据被撤（非整体撤）"
    if ST_UNKNOWN in vals:
        return "unknown_pending_audit", "有未决之闸，不得先给裁决"
    if gs["provenance"] == ST_ISSUE and "D2_attribution_overreach" in sub:
        return "downgraded", "归因越级 ⇒ 表述须降级（证据仍在）"
    if ST_ISSUE in vals:
        return "downgraded", "有闸命中，但不撤销该对象"
    if all(v in (ST_OK, ST_NA) for v in vals):
        return "survives", "各闸或已过或不适用"
    return "unknown_pending_audit", "存在 not_auditable 之闸"


def main():
    rows = census()
    inc = [r for r in rows if r["included"]]
    exc = [r for r in rows if not r["included"]]
    for r in inc:
        gs, notes, sub = {}, {}, {}
        gs["context"], notes["context"] = gate_context(r)
        gs["lexical"], notes["lexical"] = gate_lexical(r)
        gs["atomization"], notes["atomization"] = gate_atomization(r)
        gs["provenance"], notes["provenance"], sub = gate_provenance(r)
        r["gates"], r["notes"], r["sub"] = gs, notes, sub
        r["final"], r["final_reason"] = final_verdict(gs, sub)

    from collections import Counter
    L = []
    w = L.append
    w("# 审计全集普查与分母修复（126B·上级令一〜七、九；126C 重跑）\n")
    w("> ⛔ 本册**取代** 126批 之三个数字（A 11/43｜D 29/43｜四类皆未命中 8/43）。")
    w("> 三者皆因【0 锚被当成阴性】与【四闸共用分母】而无效。\n")
    w("> ### ⭐ 126C 重跑之三处变动（本册数字已随之改写）\n")
    w("> | 变动 | 前 | 后 |")
    w("> |---|---|---|")
    w("> | 13 项 `not_auditable_missing_anchor` 补锚／重分类 | 13 | **0** |")
    w("> | N（因新登 `SW-21-MAIWEI` 而 +1） | 65 | **66** |")
    w("> | `not_auditable` 一名**本身混两件事**，已拆出 `NO_TEXTUAL_CLAIM` 一档 | — | n/a 6 |")
    w(">")
    w("> ⛔ **补锚不是补新证据**：七项 FLIP 之锚原已在 `tools/fanzhuandui.py::PAIRS`，")
    w("> 123批 建 14 栏表时**没有传过来**。⇒ 「无锚」这一诊断本身，有一半是我方资产未接线所致。")
    w("> ⚠ 六项 FLIP 由 `unknown` 转为可评价、FLIP-01 补锚后暴露其依 C卷、新登 `SW-21-MAIWEI`")
    w("> ⇒ 闸四 issue 由 41 升至 **50**；R1〜R5 落入四闸皆无 issue ⇒ `survives` 由 9 升至 **13**")
    w("> （其中 FLIP-01 反向掉出）。**升降皆非病情变化，是可评价面扩大。**")
    w("> ⛔ 并注：`survives` 之名对 R1〜R5 **误导**——四闸对不作文本断言者本就问不到什么。\n")

    # ── 令一 census ──
    w("## 一、population census（令一：N 由枚举产生，不得先写后审）\n")
    w("### 1.1 discovery query\n")
    for q in CENSUS_SPEC["discovery_query"]:
        w("- %s" % q)
    w("\n### 1.2 inclusion criteria\n")
    w("> %s\n" % CENSUS_SPEC["inclusion"])
    w("### 1.3 exclusion criteria（逐条附理由）\n")
    w("| 排除者 | 理由 |")
    w("|---|---|")
    for a, b in CENSUS_SPEC["exclusion"]:
        w("| %s | %s |" % (a, b))
    w("")
    w("### 1.4 ⭐ 结果：**N = %d**（126批 报 43，**漏 %d**）\n" % (len(inc), len(inc) - 43))
    tc = Counter(r["object_type"] for r in inc)
    w("| object_type | 数 | 126批 是否在 N 内 |")
    w("|---|---:|---|")
    NEW = {"residual_claim", "meta_rule_evidence"}
    for t, n in tc.most_common():
        w("| `%s` | %d | %s |" % (t, n, "⛔**否·本批补入**" if t in NEW else "✅是"))
    w("| **合计** | **%d** | |" % len(inc))
    w("")
    w("### 1.5 ⛔⛔ population_gap：有称引而无资产者（**不入 N**）\n")
    for r in exc:
        w("#### `%s`\n" % r["object_id"])
        w("- **source**：`%s`" % r["source_file"])
        w("- %s" % r["payload"]["note"])
        w("- **exclusion_reason**：%s\n" % r["exclusion_reason"])
    w("⇒ ⭐ **这正面回答了上级之问「63 组属不属于 candidate rule」：**")
    w("**它不属于任何东西——因为它不存在。** 121批 那次扫描**未落盘，工具未入库**。")
    w("⇒ 故令十之「恢复 63 组」在字面上**无物可恢复**；须**重新扫描**并落盘方谈得上。\n")
    w("### 1.6 上级点名之其余四问\n")
    w("| 问 | 答 |")
    w("|---|---|")
    w("| 125批 组合判定研究证据为何不在 N？ | ⛔ **126批 之漏**。本批已补入 **META-M1〜M14 共 14 个对象** |")
    w("| term mapping 如何枚举？ | 以 `rules/pulse_cells_v0.json` 之 cell 为单位（一 cell ＝ 一条 observable→object 映射），共 **12**。"
      "⚠ **V8 内尚有 113 处 `X=Y` 形之格未分类**（123批 已报），**不在本 N 内**，须另立普查 |")
    w("| 28 条历史 `validation=candidate` 何在？ | ⛔ **本批查得：现行 `rules/*.json` 中 `candidate` 为 0 条**。"
      "该 28 条出自 119–120批 之 `term_layer` 叙述，**从未落为带 ID 之资产** ⇒ 与 63 组同型之 population_gap，**已记入待办** |")
    w("| evidence/*.md 尚有 active research claims？ | ✅ 有：residual R1–R5、META M1–M14 —— **已补入**。"
      "其余 `evidence/*.md` 之内容皆为 D1/D2 对象之叙述面 |")
    w("")

    # ── 令三 每闸分母 ──
    w("---\n")
    w("## 二、每闸各自之 eligible denominator（令三）\n")
    w("⛔ **禁止继续所有 gate 统一除 N。**")
    w("⛔ `not_applicable` 与 `not_auditable_missing_anchor` **不进分母**；`unknown` 不进分子。\n")
    w("| 闸 | issue_found | eligible 分母 | 比率 | not_auditable | not_applicable | unknown |")
    w("|---|---:|---:|---|---:|---:|---:|")
    GN = {"context": "闸一 context", "lexical": "闸二 lexical",
          "atomization": "闸三 atomization", "provenance": "闸四 provenance"}
    stats = {}
    for g, gn in GN.items():
        c = Counter(r["gates"][g] for r in inc)
        elig = c[ST_ISSUE] + c[ST_OK] + c[ST_UNKNOWN]
        stats[g] = (c, elig)
        w("| %s | **%d** | **%d** | %s | %d | %d | %d |"
          % (gn, c[ST_ISSUE], elig,
             ("**%d/%d**" % (c[ST_ISSUE], elig)) if elig else "—",
             c[ST_NOANCHOR], c[ST_NA], c[ST_UNKNOWN]))
    w("")
    for g, gn in GN.items():
        c, elig = stats[g]
        ids = [r["object_id"] for r in inc if r["gates"][g] == ST_ISSUE]
        na = [r["object_id"] for r in inc if r["gates"][g] == ST_NOANCHOR]
        w("- **%s** issue：%s" % (gn, "、".join(ids) or "—"))
        if na:
            w("  - ⛔ not_auditable（无锚，**不得计为阴性**）：%s" % "、".join(na))
    w("")

    # ── 令四 A 类结论 ──
    w("---\n")
    w("## 三、闸一之结论（令四：⛔ 撤销「A 类是个案」）\n")
    hv = Counter(v for v, _ in HAND.values())
    w("| 口径 | 数 |")
    w("|---|---:|")
    w("| `confirmed_new`（人读确认之新 context truncation） | **%d** |" % hv.get("TP", 0))
    w("| `reviewed_flagged`（机器报警经人读判为 FP／已知／登记本身） | **%d** |"
      % (hv.get("FP", 0) + hv.get("KNOWN", 0) + hv.get("REGISTERED", 0) + hv.get("NO_ISSUE", 0)))
    w("| `unresolved` | **%d** |" % (hv.get("UNREAD", 0) + hv.get("PENDING", 0)))
    w("")
    w("⛔⛔ **撤销 126批 之「A 类是个案」。** 现行表述只能是：\n")
    w("> **在本批已定位且完成人读的锚中，确认 %d 例 context truncation；余为已知或假命中。**"
      % hv.get("TP", 0))
    w("> **现有审计不能估计整个工程 context truncation 的总体发生率。**\n")
    w("### ⛔ 扫描器之漏报条件（须明写）\n")
    w("| 漏报形态 | 扫描器可见？ |")
    w("|---|---|")
    w("| **未写锚**之引用（只叙述而不给 `书·偏移`） | ⛔ 不可见 |")
    w("| **根本没去检索**的材料 | ⛔ 不可见 |")
    w("| 上下文冲突**不含裁决词**（`必有错乱`／`故不释`… 之外的表达） | ⛔ 不可见 |")
    w("| 解释单元边界机器不可定者 | ⚠ 只报 `unknown`，不报内容 |")
    w("")
    w("⇒ 故本闸测得者，只是 **「已记录锚中，被裁决词触发且经人读确认之 context truncation」**，")
    w("**不是构念全集**。")
    w("")
    w("### ⭐ 并报一处扫描器之已知歧义（本批人读所得）\n")
    w("`是不对的` 一词**兼指两义**：【此**文**有误】与【此**解**有误】。")
    w("〔讲伤寒·262358〕「只要是燥屎就可以用它，**是不对的**」——胡老所否者是**读者之误会**，非文本。")
    w("⇒ 该锚判 **FP**。⛔ 机器不能分此二义，**故凡此词触发者一律须人读**。\n")

    # ── 令七 对象级裁决 ──
    w("---\n")
    w("## 四、对象级裁决（令七：一对象一主裁决，字段级只作明细）\n")
    fc = Counter(r["final"] for r in inc)
    w("| final_object_verdict | 数 | 对象 |")
    w("|---|---:|---|")
    for v in FINAL:
        ids = [r["object_id"] for r in inc if r["final"] == v]
        w("| `%s` | **%d** | %s |" % (v, fc.get(v, 0), "、".join(ids) if ids else "—"))
    w("| **合计** | **%d** | |" % len(inc))
    w("")
    w("⛔ **对照 126批**：彼报「行级 downgrades 78/90」，其中 7 行全属同一对象。")
    w("**本表为对象级，一对象只计一次。**\n")
    w("### 逐对象明细\n")
    w("| # | object_id | type | 闸一 | 闸二 | 闸三 | 闸四 | **final** |")
    w("|---:|---|---|---|---|---|---|---|")
    SH = {ST_ISSUE: "⛔issue", ST_OK: "✅ok", ST_NA: "·n/a",
          ST_NOANCHOR: "⚠无锚", ST_UNKNOWN: "？未决"}
    for i, r in enumerate(inc, 1):
        w("| %d | `%s` | %s | %s | %s | %s | %s | **%s** |"
          % (i, r["object_id"], r["object_type"],
             SH[r["gates"]["context"]], SH[r["gates"]["lexical"]],
             SH[r["gates"]["atomization"]], SH[r["gates"]["provenance"]], r["final"]))
    w("")

    # ── 令五 D 类拆四 ──
    w("---\n")
    w("## 五、闸四 provenance 之四分（令五：⛔ editor_compiled 不得计入 speaker_unresolved）\n")
    sc = Counter()
    for r in inc:
        for k in r.get("sub", {}):
            sc[k] += 1
    w("| 子类 | 对象数 | 对象 |")
    w("|---|---:|---|")
    for k in ("D1_speaker_identity_unresolved", "D2_attribution_overreach",
              "D3_source_version_unresolved", "D4_passage_authorship_unresolved"):
        ids = [r["object_id"] for r in inc if k in r.get("sub", {})]
        w("| `%s` | **%d** | %s |" % (k, len(ids), "、".join(ids) if ids else "—"))
    w("")
    w("⛔⛔ **126批 之「D speaker_unresolved 29/43」作废**——它把")
    w("**「不知道谁说的」（C卷·uncertain）** 与 **「知道是整理本但没资格说是胡老本人」（editor_compiled）**")
    w("混成一类。二者**修复方法完全不同**：前者须查书目，后者须改措辞。\n")
    w("⇒ 现行只可表述为：**provenance／attribution 问题广泛存在**，")
    w("并按四子类各自给数——**不得再写「speaker_unresolved N/43」。**\n")
    return L, inc, exc


if __name__ == "__main__":
    L, inc, exc = main()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    from collections import Counter
    print("已写 %s" % OUT)
    print("N=%d（含，126批 为 43）｜population_gap=%d" % (len(inc), len(exc)))
    for g in ("context", "lexical", "atomization", "provenance"):
        c = Counter(r["gates"][g] for r in inc)
        elig = c[ST_ISSUE] + c[ST_OK] + c[ST_UNKNOWN]
        print("  %-12s issue %d / eligible %d  (无锚 %d｜n/a %d｜未决 %d)"
              % (g, c[ST_ISSUE], elig, c[ST_NOANCHOR], c[ST_NA], c[ST_UNKNOWN]))
    print("  final:", dict(Counter(r["final"] for r in inc)))
