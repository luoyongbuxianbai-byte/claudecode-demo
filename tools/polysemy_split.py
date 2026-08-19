#!/usr/bin/env python3
"""【多义词分野】127 词的三分：伪多义／真多义·已有分野／真多义·分野未定（㊵批·末位待办）。

㉗批冻结第4条立「同词不等义」，㉘批实测检出 **127 个原词多义**。
但 **127 这个数不能直接当待办量**——本工具先过闸门再分野。

三分口径：
  ① **伪多义·指代类**：「本方／本条所述／它是」等**指示词**，其"多义"是指代对象不同，
     **不是词义不同**。剔除，不入待办。
  ② **伪多义·抽取噪声**：「底下／一个／十二／一升／治十二／可见肺胀即／首段」等——
     定义句抽取器抓到了**主语前面那一截**（与 `locus_explicit` 首跑同型失误）。剔除。
  ③ **真多义**：其中再分「**已有分野**」（引擎内已写明分野token）与「**分野未定**」。

【已知失效模式】(视角㉕)
  ① 闸门是**词表＋句法特征**，人工列的。**误剔一个真多义词，它就永远不在待办里了**
     ——这是**不可见的漏**（视角㉚），故弃件一律列出词形备查，不静默丢弃。
  ② 「引擎内已写明分野」靠**在引擎全文搜「分野token」＋该词共现**判定；
     引擎用别的措辞写了分野者会被判为"未定"（**偏保守，宁可多列待办**）。
  ③ 本工具**不判断哪个义项对**，只做**分类与计数**。分野内容须人读原文定。
【弃件条件】词长 <2 字、或纯数量词/序数词者弃。
【口径】(视角㊱) 一条＝一个原词；`python3 tools/polysemy_split.py` 复跑。
"""
import re, os, json
from collections import Counter

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(B, "term_layer", "一词多义实测表.md")
rows = [l for l in open(SRC, encoding="utf-8") if l.startswith("| **") and "｜" in l]
words = []
for l in rows:
    m = re.match(r"\| \*\*(.+?)\*\* \| (\d+) \| (\d+)%", l)
    if m: words.append((m.group(1), int(m.group(2)), int(m.group(3))))

# ── 闸门① 指代类 ──
IND = re.compile(r"^(本方|该方|此方|上方|前方|本条|此条|本证|该证|本药|本来|它是|它|其|"
                 r"这个|那个|以上|上述|首段|本条所述|以后|并非|一是|一个)$")
# ── 闸门② 抽取噪声：数量/序数、以「即/则/故/可见」等连词收尾或起首、长句残片 ──
NUM = re.compile(r"^[一二三四五六七八九十百千零〇两几数\d]+(升|两|枚|钱|分|克|日|个|条|段)?$")
FRAG = re.compile(r"(即|则|故|可见|所以|因为|如果|虽|但)$|^(可见|所以|因为|如果|虽|但|治)|"
                  r"^.{7,}$")

E = open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read()
# ── 闸门③ **正向识别**（首跑后补）──────────────────────────────────
# ⚠首跑事故：只用负向词表，19 词被剔而 91 词进待办，其中「意思／法子／第二个／
#   老师明确／总而言之／在这他」等**口语转录噪声**全部穿过——与「讲座类书口语转录
#   被当定义」（弃件闸门弃782条那次）**同型第二次**。
#   → 改**正向识别**：真多义词须是**引擎方证行里实际在用的医学词**。
#   与 `cvol_rebuild` 同一条教训：**界定"该保留什么"要用正向判据，不要靠列举噪声。**
MED_LINES = [l for l in E.split("\n")
             if re.match(r"^(主症|或然症|反义|鉴别|▶T触发|▶S)", l) or "★" in l]
MED = "\n".join(MED_LINES)
# ⚠**第二次自查·反向**：首次补正向闸门时改用「两侧成边界」判子串，
#   结果把**亡阳／心下／津液／厥阴病／热结膀胱／循衣摸床／郑声／里急**等**真医学词**
#   剔了——它们在方证行里本就作复合词的一截出现（「心下」在「心下痞硬」内）。
#   **这正是本工具文件头所警告的「不可见的漏」，我自己当场犯了一次。**
#   → 边界规则撤回，改回**子串命中 ＋ 元话语停用表**（噪声是有限可列的，术语不是）。
META = re.compile(r"^(主要|意思|明确|老师明确|胡老师|中医|法子|总而言之|应当|并不是|"
                  r"在说|在这他|它就|它这里|他本来|他这个方剂|大如|有的|个药|个地方|"
                  r"第二个|第三个|底下|根本|服药当天|的机会|看变白浊|一发作|初得|"
                  r"则卫气不行|表无他病|表证未罢而|脉微是|阳也|阳就|水气者|按之没|"
                  r"外气怫郁|久伤取冷|本方证)$")

