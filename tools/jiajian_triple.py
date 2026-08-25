#!/usr/bin/env python3
"""【加减三元组】：胡老方解固定句式「此于A汤加X，故治A汤证而Y者」→ (基方｜加减药｜孤证)（57批·指令一）。

上级57批：「**"故治A汤证 + 而X者"——这个句式就是加减的完整语法**：
  A汤证＝主证＝主要矛盾；『而X者』＝**孤证**（该位有阳性反应但不构成主矛盾）；
  **加药＝专处理这个孤证**。」

⭐**取证先行**：C卷 232 方解中，
  `此于…故治…者` **37 处**｜`故治…证…而…者` **47 处**｜`此于X汤` **48 处**｜`故治…证` **79 处**。
  → **该句式确实存在且成规模。上级之判成立。**

⛔**本表之性质**：**三元组全部逐字来自方解，我方不补一味、不判一证**〔㉒〕。
  句式不合者**留在"未解析"栏**，不猜。

【已知失效模式】(视角㉕)
  ① **「此于上方/该方」之指代**须回溯上一方名；**回溯失败者标 [基方未解析]**，不猜。
  ② **加减串含解释语**（「去草枣的甘塞和生姜的辛散」）——**药名靠正向词表抽**，
     解释语不入药位；**词表漏一味即漏一条**〔R41⑪〕。
  ③ **孤证段可能含多证**（「饮多呕剧而渴者」＝三证）——**照录不拆**，
     拆分属判据结构裁决，须另行取证。
  ④ **本表只覆盖"此于…故治…者"这一句式**。胡老另有大量加减写在
     【辨证要点】与医案加减法里，**本工具抓不到**——**"全量"仍是"该句式的全量"**。
  ⑤ **去药之读法**：「去X」＝**该孤证不存在**（如「不呕者去半夏」）。
     本工具**只登记方向，不判该案是否真无此证**。
【弃件条件】基方或孤证段缺失者入未解析；孤证段 >50 字者弃（跨句）。
【口径】(视角㊱) 一条＝一个「基方×加减×孤证」三元组；`python3 tools/jiajian_triple.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL = [re.sub(r"\s+", "", x) for x in
      open(os.path.join(B, "sources", "C_jingfangliyu.txt"), encoding="utf-8", errors="ignore").read().split("\n")]
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com|[A-Za-z][A-Za-z.]{5,}|^_+$")   # 末式剔 PDF 页脚残串
NUM = re.compile(r"^[一二三四五六七八九十百零〇]+[、.．]")
anchors = [i for i, s in enumerate(CL) if s.startswith("【方剂组成】")]
def cname(i):
    for j in range(i - 1, max(0, i - 8), -1):
        s = CL[j]
        if not s or JUNK.match(s) or s.startswith("【"): continue
        return NUM.sub("", s), j
    return "", i
names = [cname(i) for i in anchors]

fangs = []
for k, i in enumerate(anchors):
    end = names[k + 1][1] if k + 1 < len(anchors) else len(CL)
    secs, cur = {}, None
    for off, s in enumerate(CL[i:end]):
        m = re.match(r"^【(方剂组成|用法|方解|仲景对本方证的论述|辨证要点|验案)】", s)
        if m: cur = m.group(1); secs[cur] = (i + off + 1, s[len(m.group(0)):])
        elif cur: secs[cur] = (secs[cur][0], secs[cur][1] + JUNK.sub("", s))
    fangs.append(dict(name=names[k][0], zu=secs.get("方剂组成", (0, ""))[1],
                      jie=secs.get("方解", (0, ""))))

# ── 药名正向词表（从全部【方剂组成】反抽·失效模式②）────────────────
DOSE = re.compile(r"[（(][^）)]*[)）]|\d+\.?\d*\s*(?:克|两|升|枚|钱|分|合|斤|片|个|字)|"
                  r"[一二三四五六七八九十]+(?:枚|两|升|钱|分|合|斤|片)")
herbs = Counter()
for f in fangs:
    for tok in re.split(r"[、，,；;]", DOSE.sub("|", f["zu"])):
        for h in re.split(r"\|", tok):
            h = re.sub(r"[^一-鿿]", "", h)
            if 2 <= len(h) <= 6: herbs[h] += 1
HERB = sorted([h for h in herbs], key=len, reverse=True)
HERB_RX = re.compile("|".join(map(re.escape, HERB)))

# ── 三元组抽取 ──────────────────────────────────────────────
PAT = re.compile(r"此于([^，,。]{2,30})[，,]?([^。]{0,60}?)[，,]故治([^。]{2,36}?)"
                 r"(?:证|方证)?[，,]?(?:而|有|即)?([^。]{0,44}?)者")
FANGNAME = re.compile(r"[一-鿿]{2,18}(?:汤|散|丸|饮|煎)")
rows, unres = [], []
prev = ""
for f in fangs:
    ln, jie = f["jie"]
    if not jie: continue
    for m in PAT.finditer(jie):
        base_raw, op, treat, gu = m.groups()
        # ① 基方：句中方名；「上方/该方/本方」→ 回溯上一方名
        bm = FANGNAME.search(base_raw)
        if bm: base = bm.group()
        elif re.search(r"上方|该方|本方|前方", base_raw): base = prev or "[基方未解析]"
        else: base = "[基方未解析]"
        # ② 加减药：**正向词表**，解释语不入
        #   ⛔首跑缺陷·自查：句中「此于桂枝甘草汤**而加龙牡**，故治…」基方段与操作段
        #   之间无逗号，致药名落入 base_raw 而 op 为空 → 方向「?」27/40。
        #   **改为在 base_raw+op 全前缀上抽药，并剔除基方名本身**（否则基方药被误记为加味）。
        pre = base_raw + op
        if bm: pre = pre.replace(bm.group(), "")
        add = list(dict.fromkeys(HERB_RX.findall(pre)))
        direction = "去" if re.search(r"[去减]", pre) else ("加" if add else "?")
        gu = gu.strip("而有即，,")
        if not gu or len(gu) > 50:
            unres.append(dict(fang=f["name"][:18], sent=m.group()[:80], why="孤证段缺失或过长")); continue
        rows.append(dict(fang=f["name"][:18], base=base, dir=direction,
                         add=add, gu=gu, treat=treat, sent=m.group()[:150]))
    prev = f["name"]

print("C卷 %d 方 → **三元组 %d 条**（未解析 %d）\n" % (len(fangs), len(rows), len(unres)))
print("  基方可解析 %d ｜ [基方未解析] %d"
      % (sum(1 for r in rows if not r["base"].startswith("[")),
         sum(1 for r in rows if r["base"].startswith("["))))
print("  方向：%s" % dict(Counter(r["dir"] for r in rows)))
print("  加减药有解析者 %d 条（无药名者多为「倍用量／去某之辛散」一类）"
      % sum(1 for r in rows if r["add"]))

# ── ⭐药 → 孤证 反向映射（上级指令一③：加减＝孤证→药之映射）────────
inv = defaultdict(list)
for r in rows:
    for h in r["add"]:
        inv[h].append(r)
print("\n── **药 → 孤证** 反向映射：%d 味 ──" % len(inv))
for h, rs in sorted(inv.items(), key=lambda x: -len(x[1]))[:16]:
    print("  **%-6s** ← %s" % (h, "／".join(dict.fromkeys(x["gu"][:22] for x in rs))[:96]))

# ── ⛔自检：必然失败样例 ────────────────────────────────────
_p = PAT.search("此于子虚乌有汤加莫须有草，故治子虚乌有汤证而杳无此症者")
assert _p, "自检失败：正则连构造样例都匹不上"
assert not HERB_RX.findall("莫须有草"), "自检失败：虚构药名被词表命中"
print("\n[自检] 构造样例可匹配、虚构药名不命中 → 抽取器有分辨力")

# ═══ 58批·指令三：**去药专项**（上级令此项优先——它是禁忌的来源）═══
#   「去X」＝该孤证**不在场**。柴胡桂姜之禁（无参草枣→禁便稀）即由"缺什么"判出。
#   ⚠**去药句式与加药不同**：常作「不X者去Y」「若X者去Y」「去Y者，以其X也」。
#   故**另立句式族**，不复用 PAT。
QU_PATS = [
 (r"(?:若|其)?不([^。；，,]{2,14})者[，,]?去([^。；，,]{2,16})", "不X者去Y"),
 (r"(?:若|其)([^。；，,]{2,14})者[，,]?去([^。；，,]{2,16})", "若X者去Y"),
 (r"去([^。；，,]{2,16})者[，,]?(?:以其|因其|为其)([^。；，,]{2,20})", "去Y者以其X"),
 (r"去([^。；，,]{2,16})[，,](?:恐|防|以免)([^。；，,]{2,20})", "去Y恐X"),
]
FULL = []
for fn in ["C_jingfangliyu.txt", "ocr_未识别2.txt", "ocr_未识别1.txt", "ocr_解读张仲景医学.txt",
           "ocr_经方传真系.txt", "ocr_胡希恕病位类方解.txt", "ocr_中医临床家胡希恕.txt",
           "ocr_冯世纶带教实录第一辑.txt"]:
    pth = os.path.join(B, "sources", fn)
    if not os.path.exists(pth): continue
    lines = [JUNK.sub("", re.sub(r"\s+", "", x)) for x in
             open(pth, encoding="utf-8", errors="ignore").read().split("\n")]
    off, idx = 0, []
    for i, l in enumerate(lines): idx.append((off, i + 1)); off += len(l)
    FULL.append((fn[:14], "".join(lines), idx))
def _ln(idx, pos):
    lo, hi = 0, len(idx) - 1
    while lo < hi:
        m = (lo + hi + 1) // 2
        if idx[m][0] <= pos: lo = m
        else: hi = m - 1
    return idx[lo][1]
qu, qdrop = [], Counter()
for bk, T, idx in FULL:
    for rx, fam in QU_PATS:
        for m in re.finditer(rx, T):
            g = m.groups()
            if fam.startswith("去"): drug_raw, cond = g[0], g[1]
            else: cond, drug_raw = g[0], g[1]
            drug = list(dict.fromkeys(HERB_RX.findall(drug_raw)))
            if not drug: qdrop["去药无药名"] += 1; continue      # 正向识别
            # ⛔⛔**58批·逐条人读所得之硬闸门**：「若X者去Y」之主要产地是**仲景方后加减法**，
            #   而**胡老明令不采**，四处逐字：
            #     「至于这个**方后的加减要不得**，我们开始讲就说了**都不要**」
            #     「它底下这些，**这些加减更要不得**」
            #     〔C卷·小柴胡汤按〕「方后**原有加减法，当是后人所附，故去之**」
            #     〔C卷·黄芪建中汤方解〕「**方后加减法系后人所加，不可从**」
            #   实测：本工具首跑 12 条中 **5 条出自方后加减法**（小柴胡/真武），
            #   且其上下文正是胡老**当场逐条驳斥**（「这些都要不得呀…其实这不对…也不对」）。
            #   → **凡上下文含胡老之否定语者，一律标 [胡老不采]，不入判据。**
            ctxw = T[max(0, m.start() - 300):m.end() + 300]
            #   ⚠**自动闸门覆盖不全**：小柴胡方后加减法之否定语写在 C卷按语里，
            #     不在同一 ±300 字窗口 → 正则抓不到。**故另附人读名单**
            #     （同 case_purity 之做法：**名单是人工核过的结果，不是正则产物**）。
            HUMAN_REJECT = {("ocr_未识别2.txt", 7909), ("ocr_未识别2.txt", 7912),
                            ("ocr_未识别2.txt", 7913)}   # 小柴胡汤方后加减法·C卷按「后人所附，故去之」
            _ln0 = _ln(idx, m.start())
            rejected = bool(re.search(r"要不得|不可从|后人所[附加]|故去之|这不对|也不对|都不要", ctxw)) \
                       or (bk, _ln0) in HUMAN_REJECT
            外源 = bool(re.search(r"医宗金鉴|注家|成无己|方有执|尤在泾", ctxw))
            qu.append(dict(book=bk, line=_ln(idx, m.start()), fam=fam,
                           rejected=rejected, ext=外源,
                           drug=drug, cond=cond[:30], sent=m.group()[:90],
                           ctx=T[max(0, m.start() - 90):m.end() + 60]))
seen2, quniq = set(), []
for r in qu:
    k = (r["book"], r["sent"])
    if k in seen2: continue
    seen2.add(k); quniq.append(r)
print("\n═══ 58批·指令三·**去药专项**（八书全库·四句式族）═══")
print("  候选 %d ｜ 弃(无药名) %d ｜ **去重后 %d 条**（57批仅 5 例，**扩 %.0f 倍**）"
      % (len(qu), qdrop["去药无药名"], len(quniq), len(quniq) / 5))
ok = [r for r in quniq if not r["rejected"] and not r["ext"]]
rej = [r for r in quniq if r["rejected"]]
ex_ = [r for r in quniq if r["ext"] and not r["rejected"]]
print("  ⛔**分档（逐条人读后所立之闸门）**：**有效 %d 条**｜"
      "**[胡老不采·方后加减法] %d 条**｜[他人转述] %d 条" % (len(ok), len(rej), len(ex_)))
print("  句式：%s" % dict(Counter(r["fam"] for r in quniq)))
qinv = defaultdict(list)
for r in ok:
    for d in r["drug"]: qinv[d].append(r)
print("  **药 → 其「不在场」之孤证**（前12味）：")
for d, rs in sorted(qinv.items(), key=lambda x: -len(x[1]))[:12]:
    print("    **%-5s** 去之因：%s" % (d, "／".join(dict.fromkeys(x["cond"][:18] for x in rs))[:88]))

# ═══ 58批·指令二：**孤证拆到单证粒度** ═══
#   多证合写者（「饮多呕剧而渴」＝三证）须拆；⚠**拆分本身是我方动作**，
#   故**原串与拆分并列保留**，并标 [拆分·待人读核]，不覆盖原文。
SPLIT = re.compile(r"[、，,]|而(?![已])|或|及|以至")
for r in rows:
    parts = [x.strip() for x in SPLIT.split(r["gu"]) if len(x.strip()) >= 2]
    r["gu_split"] = parts
    r["gu_n"] = len(parts)
multi = [r for r in rows if r["gu_n"] > 1]
print("\n═══ 58批·指令二·**孤证拆分** ═══")
print("  40 条中**含多证者 %d 条**（%.0f%%）｜拆后单证 %d 项"
      % (len(multi), 100 * len(multi) / len(rows), sum(r["gu_n"] for r in rows)))
print("  ⚠**拆分是我方动作**：原串与拆分**并列保留**，全部标 [拆分·待人读核]，**不覆盖原文**。")
for r in multi[:5]:
    print("    〔%s〕%s → %s" % (r["fang"][:14], r["gu"][:30], "｜".join(r["gu_split"])))

OUT = os.path.join(B, "term_layer")
json.dump(dict(add=rows, qu=quniq), open(os.path.join(OUT, "_jiajian.json"), "w"), ensure_ascii=False, indent=1)
QU_OUT = quniq
L = ["# 加减三元组：「此于A汤加X，故治A汤证而Y者」（57批·指令一）", "",
     "> **句式取证**：C卷 232 方解中 `此于…故治…者` **37 处**｜`故治…证…而…者` **47 处**。",
     "> **读法**（上级57批）：**A汤证＝主证/主矛盾｜「而Y者」＝孤证（该位阳性但非主矛盾）｜X＝专处理孤证之药。**",
     "> ⚠**三元组逐字来自方解，我方不补一味不判一证**〔㉒〕；句式不合者留「未解析」，不猜。", "",
     "## 一、三元组全表（%d 条）" % len(rows), "",
     "| 方 | 基方 | 向 | 加减药 | **孤证（「而…者」）** | 原语 |", "|---|---|---|---|---|---|"]
for r in rows:
    L.append("| %s | %s | %s | %s | **%s** | %s |" %
             (r["fang"], r["base"], r["dir"], "／".join(r["add"]) or "—", r["gu"], r["sent"][:80]))
L += ["", "## 二、⭐药 → 孤证 反向映射（%d 味）" % len(inv), "",
      "| 药 | 所处理之孤证（逐字） |", "|---|---|"]
for h, rs in sorted(inv.items(), key=lambda x: -len(x[1])):
    L.append("| **%s** | %s |" % (h, "／".join(dict.fromkeys(x["gu"] for x in rs))))
L += ["", "## 三、⭐去药专项（58批·指令三·抽 %d 条 → **有效 %d 条**）" % (len(quniq), len(ok)), "",
      "> **「去X」＝该孤证不在场。**「缺什么」是禁忌的来源——柴胡桂姜无参草枣故禁便稀，即由此判。",
      "> 句式族四：`不X者去Y`／`若X者去Y`／`去Y者以其X`／`去Y恐X`；**正向识别药名**，无药名者弃。", "",
      "| 药（去） | 去之因（该孤证不在场） | 出处 | 原语 |", "|---|---|---|---|"]
for r in ok:
    L.append("| **%s** | %s | %s L%d | %s |" % ("／".join(r["drug"]), r["cond"], r["book"], r["line"], r["sent"][:60]))
L += ["", "⛔**[胡老不采·方后加减法] %d 条**（逐条列出，**不入判据**）：" % len(rej), ""]
for r in rej: L.append("- 〔%s L%d〕%s" % (r["book"], r["line"], r["sent"][:60]))
L += ["", "⚠[他人转述] %d 条（如《医宗金鉴》语，非胡老）：" % len(ex_), ""]
for r in ex_: L.append("- 〔%s L%d〕%s" % (r["book"], r["line"], r["sent"][:60]))
L += ["", "## 四、孤证拆分（58批·指令二·⚠[拆分·待人读核]·原串并列保留）", "",
      "| 原孤证串 | 拆后单证 |", "|---|---|"]
for r in rows:
    if r["gu_n"] > 1: L.append("| %s | %s |" % (r["gu"], "｜".join(r["gu_split"])))
L += ["", "## 五、未解析（%d 条·备查·视角㉚）" % len(unres), ""]
for u in unres[:40]: L.append("- 〔%s〕%s ——%s" % (u["fang"], u["sent"], u["why"]))
open(os.path.join(OUT, "附录H_加减三元组.md"), "w").write("\n".join(L))
print("\n→ term_layer/附录H_加减三元组.md")
