#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_text_critical_gate.py —— text-critical gate 回归（125批·上级令八、令十⑨）

⛔ 硬规则（上级令一）：
   **胡老明确判为错简、错乱、传抄误并拒绝解释之文本，
     不得作为胡老体系规则的正证或反例；只能作为 text-critical evidence 保存。**

本器实装三件：
  G1 闸门表本身之自洽（`suspected_corruption`／`rejected_by_hu` 只许 evidence_only）
  G2 已登记之文本，其 allowed_roles 须与闸门表一致
  G3 ⭐**反向回归**：§214 不得再出现在任何 cell／翻转组之【反例】或【scope_split 依据】中
     —— 这一款若变红，即说明 124批 那个错误复活了
"""
import json
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(B, "schema", "text_critical_v0.json"), encoding="utf-8"))
D = json.load(open(os.path.join(B, "rules", "text_critical_v0.json"), encoding="utf-8"))
GATE = S["GATE"]
P = {p["passage_id"]: p for p in D["passages"]}

FAIL = []


def ck(name, cond, why=""):
    print(("✅PASS " if cond else "⛔FAIL ") + name + ("" if cond else "   " + why))
    if not cond:
        FAIL.append(name)


# ── G1 闸门表自洽 ─────────────────────────────────────────
for st in ("suspected_corruption", "rejected_by_hu", "emended_by_hu", "disputed_cross_source"):
    ck("G1 闸门·%s 只许 evidence_only" % st,
       GATE[st] == ["text_critical_evidence_only"], str(GATE[st]))
for st in ("suspected_corruption", "rejected_by_hu", "emended_by_hu", "disputed_cross_source",
           "variant", "editorial_reconstruction"):
    ck("G1 闸门·%s 不得 confirm/falsify/scope_split" % st,
       not ({"confirm", "falsify", "scope_split"} & set(GATE[st])), str(GATE[st]))
ck("G1 闸门·只有 accepted 可 falsify",
   [k for k, v in GATE.items() if "falsify" in v] == ["accepted"])
ck("G1 硬规则已写入 schema", "拒绝解释" in S["HARD_RULE"])

# ── G2 已登记文本之角色须合闸 ─────────────────────────────
ck("G2 首批样本 ≥2 条（令八指定 §214、§25 洪大）", len(P) >= 2)
for pid, p in P.items():
    st = p["text_status"]
    ck("G2 %s 之 text_status 合法" % pid, st in S["definitions"]["text_status"]["enum"])
    ck("G2 %s 之 allowed_roles 合闸" % pid,
       set(p["allowed_roles"]) <= set(GATE[st]),
       "%s ⊄ %s" % (p["allowed_roles"], GATE[st]))
    # ⚠ 126L 订正命名：本项**只证字段存在**，⛔ 不证归属。归属由 G4 查。
    ck("G2 %s 之 verdict_source／verdict_anchor 字段非空（⛔ 只证字段存在，不证归属）" % pid,
       bool(p.get("verdict_source")) and bool(p.get("verdict_anchor")))

ck("⭐§214 已登记为 rejected_by_hu", P["SW-214"]["text_status"] == "rejected_by_hu")
ck("⭐§214 之判定引了『故不释』",
   "故不释" in P["SW-214"]["verdict_source"])
ck("⭐§214 留有误用记录（防复用）", bool(P["SW-214"].get("misuse_history")))

# ── G3 ⭐反向回归：§214 不得再被当反例用 ───────────────────
def _scan(path, keys=("counterexamples", "counterexample_search", "competitor_set",
                      "falsifier", "decision", "process_stage", "state_transition")):
    """在研究层与规则层里找『214』之实际【使用】，排除 text_critical 档本身。"""
    hits = []
    raw = open(path, encoding="utf-8").read()
    for m in re.finditer(r"§?21[34]\b|§214", raw):
        w = raw[max(0, m.start() - 220): m.start() + 220]
        # 只在【反例/scope_split 依据】语境中算命中
        if any(k in w for k in ("反例", "counterexample", "scope_split", "falsif")):
            hits.append((m.start(), w[:120].replace("\n", " ")))
    return hits


targets = [os.path.join(B, "rules", "pulse_cells_v0.json"),
           os.path.join(B, "tools", "jiegou_buqi_123.py"),
           os.path.join(B, "evidence", "反例攻击_四组_124批.md"),
           os.path.join(B, "evidence", "FLIP-03_FLIP-08_重编码_124批.md")]
bad = []
for t in targets:
    if not os.path.exists(t):
        continue
    raw = open(t, encoding="utf-8").read()
    # ⛔ 初版以裸 `214` 为式 ⇒ 命中锚号里的数字片段（如 `C卷·22147`）而假红。
    #   **这与 124批 我把令一断言写得过宽是同一族错误：检测器写得比要禁的东西宽。**
    #   现只认【条号形态】：§214 / 第214条 / 214条。
    for m in re.finditer(r"(?:§|第)214(?:条)?|\b214条", raw):
        w = raw[max(0, m.start() - 260): m.start() + 260]
        if any(k in w for k in ("反例", "scope_split", "counterexample")):
            # 允许出现在【撤销说明】中
            if any(k in w for k in ("撤", "已废", "不得作", "rejected_by_hu",
                                    "错乱", "故不释", "125批")):
                continue
            bad.append((os.path.basename(t), m.start(), w[:100].replace("\n", " ")))
ck("⭐⭐G3 §214 不再被当作【活】反例／scope_split 依据", not bad,
   "仍在用：%s" % bad[:3])

# ── G4 ⭐⭐ HARD_RULE_2 之检查（126M 重写）──────────────────────────
#
# ⛔⛔ 126M 撤回 126L 之表述与实现。上级线直接调用 126L 之函数，得两个反向样本：
#        A·讲伤寒·389357（已知归属未定之末篇）→ 通过   ← 应不通过
#        A·讲伤寒·不存在（无有效位置）        → 通过   ← 应不通过
#      Code 复核并发现**比所报更宽**：裸书名「讲伤寒」（完全无偏移）亦通过。
#      ⇒ 126L 之 G4 实际验证的是「**锚字符串里含某个书名**」，
#        **既未验证锚可定位，也未验证段落归属**。
#      ⚠ 而 389357 正是 Code 自己在 126E 立 G 类（file_level_attribution_masking_
#        passage_level）时认定之末篇锚 —— **我写的闸门重犯了它要防的错**。
#      ⇒ ⛔ **「机器可证成之胡老归因 N 条」这一表述，撤回。**
#
# ⭐⭐ 126M 之设计原则（依上级令一）：
#      **本检查只能【排除】，永远不能【证成】。**
#      因为「锚落在讲课分区」只是段落归属之**必要非充分**条件：
#      同一分区内仍可有引录、转述、他人插话、整理者按语。
#      ⇒ 故本检查之输出只有三种：not_applicable｜disqualified｜not_disqualified。
#      ⛔ **没有 verified 这一档**，⛔ 任何调用方不得把 not_disqualified 读作已验证。
#      ⇒ 凡 ASSERTS_HU 之条目，**无论检查结果如何，一律须人工核验**。
#
# 本检查实际做的三件事（⛔ 仅此三件）：
#   ①锚是否可解析出「书名＋数值偏移」        ⇒ 否则 disqualified(anchor_unparseable)
#   ②该偏移是否在该书语料长度之内            ⇒ 否则 disqualified(offset_out_of_range)
#   ③该偏移落入之体裁分区 speaker 是否 hu_lecture
#                                            ⇒ 否则 disqualified(non_lecture_zone)
SPEAKER = {"讲伤寒": "hu_lecture", "讲金匮": "hu_lecture", "C卷": "uncertain",
           "解读": "editor_compiled", "传真系": "editor_compiled",
           "病位类方解": "editor_compiled", "汤液经方系": "editor_compiled",
           "中国汤液方证": "editor_compiled", "伤寒论传真": "editor_compiled",
           "金匮要略传真": "editor_compiled", "临床家": "editor_compiled",
           "带教": "editor_compiled_feng"}
# 这三个值**断言了「胡老本人」作过文本裁决**；disputed_cross_source 不作此断言。
ASSERTS_HU = {"emended_by_hu", "rejected_by_hu", "suspected_corruption"}

sys.path.insert(0, os.path.join(B, "tools"))
from reading_ledger import GENRE_SPLITS          # noqa: E402  ⭐ 分区表之唯一来源
try:
    from corpus_guard import load_one            # noqa: E402  统一入口（闸门9 第六款）
    _CORPUS_OK = True
except Exception as _e:                          # ⛔ 取不到语料时不得假装查过
    _CORPUS_OK = False
    _CORPUS_WHY = str(_e)

_LEN_CACHE = {}


def book_len(book):
    """该书 cleaned 语料之长度；⛔ 取不到则返回 None（⛔ 不得当作 0 或 ∞）。"""
    if book not in _LEN_CACHE:
        if not _CORPUS_OK:
            _LEN_CACHE[book] = None
        else:
            try:
                _LEN_CACHE[book] = len(load_one(book))
            except Exception:
                _LEN_CACHE[book] = None
    return _LEN_CACHE[book]


def zone_of(book, off):
    """偏移所落之体裁分区。⛔ 该书未登记分区表者返回 None ⇒ 不得推定为讲课正文。"""
    for z in GENRE_SPLITS.get(book, []):
        if z["start"] <= off < z["end"]:
            return z
    return None


# 锚之形态：`A·<书名>·<数字>`，可带 `–终点`、`区`、附注
_ANCHOR_RE = re.compile(r"(?:^|[·|｜;；,，\s])([\u4e00-\u9fa5A-Za-z0-9]+)·(\d+)")


def parse_anchors(anchor):
    """从锚串析出全部 (书名, 偏移)。⛔ 只认已知书名；未知书名不入。"""
    out = []
    for bk, off in _ANCHOR_RE.findall(anchor or ""):
        if bk in SPEAKER:
            out.append((bk, int(off)))
    return out


def attribution_check(passage):
    """HARD_RULE_2 之**可执行部分**。

    返回 (verdict, why)，verdict ∈ {not_applicable, disqualified, not_disqualified}。
    ⛔⛔ **永不返回 verified**——本检查不能证成段落归属，只能排除。
    """
    st = passage.get("text_status")
    if st not in ASSERTS_HU:
        return "not_applicable", "本值不断言胡老本人之裁决"
    anchor = passage.get("verdict_anchor") or ""
    pairs = parse_anchors(anchor)
    if not pairs:
        return "disqualified", "anchor_unparseable：析不出『已知书名·数值偏移』 ← %r" % anchor
    reasons, live = [], []
    for bk, off in pairs:
        n = book_len(bk)
        if n is None:
            reasons.append("%s·%d：语料长度取不到（%s）⇒ 无法核位置"
                           % (bk, off, "corpus_guard 不可用" if not _CORPUS_OK else "载入失败"))
            continue
        if not (0 <= off < n):
            reasons.append("%s·%d：offset_out_of_range（该书长 %d）" % (bk, off, n))
            continue
        z = zone_of(bk, off)
        if z is None:
            reasons.append("%s·%d：该书无体裁分区表 ⇒ ⛔ 不得推定为讲课正文" % (bk, off))
            continue
        if z["speaker"] != "hu_lecture":
            reasons.append("%s·%d：落入 %s（speaker=%s）⇒ non_lecture_zone"
                           % (bk, off, z["genre"], z["speaker"]))
            continue
        live.append("%s·%d(%s)" % (bk, off, z["genre"]))
    if live:
        return "not_disqualified", ("锚落在讲课分区：%s ⛔ 这是必要非充分条件，"
                                    "⛔ 不证明段落归属" % live)
    return "disqualified", "；".join(reasons)


# ⭐⭐ 控样本：含上级线 126M 给出之**两个反向样本**（⛔ 必须判 disqualified）
_CTRL = [
    # (名称, passage, 期望 verdict)
    ("负控1·归属未定之整理本而标 emended_by_hu",
     {"text_status": "emended_by_hu", "verdict_anchor": "A·C卷·29360"}, "disqualified"),
    ("⭐负控2·上级样本 A·讲伤寒·389357（末篇 appended_article，speaker=unresolved）",
     {"text_status": "emended_by_hu", "verdict_anchor": "A·讲伤寒·389357"}, "disqualified"),
    ("⭐负控3·上级样本 A·讲伤寒·不存在（无有效位置）",
     {"text_status": "emended_by_hu", "verdict_anchor": "A·讲伤寒·不存在"}, "disqualified"),
    ("负控4·Code 自查补：裸书名，完全无偏移",
     {"text_status": "emended_by_hu", "verdict_anchor": "讲伤寒"}, "disqualified"),
    ("负控5·Code 自查补：偏移超出语料长度",
     {"text_status": "emended_by_hu", "verdict_anchor": "A·讲伤寒·99999999"}, "disqualified"),
    ("负控6·Code 自查补：末篇起点前一字（387512）须【不】被排除，起点（387513）须被排除",
     {"text_status": "emended_by_hu", "verdict_anchor": "A·讲伤寒·387513"}, "disqualified"),
    ("正控1·同一证据撤下确定归因（disputed_cross_source）⇒ 不适用",
     {"text_status": "disputed_cross_source", "verdict_anchor": "A·C卷·29360"}, "not_applicable"),
    ("正控2·锚在讲课正文区 ⇒ 不被排除（⛔ 仍非已验证）",
     {"text_status": "suspected_corruption", "verdict_anchor": "A·讲伤寒·156700"}, "not_disqualified"),
    ("正控3·边界·末篇起点前一字 ⇒ 不被排除",
     {"text_status": "suspected_corruption", "verdict_anchor": "A·讲伤寒·387512"}, "not_disqualified"),
]
if not _CORPUS_OK:
    ck("⛔G4 语料不可用 ⇒ 位置类检查无法执行（⛔ 不得当作通过）", False, _CORPUS_WHY)
for nm, smp, want in _CTRL:
    got, why = attribution_check(smp)
    ck("⭐G4-控 %s ⇒ 须判 %s" % (nm, want), got == want, "实得 %s：%s" % (got, why))

# ⭐ 跑在真实数据上
_disq, _live = [], []
for pid, p in sorted(P.items()):
    v, why = attribution_check(p)
    if v == "not_applicable":
        continue
    (_disq if v == "disqualified" else _live).append((pid, why))
    # ⛔ 无论 disqualified 还是 not_disqualified，皆须带 attribution_review 明报
    ck("⭐G4 %s 之胡老归因未经证成 ⇒ 须带 attribution_review 明报（⛔ 不得静默）" % pid,
       isinstance(p.get("attribution_review"), dict)
       and p["attribution_review"].get("status") == "pending_manual_review", why)

print("\n⚠ G4 之能力边界（⛔ 照抄，勿改写）：")
print("   本检查**只能排除，不能证成**。⛔ 无『机器可证成』一档。")
print("   机器可**排除**者 %d 条：%s" % (len(_disq), "｜".join(p for p, _ in _disq) or "无"))
print("   机器**未能排除**者 %d 条：%s" % (len(_live), "｜".join(p for p, _ in _live) or "无"))
print("   ⛔ 『未能排除』≠ 已验证：锚落在讲课分区只是**必要非充分**条件，")
print("      同一分区内仍可有引录、转述、他人插话、整理者按语。")
print("   ⇒ ⭐ 上列 %d 条 **全部**须人工核验；attribution_review 只表示**缺口已显露**。"
      % (len(_disq) + len(_live)))

# ── G5 ⭐⭐ 阻止未验证归因被下游当作确定事实（126M·上级令一末句）──────
#   上级令：「带 attribution_review 只能表示缺口已显露，
#            不能让下游继续把旧确定性归因当已验证事实。」
#   ⇒ 本节扫现役资产，凡引这些 passage_id 者，须同处带未验证标记。
_UNVERIFIED = [pid for pid, _ in _disq + _live]
_SCAN_DIRS = ["rules", "V8", "term_layer", "tools", "runtime", "compiler"]
_MARKS = ("attribution_review", "未验证", "未经证成", "待人工核验", "pending_manual_review",
          "归属未定", "disputed_cross_source", "text_status_history")
_naked = []
for _d in _SCAN_DIRS:
    _root = os.path.join(B, _d)
    for _dp, _, _fns in os.walk(_root) if os.path.isdir(_root) else []:
        for _fn in _fns:
            if not _fn.endswith((".md", ".json", ".py")):
                continue
            _fp = os.path.join(_dp, _fn)
            if os.path.relpath(_fp, B) in ("rules/text_critical_v0.json",):
                continue        # 登记档本身
            try:
                _raw = open(_fp, encoding="utf-8").read()
            except Exception:
                continue
            for _pid in _UNVERIFIED:
                for _m in re.finditer(re.escape(_pid), _raw):
                    _w = _raw[max(0, _m.start() - 400): _m.start() + 400]
                    if not any(k in _w for k in _MARKS):
                        _naked.append((os.path.relpath(_fp, B), _pid))
ck("⭐⭐G5 未验证之胡老归因，下游引用处皆带未验证标记（⛔ 不得裸引）",
   not _naked, "裸引：%s" % _naked[:5])


print("\n失败 %d 项%s" % (len(FAIL), ("：" + "｜".join(FAIL)) if FAIL else ""))
sys.exit(1 if FAIL else 0)
