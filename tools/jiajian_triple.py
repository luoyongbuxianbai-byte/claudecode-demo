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

OUT = os.path.join(B, "term_layer")
json.dump(rows, open(os.path.join(OUT, "_jiajian.json"), "w"), ensure_ascii=False, indent=1)
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
L += ["", "## 三、未解析（%d 条·备查·视角㉚）" % len(unres), ""]
for u in unres[:40]: L.append("- 〔%s〕%s ——%s" % (u["fang"], u["sent"], u["why"]))
open(os.path.join(OUT, "附录H_加减三元组.md"), "w").write("\n".join(L))
print("\n→ term_layer/附录H_加减三元组.md")