def gate(w):
    if IND.match(w): return "伪·指代"
    if NUM.match(w): return "伪·数量"
    if FRAG.search(w): return "伪·抽取噪声"
    if len(w) < 2: return "伪·过短"
    if META.match(w): return "伪·元话语/口语"
    if w not in MED: return "伪·非医学词(引擎方证行内 0 命中)"
    return None

def has_split(w):
    """引擎内是否已为该词写明分野。判据：同一行内该词与「分野」二字共现。"""
    for line in E.split("\n"):
        if w in line and "分野" in line: return line.strip()[:110]
    return None

real, fake = [], []
for w, n, ov in words:
    g = gate(w)
    if g: fake.append((w, n, g)); continue
    real.append((w, n, ov, has_split(w)))

done = [r for r in real if r[3]]
todo = [r for r in real if not r[3]]

L = ["# 多义词分野·三分表（㊵批）", "",
     "> 生成：`tools/polysemy_split.py`（文件头含【已知失效模式】【弃件条件】【口径】）。", "",
     "## 〇、127 不是待办量", "",
     "| 类 | 数 | 说明 |", "|---|---|---|",
     "| **伪多义**（指代词／数量词／抽取噪声） | **%d** | 剔除，不入待办 |" % len(fake),
     "| **真多义·引擎内已写明分野** | **%d** | 已闭合 |" % len(done),
     "| **真多义·分野未定** | **%d** | ← **这才是待办量** |" % len(todo),
     "| 合计 | %d | |" % len(words), "",
     "> ⚠**伪多义中「抽取噪声」一类与 `locus_explicit` 首跑同型**：",
     "> 定义句抽取器抓到的是**主语前面那一截**（「治十二」「可见肺胀即」「大病差后即」）。",
     "> **同一个抽取缺陷在两个工具里各犯了一次**——记为工具族共性缺陷，不是单点失误。", "",
     "---", "", "## 一、**真多义·分野未定（待办 %d 词）**" % len(todo), "",
     "| # | 原词 | 义项数 | 最低重合 |", "|---|---|---|---|"]
for k, (w, n, ov, _) in enumerate(sorted(todo, key=lambda x: -x[1]), 1):
    L.append("| %d | **%s** | %d | %d%% |" % (k, w, n, ov))

L += ["", "---", "", "## 二、真多义·已写明分野（%d 词·已闭合）" % len(done), "",
      "| 原词 | 义项数 | 引擎内分野行 |", "|---|---|---|"]
for w, n, ov, line in sorted(done, key=lambda x: -x[1]):
    L.append("| **%s** | %d | %s |" % (w, n, line.replace("|", "／")))

L += ["", "---", "", "## 三、弃件（%d 词·**列出备查，不静默丢弃**·视角㉚）" % len(fake), ""]
for g in sorted({gg for _, _, gg in fake}):
    ws = [w for w, n, gg in fake if gg == g]
    if ws: L.append("- **%s**（%d）：%s" % (g, len(ws), "／".join(ws)))
L += ["", "> ⚠**误剔一个真多义词，它就永远不在待办里了**——这是**不可见的漏**（视角㉚）。",
      "> 故弃件全部列出词形，**由人复核**。"]

open(os.path.join(B, "term_layer", "多义词分野三分表.md"), "w", encoding="utf-8").write("\n".join(L))
json.dump(dict(fake=len(fake), done=len(done), todo=[w for w, *_ in todo]),
          open(os.path.join(B, "term_layer", "_polysemy.json"), "w"), ensure_ascii=False, indent=1)
print("127 词三分：伪多义 %d ｜真多义已闭合 %d ｜**真多义待办 %d**" % (len(fake), len(done), len(todo)))
print("待办词：", "／".join(w for w, *_ in sorted(todo, key=lambda x: -x[1])))
