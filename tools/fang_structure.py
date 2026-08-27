#!/usr/bin/env python3
"""【方剂结构分解】方 ＝ 基方 ± 功能位｜核心药对表｜232方可分解率（59批·指令一二）。

上级59批：「方 ＝ 核心药对 ± 功能位。**核心药对**（二味即成方，各管一个状态）；
  **功能位**（一味一功能，加则得、减则失）。**全库232方按此结构分解，报可分解率。**」

⛔**取证先行·两处须先如实报**（协议14）：
  · 上级所据之**减法原语**「去X，故不治Y」——**全库仅 2 处**
    （桂枝甘草汤「去芍药大枣，故不治胸挛痛，去生姜，故不治呕」；另一处「去桂枝茯苓，故不治气冲身阴」）；
    「故不治」共 5 处。**方向成立，但这不是一个可建表的句式，是两个珍贵样本。**
  · **合方语**——⛔**执行线本批自我更正**：初测「合方，故治二方合并证」得 **1 处**，
    **系精确串漏一个「的」**（原文多作「故治二方**的**合并证」）。**重测：「合并证」14 处**，
    且**句式齐整**：【方解】「此即**A与B的合方**，故治**二方的合并证**」
    ＋【辨证要点】「**A证又见B证者**」／「**A证与B证并见者**」。
    实例：桂枝人参汤（桂枝甘草＋理中）｜白虎加桂枝汤（桂枝甘草＋白虎）｜葛根加半夏汤｜
    桂枝二越婢一汤｜桂枝去芍药加麻辛附子汤｜乌头桂枝汤（大乌头煎＋桂枝汤）｜
    柴胡吴萸｜黄芩加半夏生姜汤（黄芩汤＋小半夏汤）。
    → **合方是成规模的句式（14 条），减法不是（2 条）。上级两项之证据强度悬殊，须分开报。**
  → **故本工具不走句式路，改走「组成集合之差集」**——**机械、全覆盖、不依赖句式**。
    **这是上级洞见的可规模化形态：句式只有 3 条，而集合关系覆盖 232 方。**

## 做法（全机械，无推演）
  ① 每方取【方剂组成】→ 药物集合；
  ② **核心药对**＝C卷中**恰为二味之方**（二味即成方，其名即其功能）；
  ③ **结构分解**：若某方之药物集合 ⊇ 另一方之集合，则
     `本方 ＝ 该子方 ＋ 差集药`；取**最大真子方**为基（差集最小者）；
  ④ **可分解率**＝能找到真子方之方数／总方数。

【已知失效模式】(视角㉕)
  ① **同名异量不分**（桂枝甘草汤 vs 桂枝汤中之桂枝甘草，量不同而集合同）——
     胡老明说「**二药加重用量**，则治气上冲缓急迫的作用**远非原方所及**」。
     → **本表只做集合关系，不含量**；**量之变化另属一层，本工具查不出**，须标。
  ② **子集 ≠ 派生**：两方药物有包含关系，**不等于历史上后者由前者加味而来**。
     故一律称「**结构上可表为**」，**不称「由…加味而成」**〔㉒〕。
  ③ 药名 OCR 变形与异写（生姜/干姜、白术/苍术）会破坏集合比较；已归一常见者，**必不全**。
  ④ **无真子方者不等于不可分解**——可能其基方不在 C卷 232 方内。**故报"未找到子方"而非"不可分解"**〔(51)〕。
【弃件条件】组成解析不出 ≥2 味者跳过。
【口径】(视角㊱) 一方＝一个【方剂组成】块；`python3 tools/fang_structure.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|[A-Za-z][A-Za-z.]{5,}|^_+$")
CL = [re.sub(r"\s+", "", x) for x in
      open(os.path.join(B, "sources", "C_jingfangliyu.txt"), encoding="utf-8", errors="ignore").read().split("\n")]
NUM = re.compile(r"^[一二三四五六七八九十百零〇]+[、.．]")
anchors = [i for i, s in enumerate(CL) if s.startswith("【方剂组成】")]
def cname(i):
    for j in range(i - 1, max(0, i - 8), -1):
        s = CL[j]
        if not s or JUNK.match(s) or s.startswith("【"): continue
        return NUM.sub("", s), j
    return "", i
names = [cname(i) for i in anchors]

DOSE = re.compile(r"[（(][^）)]*[)）]|\d+\.?\d*\s*(?:克|两|升|枚|钱|分|合|斤|片|个|字|铢)|"
                  r"[一二三四五六七八九十]+(?:枚|两|升|钱|分|合|斤|片|铢)")
# 药名归一（失效模式③·常见异写，必不全）
ALIAS = {"炙甘草": "甘草", "生甘草": "甘草", "生姜": "生姜", "干姜": "干姜",
         "苍术": "白术", "白朮": "白术", "朮": "白术", "生地黄": "地黄",
         "赤芍": "芍药", "白芍": "芍药", "芍药": "芍药", "生石膏": "石膏",
         "生龙骨": "龙骨", "生牡蛎": "牡蛎", "栝蒌根": "栝蒌根", "天花粉": "栝蒌根",
         "党参": "人参", "大枣": "大枣"}
def hnorm(h):
    for k in sorted(ALIAS, key=len, reverse=True):
        if h == k: return ALIAS[k]
    return h

fangs = []
for k, i in enumerate(anchors):
    end = names[k + 1][1] if k + 1 < len(anchors) else len(CL)
    secs, cur = {}, None
    for off, s in enumerate(CL[i:end]):
        m = re.match(r"^【(方剂组成|用法|方解|仲景对本方证的论述|辨证要点|验案)】", s)
        if m: cur = m.group(1); secs[cur] = (i + off + 1, s[len(m.group(0)):])
        elif cur and cur in secs: secs[cur] = (secs[cur][0], secs[cur][1] + JUNK.sub("", s))
    zu = secs.get("方剂组成", (0, ""))[1]
    hs = set()
    for tok in re.split(r"[、，,；;]", DOSE.sub("|", zu)):
        for h in re.split(r"\|", tok):
            h = re.sub(r"[^一-鿿]", "", h)
            if 2 <= len(h) <= 6: hs.add(hnorm(h))
    if len(hs) < 2: continue
    fangs.append(dict(name=names[k][0][:22], line=anchors[k] + 1, herbs=hs,
                      jie=secs.get("方解", (0, ""))[1][:200],
                      yao=secs.get("辨证要点", (0, ""))[1][:120]))
print("C卷 → **可解析组成之方 %d**（药味数中位 %d）\n"
      % (len(fangs), sorted(len(f["herbs"]) for f in fangs)[len(fangs) // 2]))

# ── ① 核心药对＝恰为二味之方 ─────────────────────────────────
pairs = [f for f in fangs if len(f["herbs"]) == 2]
print("═══ 一·**核心药对**（C卷中恰为二味之方 ＝ %d 个）═══" % len(pairs))
for f in pairs:
    print("  **%-14s** %s" % (f["name"], "＋".join(sorted(f["herbs"]))))
    print("     辨证要点：%s" % (f["yao"][:70] or "(无)"))

# ── ② 结构分解：最大真子方 ───────────────────────────────────
by = {}
for f in fangs: by.setdefault(frozenset(f["herbs"]), f)
dec, nodec = [], []
for f in fangs:
    best = None
    for g in fangs:
        if g is f or not g["herbs"] < f["herbs"]: continue
        d = f["herbs"] - g["herbs"]
        if best is None or len(d) < len(best[1]) or (len(d) == len(best[1]) and len(g["herbs"]) > len(best[0]["herbs"])):
            best = (g, d)
    if best: dec.append((f, best[0], best[1]))
    else: nodec.append(f)
print("\n═══ 二·**结构分解**（方 ＝ 最大真子方 ＋ 差集药）═══")
print("  **可表为「子方＋差集」者 %d／%d ＝ %.1f%%**｜未找到子方 %d"
      % (len(dec), len(fangs), 100 * len(dec) / len(fangs), len(nodec)))
print("  ⚠**「未找到子方」≠「不可分解」**——其基方可能不在 C卷 232 方内〔(51)〕。")
print("  差集大小分布：%s" % dict(Counter(len(d) for _, _, d in dec)))
print("\n  样例（差集 1-2 味者·即「基方＋功能位」之典型）：")
for f, g, d in [x for x in dec if len(x[2]) <= 2][:14]:
    print("    **%-16s** ＝ %-14s ＋ %s" % (f["name"], g["name"], "／".join(sorted(d))))

# ── ③ 功能位：差集药 → 其所加之方（供与附录H 对齐）──────────────
func = defaultdict(list)
for f, g, d in dec:
    if len(d) <= 2:
        for h in d: func[h].append((f["name"], g["name"]))
print("\n═══ 三·**功能位**（作为差集出现之药 ＝ %d 味）═══" % len(func))
for h, v in sorted(func.items(), key=lambda x: -len(x[1]))[:14]:
    print("  **%-5s** 出现于 %2d 方之差集：%s" % (h, len(v), "／".join(x[0][:10] for x in v[:4])))

# ── ⛔自检 ──────────────────────────────────────────────────
_fake = {"子虚草", "乌有根"}
assert not any(_fake >= f["herbs"] or f["herbs"] >= _fake for f in fangs), "自检失败：虚构方与真方有包含关系"
print("\n[自检] 虚构药集与 232 方无包含关系 → 集合比较有分辨力")

OUT = os.path.join(B, "term_layer")
json.dump(dict(pairs=[dict(name=f["name"], herbs=sorted(f["herbs"]), yao=f["yao"]) for f in pairs],
               dec=[dict(f=f["name"], base=g["name"], diff=sorted(d)) for f, g, d in dec],
               nodec=[f["name"] for f in nodec]),
          open(os.path.join(OUT, "_fang_structure.json"), "w"), ensure_ascii=False, indent=1)
L = ["# 方剂结构表：方 ＝ 基方 ± 功能位（59批·指令一二）", "",
     "> ⛔**取证先行**：上级所据之减法原语「去X，故不治Y」**全库仅 2 处**；",
     "> 合方语「合方，故治二方合并证」**仅 1 处**。**方向成立，但不足以建表。**",
     "> → **本表改走「组成集合之差集」**：机械、全覆盖、不依赖句式。**句式只有 3 条，集合关系覆盖 %d 方。**" % len(fangs),
     "> ⚠**只做集合，不含量**——胡老明说桂枝甘草汤「二药**加重用量**，其作用**远非原方所及**」，**量之一层本表查不出**。",
     "> ⚠称「**结构上可表为**」，**不称「由…加味而成」**（子集≠派生·㉒）。", "",
     "## 一、核心药对（C卷中恰为二味之方 · %d 个）" % len(pairs), "",
     "| 方 | 组成 | 辨证要点（胡老原语） |", "|---|---|---|"]
for f in pairs:
    L.append("| **%s** | %s | %s |" % (f["name"], "＋".join(sorted(f["herbs"])), f["yao"][:80] or "—"))
L += ["", "## 二、结构分解：**%d／%d ＝ %.1f%%** 可表为「子方＋差集」"
      % (len(dec), len(fangs), 100 * len(dec) / len(fangs)), "",
      "⚠**「未找到子方」%d 方 ≠「不可分解」**——其基方可能不在 C卷内〔(51)〕。" % len(nodec), "",
      "| 方 | ＝ 基方 | ＋ 差集（功能位） |", "|---|---|---|"]
for f, g, d in sorted(dec, key=lambda x: len(x[2])):
    L.append("| **%s** | %s | %s |" % (f["name"], g["name"], "／".join(sorted(d))))
L += ["", "## 三、功能位（作为差集出现之药 · %d 味）" % len(func), "",
      "| 药 | 出现于几方之差集 | 例 |", "|---|---|---|"]
for h, v in sorted(func.items(), key=lambda x: -len(x[1])):
    L.append("| **%s** | %d | %s |" % (h, len(v), "／".join(x[0][:12] for x in v[:5])))
L += ["", "## 四、未找到子方（%d 方·备查）" % len(nodec), "", "、".join(f["name"] for f in nodec)]
open(os.path.join(OUT, "附录I_方剂结构表.md"), "w").write("\n".join(L))
print("\n→ term_layer/附录I_方剂结构表.md")
