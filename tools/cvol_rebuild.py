#!/usr/bin/env python3
"""【C卷重构·方证库主干化】（㊵批·欠账最大项之执行件）。

事故性质（上级㊵批指出）：C卷自㉚批起**只被用作锚源**去补既有条目，
**方证库主干仍是十七批叠加物**——即「以C卷为底本」这件事**从未真正发生**。
本工具执行的是**换主干**，不是**再补锚**。

做法（四步，机械）：
  ① 以 C卷《经方理论与实践》**230 方六段**为主干骨架
     （六段＝方剂组成／用法／方解／仲景对本方证的论述／辨证要点／验案）；
  ② 引擎现有方条目逐方与之比对：**名对上的**，比 ★辨证要点 与 C卷【辨证要点】；
     **冲突处一律保留 C卷原文**，引擎写法降为「[异文·存查]」并记入冲突清单；
  ③ **名对不上的**（非C卷来源条目）逐条判来源与等级：
     A＝有《伤寒论》/《金匮》条文原文｜B＝有胡老医案｜C＝他人转述/我方推演｜**N＝无证据**；
  ④ **N 级条目移 archive/**，不留在核心执行件内。

【已知失效模式】(视角㉕)
  ① **方名匹配靠归一化字符串**。C卷有 OCR 变形、别名（「新加汤」vs「桂枝加芍药生姜
     各一两人参三两新加汤」）、加味方合写。**归一化漏一种写法即误判为"非C卷来源"**，
     结果是把有据条目错划进待清理堆。故 **N 级判定不只看名，还须过全库正文检索**（见④）。
  ② 「★与C卷辨证要点冲突」是**字面差异检测**，不是医学判断。
     多数差异是**详略不同**而非**方向相反**——故一律输出「冲突**候选**」，**由人逐条读**。
  ③ 等级 A 的判据是「引擎条目内有 [原文] 行」；若某方确有条文而引擎漏录，
     本工具会把它错判为低一级。**这是偏保守方向的错（宁可低判）**，与协议4一致。
  ④ **验案段 C卷只有 111 方有**，其余 119 方无验案——**"无验案"不等于"无证据"**，
     不得因此降级。
【弃件条件】引擎块中非方证条目者（示范/纲领/W-/病例/章节标题）一律跳过，不计入分母。
【口径】(视角㊱) 一条＝一个方证条目；体量以**行数**计；`python3 tools/cvol_rebuild.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com|^_+$")
SEC = ["方剂组成", "用法", "方解", "仲景对本方证的论述", "辨证要点", "验案"]

# ── ① 解析 C卷 230 方六段 ──────────────────────────────────────────
CL = [re.sub(r"\s+", "", x) for x in
      open(os.path.join(B, "sources", "C_jingfangliyu.txt"), encoding="utf-8", errors="ignore").read().split("\n")]
NUM = re.compile(r"^[一二三四五六七八九十百零〇]+[、.．]")
anchors = [i for i, s in enumerate(CL) if s.startswith("【方剂组成】")]

def cname(i):
    """方名行 ＝ 【方剂组成】上方最近的一条非空非页眉非段标题行。返回 (名, 行号)。"""
    for j in range(i - 1, max(0, i - 8), -1):
        s = CL[j]
        if not s or JUNK.match(s) or s.startswith("【"): continue
        return NUM.sub("", s), j
    return "", i

names = [cname(i) for i in anchors]

cvol = []
for k, i in enumerate(anchors):
    # ⚠边界：**下一方的方名行**才是本方的终点。
    # 首版误用 anchors[k+1]-8，而【辨证要点】恰在下一方名之前 → 被整段截掉，
    # 230 方只解析出 20 方。此为本工具首跑自查所得，记于此以防复发。
    end = names[k + 1][1] if k + 1 < len(anchors) else len(CL)
    body = CL[i:end]
    secs, cur = {}, None
    for s in body:
        m = re.match(r"【(.+?)】(.*)", s)
        if m and m.group(1) in SEC:
            cur = m.group(1); secs[cur] = [m.group(2)]
        elif cur and s and not JUNK.match(s):
            secs[cur].append(s)
    cvol.append(dict(name=names[k][0], line=i + 1,
                     secs={k2: "".join(v) for k2, v in secs.items()}))
cvol = [c for c in cvol if c["name"] and "辨证要点" in c["secs"]]

# ── 方名归一化 ────────────────────────────────────────────────────
def norm(s):
    s = re.sub(r"[（(].*?[)）]", "", s)
    s = re.sub(r"·.*$", "", s)
    s = NUM.sub("", s)
    s = re.sub(r"[方]$", "", s)
    s = re.sub(r"[\s、，,。：:；;【】\[\]★]", "", s)
    return s

def keys(s):
    """一名多键（**严格**）：正名 ＋ 去『方』尾 ＋ 去剂型尾。用于 C卷索引匹配。"""
    n = norm(s)
    out = {n}
    for suf in ("汤方", "散方", "丸方", "方"):
        if n.endswith(suf): out.add(n[:-len(suf)])
    for suf in ("汤", "散", "丸"):
        if n.endswith(suf): out.add(n[:-1])
    return {x for x in out if len(x) >= 2}

def keys_wide(s):
    """**剂型互换版**（汤/散/丸），**只用于全库命中计数，不用于索引匹配**。
    ⚠**第四次自查所得**：唯一一条 N 级「一物瓜蒂**散**」被判「全库 0 命中」；
      实测胡老与《金匮》原文均作「一物瓜蒂**汤**」（9 处，含金匮讲义逐字讲解）。
      **N 级判定本身也要过术语关（视角㉞）——清理器不做异写归一，删的是自己的笔误。**
    ⚠**同一批的第二个自查**：首次修正时把剂型互换**一并塞进了索引匹配**，
      结果不同方被互相误配，缺口数从 53 虚涨到 56。
      **放宽计数器 ≠ 放宽匹配器**；一次只放宽一个。"""
    out = set(keys(s))
    for x in list(out):
        for suf in ("汤", "散", "丸"):
            if x.endswith(suf):
                out |= {x[:-1] + y for y in ("汤", "散", "丸")}
    return {x for x in out if len(x) >= 2}

cidx = {}
for c in cvol:
    for k in keys(c["name"]): cidx.setdefault(k, c)

# ── ② 解析引擎方条目 ──────────────────────────────────────────────
EP = os.path.join(B, "hxs_engine_v79_full.md")
EL = open(EP, encoding="utf-8").read().split("\n")
heads = [i for i, l in enumerate(EL) if l.startswith("【")]
# ⚠**首跑事故·必读**：初版用**负向过滤**（SKIP 掉「示范/纲领/病例…」）判定方条目，
#   结果把「底本声明」「附录F～V」「Z轴系统」「方证三级权重数据库」等 25 个
#   **非方条目**判成方条目，且因它们在 C卷中无同名而全部落入 **N 级（应移 archive）**。
#   ——机械执行的话，**会把全部附录 1220 行删掉**。
#   改为**正向识别**：方条目须满足「头部有 DDL 标记 / 出处标记(·§ 或 ·金匮)」或
#   「体内有『组成：』行」。**删除类操作一律不得用负向过滤界定对象。**
POS_HEAD = re.compile(r"DDL-\d|·§\d|·金匮|·伤寒")
NEG_HEAD = re.compile(r"附录|底本|声明|轴\(|轴｜|数据库|说明|立场|编号|新增内容|注脚|"
                      r"核查|补全记录|示范|纲领|完整性标记|病例|第[〇零一二三四五六七八九十]+章|"
                      r"W-\d|通则化|语料C\d+案|R0·|^[LA]\d|^[AB]侧|速查")

ent, rejected = [], []
for k, i in enumerate(heads):
    end = heads[k + 1] if k + 1 < len(heads) else len(EL)
    head = EL[i]
    nm = re.match(r"【(.+?)】", head)
    if not nm: continue
    raw = nm.group(1)
    body = "\n".join(EL[i:end])
    ok = (POS_HEAD.search(head) or re.search(r"^组成：", body, re.M)) and not NEG_HEAD.search(raw)
    rec = dict(raw=raw, head=head, line=i + 1, nlines=end - i, body=body)
    (ent if ok else rejected).append(rec)

# ── ③ 匹配 ───────────────────────────────────────────────────────
def star(e):
    """★辨证要点**只取标题行**。
    ⚠首跑事故：原从 body 全文取 `★(.+?)★`，抓到的是正文里的
    `主症★[已换源·降为仲景条文谱…[★换源·X-0]]`，**156 条冲突候选中大半是这个抽取失败**，
    不是真冲突。**抽取失败与内容冲突必须分开计数。**"""
    m = re.search(r"★(.+?)★", e["head"])
    if m: return m.group(1)
    m = re.search(r"^主症★[^：]*：(.+)$", e["body"], re.M)
    return m.group(1)[:120] if m else ""

matched, unmatched = [], []
for e in ent:
    hit = None
    # ⚠**第五次自查**：原按 `for k in keys(...)` 迭代 **set**，顺序不定——
    #   「四逆散」有时先撞上短键「四逆」而误配到**四逆汤**，导致同一份数据
    #   两次运行得出 53 / 54 两个缺口数。**结果不可复现的工具不得用于出清单。**
    #   → 改**最长键优先**（最具体者先匹配），结果确定。
    for k in sorted(keys(e["raw"]), key=len, reverse=True):
        if k in cidx: hit = cidx[k]; break
    if hit: e["c"] = hit; matched.append(e)
    else: unmatched.append(e)

# ── ④ 冲突候选：★ vs C卷辨证要点（字面差异，非医学判断）──────────
def toks(s):
    """滑动 2-gram。
    ⚠首跑事故：原用 `findall(r"[一-鿿]{2,4}")`，它取的是**不重叠的最长块**，
    「热利下重」整串成**一个**词元，与C卷「热痢下重」（利/痢一字之差）重合率算作 0%
    ——**全部 209 条重合率都是 0%**，122 条「冲突候选」是**度量坏了**，不是内容冲突。
    改滑动 2-gram 后才可比。**分母全为 0 的指标必须当场判废，不得据以出清单。**"""
    z = re.sub(r"[^一-鿿]", "", s)
    return {z[i:i + 2] for i in range(len(z) - 1)}

# ⚠**第三次自查所得（决定性）**：引擎已有 `[★换源·X-0]` 规程——
#   「本方判定★以③C卷辨证要点原文为准；条目行原★降为[仲景条文谱]保留不删」。
#   凡已挂该规程者，其标题★与C卷的差异是**按设计保留的**，**不是未决冲突**。
#   若不分开计，会把 193 条**已决**的算进冲突清单，虚报欠账规模。
#   → **冲突清单只计未换源者**；已换源者单独计为「已决·按设计保留异文」。
XY = re.compile(r"\[★换源·X-0\]")
conf, settled = [], []
for e in matched:
    s = star(e); cy = e["c"]["secs"].get("辨证要点", "")
    if not s or not cy: continue
    ts, tc = toks(s), toks(cy)
    if not ts: continue
    ov = len(ts & tc) / len(ts)
    e["ov"] = ov
    if XY.search(e["body"]): settled.append(e); continue
    if ov < 0.34: conf.append((e, s, cy, ov))
conf.sort(key=lambda x: x[3])
# 口径（视角㊱）：以**全部 matched** 为分母，不因缺★/缺C卷要点而漏计。
sourced   = [e for e in matched if XY.search(e["body"])]
unsourced = [e for e in matched if not XY.search(e["body"])]
assert len(sourced) + len(unsourced) == len(matched)

# ── ⑤ 非C卷条目定级 ──────────────────────────────────────────────
BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读", "ocr_解读张仲景医学.txt"), ("传真系", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("汤液经方系", "ocr_冯世纶2005汤液经方系_书名待定.txt"),
         ("伤寒论传真", "传真_伤寒论传真.txt"), ("金匮传真", "传真_金匮要略传真.txt"),
         ("中国汤液方证", "汤液_中国汤液方证.txt")]
T = "".join(JUNK.sub("", re.sub(r"\s+", "", open(os.path.join(B, "sources", f), encoding="utf-8",
            errors="ignore").read())) for f in BOOKS if os.path.exists(os.path.join(B, "sources", f)))

def grade(e):
    b = e["body"]
    if re.search(r"^\[原文\]", b, re.M): return "A", "引擎内有条文原文行"
    if re.search(r"★HXS验案|语料C\d+案|验案", b): return "B", "有胡老医案"
    n = norm(e["raw"])
    hits = T.count(n) if len(n) >= 2 else 0
    if hits == 0 and len(n) >= 2:
        for k in keys_wide(e["raw"]):
            hits = max(hits, T.count(k))
    if hits > 0: return "C", "无条文无医案，但胡老书正文命中 %d 处" % hits
    return "N", "**全库 0 命中**：无C卷、无条文、无医案、七本书正文亦无"

for e in unmatched:
    e["grade"], e["why"] = grade(e)
NG = [e for e in unmatched if e["grade"] == "N"]

# ── 输出 ─────────────────────────────────────────────────────────
tot_lines = len(EL)
n_ent_lines = sum(e["nlines"] for e in ent)
ngl = sum(e["nlines"] for e in NG)

L = ["# C卷重构·方证库主干化（㊵批）", "",
     "> 生成：`tools/cvol_rebuild.py`（文件头含【已知失效模式】【弃件条件】【口径】）。", "",
     "> **本批执行的是「换主干」，不是「再补锚」。** 上级㊵批指出：C卷自㉚批起只被",
     "> 用作锚源去补既有条目，方证库主干仍是**十七批叠加物**——「以C卷为底本」**从未真正发生**。", "",
     "## 〇、口径与体量", "",
     "| 项 | 数 |", "|---|---|",
     "| C卷解析出的方（含六段·辨证要点齐备） | **%d** |" % len(cvol),
     "| 引擎方证条目（已剔除示范/纲领/病例等非方条目） | **%d** |" % len(ent),
     "| 其中**与C卷对得上名**者 | **%d**（%.0f%%） |" % (len(matched), 100 * len(matched) / max(1, len(ent))),
     "| 其中**非C卷来源**者 | **%d** |" % len(unmatched),
     "| 引擎总行数 | %d |" % tot_lines,
     "| 方条目占用行数 | %d（%.0f%%） |" % (n_ent_lines, 100 * n_ent_lines / tot_lines), "",
     "> ⚠**C卷 %d 方中有 %d 方引擎尚无对应条目**——这是**缺口**，不是冗余，另列于第三节。"
     % (len(cvol), len(cvol) - len({id(e["c"]) for e in matched})), "",
     "---", "", "## 一、冲突清单（★ vs C卷【辨证要点】·**字面差异检测，非医学判断**）", "",
     "> 判据：★的词元有 **<34%** 出现在 C卷【辨证要点】中者列为冲突候选。",
     "> **多数差异是详略不同而非方向相反**——故称「候选」，**须人逐条读**。",
     "> **处置定则：冲突处一律保留 C卷原文**，引擎写法降为 `[异文·存查]`。", "",
     "| 状态 | 条数 |", "|---|---|",
     "| 已挂 `[★换源·X-0]` 规程（★以C卷为准，原★按设计降为[仲景条文谱]保留） | **%d** |" % len(sourced),
     "| **未换源**（C卷六段未挂，主干仍是十七批叠加物） | **%d** |" % len(unsourced),
     "| 其中★与C卷辨证要点**字面重合 <34%%** ＝ **未决冲突候选** | **%d** |" % len(conf), "",
     "> ⚠**本表第三次自查订正**：初版把 %d 条**已换源**者一并计入冲突，虚报欠账规模。" % len(sourced),
     "> （其中 %d 条因缺★或缺C卷要点而无法比对，已计入未换源分母、不计入冲突候选。）"
     % (len(unsourced) - len([1 for e in unsourced if star(e) and e["c"]["secs"].get("辨证要点")])),
     "> 已换源者的★差异是**按规程保留的**（原★降为[仲景条文谱]，不删），**不是未决冲突**。", "",
     "| # | 方 | 引擎★ | C卷【辨证要点】(截) | 词元重合 |", "|---|---|---|---|---|"]
for k, (e, s, cy, ov) in enumerate(conf[:60], 1):
    L.append("| %d | **%s** | %s | %s | %.0f%% |" % (
        k, e["c"]["name"], s[:46].replace("|", "／"), cy[:76].replace("|", "／"), 100 * ov))

L += ["", "---", "", "## 二、非C卷来源条目·来源与等级", "",
      "> A＝有《伤寒论》/《金匮》条文原文｜B＝有胡老医案｜C＝胡老书正文有但无条文无医案｜",
      "> **N＝无证据（全库 0 命中）**。", ""]
gc = Counter(e["grade"] for e in unmatched)
L += ["| 等级 | 条数 | 处置 |", "|---|---|---|",
      "| A | %d | 保留，标 `[来源:条文·非C卷]` |" % gc["A"],
      "| B | %d | 保留，标 `[来源:医案·非C卷]` |" % gc["B"],
      "| C | %d | 保留但**降级**，标 `[来源:胡老书正文·无条文无医案]` |" % gc["C"],
      "| **N** | **%d** | **移 archive/** |" % gc["N"], ""]

L += ["### N 级移出清单（**无C卷、无条文、无医案、七本书正文 0 命中**）", ""]
if NG:
    L += ["| # | 条目 | 引擎行 | 占行 |", "|---|---|---|---|"]
    for k, e in enumerate(sorted(NG, key=lambda x: -x["nlines"]), 1):
        L.append("| %d | `%s` | L%d | %d |" % (k, e["raw"].replace("|", "／"), e["line"], e["nlines"]))
    L += ["", "**合计 %d 条／%d 行。**" % (len(NG), ngl)]
else:
    L += ["**0 条。**", "",
          "> ⚠这个 0 **不是「全部有据」的证明**：等级 C 有 %d 条，其判据只是「胡老书正文命中过这个方名」，"
          % gc["C"],
          "> **命中一次也算命中**。真正的弱项在 C 级，不在 N 级——见第四节。"]

L += ["", "---", "", "## 三、C卷有而引擎无（**缺口**）", ""]
got = {id(e["c"]) for e in matched}
miss = [c for c in cvol if id(c) not in got]
L += ["**%d 方。**" % len(miss), "", "| # | C卷方名 | C卷行 | 辨证要点(截) |", "|---|---|---|---|"]
for k, c in enumerate(miss[:80], 1):
    L.append("| %d | **%s** | L%d | %s |" % (k, c["name"], c["line"],
             c["secs"].get("辨证要点", "")[:70].replace("|", "／")))

L += ["", "---", "", "## 四、等级 C 条目（真正的弱项）", "",
      "> 这些条目**既无条文、又无医案**，只是方名在胡老书里出现过。",
      "> 按证据分级，它们是**我方或他人的叠加物**，**不是胡老方证库的一部分**。", "",
      "| # | 条目 | 行 | 占行 | 命中 |", "|---|---|---|---|---|"]
CG = sorted([e for e in unmatched if e["grade"] == "C"], key=lambda x: -x["nlines"])
for k, e in enumerate(CG[:60], 1):
    L.append("| %d | `%s` | L%d | %d | %s |" % (k, e["raw"].replace("|", "／"), e["line"],
             e["nlines"], e["why"].split("命中")[-1] if "命中" in e["why"] else ""))
L += ["", "**C 级合计 %d 条／%d 行。**" % (len(CG), sum(e["nlines"] for e in CG))]

open(os.path.join(B, "term_layer", "C卷重构_主干化.md"), "w", encoding="utf-8").write("\n".join(L))
json.dump(dict(cvol=len(cvol), ent=len(ent), matched=len(matched),
               grades=dict(gc), conflicts=len(conf), miss=len(miss),
               N=[e["raw"] for e in NG], C=[e["raw"] for e in CG]),
          open(os.path.join(B, "term_layer", "_cvol_rebuild.json"), "w"), ensure_ascii=False, indent=1)

print("C卷方 %d ｜引擎方条目 %d ｜对上名 %d ｜非C卷 %d" % (len(cvol), len(ent), len(matched), len(unmatched)))
print("非C卷等级：", dict(gc))
print("冲突候选 %d 条｜C卷有而引擎无 %d 方" % (len(conf), len(miss)))
print("N级 %d 条/%d 行｜C级 %d 条/%d 行" % (len(NG), ngl, len(CG), sum(e["nlines"] for e in CG)))
print("引擎总行 %d ｜方条目占 %d 行 (%.0f%%)" % (tot_lines, n_ent_lines, 100 * n_ent_lines / tot_lines))
