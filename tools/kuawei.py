#!/usr/bin/env python3
"""【叠加结构专项】方按二味单元分解 → **跨位方占比**（70批·用户核心诉求·上级指令二）。

## 用户之命题（先写死再测）
  「**基方可以演变很多方**……**叠加通常都是表里共存的，你看基方就知道**，但是我理不清。」
  → 可检验形式：**三味以上之方，其所含二味单元是否绝大多数跨越一个以上病位？**
    · **是** → 「表里共存」为**结构性必然**（发汗须津液之源、攻里须防表未解），非偶然。
    · **否** → 命题证伪。

## 已知锚（A级·跑之前列出）
  〔A·胡老·桂枝汤〕「**既是发汗解热汤剂，又是安中养液方药**」——**胡老自己说它是两个东西。**
  〔A·带教·柴胡桂姜〕「**以甘草干姜汤理中气以复津液**，其方证比小柴胡汤方证明显**阴转**」
    ——**冯氏把「干姜＋甘草」直接叫作甘草干姜汤单元。**

⛔【本工具最大的风险·必须先说】
  **「药→病位」之映射，若由我方指派，则整个结果是我方发明的，不是语料的。**
  → **故本工具不指派药之病位。** 词汇表**只用 28 个二味方**，
    **其状态取自各方自身的【辨证要点】原文**〔附录K·已建〕，
    **病位再由该状态经已挂之判断词表推出**。**任一环无原文支撑者，标 [位未定]，排除出分母。**

【已知失效模式】(视角㉕)
  ① **子集≠派生**〔fang_structure 已立〕→ 一律称「结构上含有」，不称「由…加味而成」。
  ② **二味单元覆盖不全**：28 个单元盖不住所有方（如柴胡、麻黄无二味方）
     → **未被任何单元覆盖之药一律计入 [未覆盖]**，并**在报数时同时报覆盖率**；
     **覆盖率低则本结论之效力相应受限，须明写。**
  ③ **同名异量不分**〔fang_structure 已立〕。
  ④ ⭐**「跨位」之定义须先冻结**：本工具定为「该方所含二味单元之病位集合 ≥2 个不同位」。
     **不含「一个单元本身跨位」之情形**（如桂枝甘草＝表，芍药甘草＝里，各算一位）。
【弃件条件】组成解析不出 ≥2 味者；所含可定位单元 <1 者。
【口径】(视角㊱) 一方一条；`python3 tools/kuawei.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fs = json.load(open(os.path.join(B, "term_layer", "_fang_structure.json")))
zt = json.load(open(os.path.join(B, "term_layer", "_zhuangtai.json")))

# ⛔【70批实发·两处修补】
#  ① **否定语泄漏**：桂枝甘草汤【辨证要点】作「心下悸欲得按而**无里实证**者」，
#     状态抽取把「里实」当成在场状态 → 该方被误判为「里」。
#     **「无X／不X／非X」中的 X 是不在场，不得计为状态。** 本工具先剔负项再定位。
#  ② **药名两侧归一不一致**：单元侧来自 _fang_structure 之解析，方剂侧来自本工具重解析，
#     носители 之前缀与 OCR 噪声不同 → 子集匹配全灭（151 方「无可定位单元」）。
#     **两侧须用同一归一函数。**
NEG = re.compile(r"(?:无|不|非|未)([一-鿿]{2,6})")
def strip_neg(yao, states):
    bad = set()
    for m in NEG.finditer(yao):
        for st in states:
            if st in m.group(1) or m.group(1) in st: bad.add(st)
    return [x for x in states if x not in bad], sorted(bad)
def norm(h):
    # ⛔70批实发：单位字粘在下一味药前（「桂枝12**克炙甘草**6克」）→ 须先剥单位
    h = re.sub(r"^(?:克|克|g|两|钱|斤|枚|升|合|分|铢)+", "", h)
    h = re.sub(r"[各等]?分$|\d.*$|[一二三四五六七八九十]+[枚茎杯两斤]?$", "", h)
    # ⛔只剥**炮制**前缀；生/干/大/小 是药名本身（生姜≠干姜；大黄、大枣、小麦）
    h = re.sub(r"^(?:炙|炮|熟|清|炒|真|煨)(?=[一-鿿]{2,})", "", h)
    h = re.sub(r"汁$|各$", "", h)
    return h
# ── 一·二味单元之状态（取自各方自身【辨证要点】原文·附录K）──
UNIT = {}
for p in zt["pairs"]:   # ⛔状态在 _zhuangtai.json 之 pairs，非 _fang_structure
    hs = frozenset(norm(h) for h in p["herbs"])
    st, neg = strip_neg(p["yao"], p.get("zt", []))
    UNIT[hs] = dict(name=p["name"].lstrip("-、"), yao=p["yao"], zt=st, neg=neg)
# ── 二·状态→病位（用已挂之判断词表·不新造）──
W2P = {"表": ["表实","表虚","浮肿","身疼","无汗","汗出","恶风","恶寒","身痒"],
       "里": ["胃虚","里实","里寒","里热","大便难","下利","呕逆","干呕","心下痞","腹满",
              "腹痛","小便不利","吐涎沫","纳差","便干","虚寒","急迫","烦热","身热","挛痛"],
       "半表半里": ["胸胁苦满","口苦","咽干","目眩","胸满"]}
def locus(states):
    s = set()
    for w in states:
        for k, ws in W2P.items():
            if any(x in w or w in x for x in ws): s.add(k)
    return s
for hs, u in UNIT.items(): u["wei"] = locus(u["zt"])
ok = {hs: u for hs, u in UNIT.items() if u["wei"]}
print("═══ 【叠加结构专项】═══")
print("二味单元 %d 个｜**可定位者 %d 个**（其余状态词未采，标[位未定]排除）" % (len(UNIT), len(ok)))
nneg = [u for u in UNIT.values() if u["neg"]]
if nneg:
    print("  ⛔**否定语泄漏已剔除 %d 个单元**：%s" % (len(nneg),
          "／".join("%s(剔「%s」)" % (u["name"][:8], "、".join(u["neg"])) for u in nneg)))
for hs, u in sorted(ok.items(), key=lambda x: x[1]["name"]):
    print("  %-16s %-10s → %s  〔%s〕" % ("＋".join(sorted(hs)), u["name"][:10],
          "／".join(sorted(u["wei"])), u["yao"][:26]))

# ── 三·全库方之分解与跨位统计 ──
allf = fs["dec"] + [dict(f=x["name"], base=None, diff=None) for x in fs["pairs"]]
comp = {}
for r in zt["rows"]: comp.setdefault(r["fang"], None)
# 取 C卷【方剂组成】
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}")
C = JUNK.sub("", re.sub(r"\s+", "", open(os.path.join(B, "sources", "C_jingfangliyu.txt"),
                                          encoding="utf-8", errors="ignore").read()))
HERB = re.compile(r"([一-鿿]{2,5})(?=\d|各)")
fangs = {}
for m in re.finditer(r"([一-鿿]{2,12}(?:汤|散|丸))(?:方)?【方剂组成】(.{6,400}?)【", C):
    hs = set(norm(h) for h in HERB.findall(m.group(2)))
    if len(hs) >= 2: fangs.setdefault(m.group(1), hs)
print("\nC卷方剂 **%d** 个（组成可解析 ≥2 味）" % len(fangs))

rows, drop = [], Counter()
for f, hs in fangs.items():
    if len(hs) < 3: drop["二味方本身"] += 1; continue
    units = [u for uh, u in ok.items() if uh <= hs]
    if not units: drop["无可定位单元"] += 1; continue
    wei = set()
    for u in units: wei |= u["wei"]
    covered = set()
    for uh in [k for k in ok if k <= hs]: covered |= uh
    rows.append(dict(f=f, n=len(hs), units=[u["name"] for u in units], wei=wei,
                     cov=len(covered)/len(hs)))
N = len(rows)
kua = [r for r in rows if len(r["wei"]) >= 2]
cov = sum(r["cov"] for r in rows)/N if N else 0
print("三味以上方 **%d**（弃：%s）" % (N, dict(drop)))
print("  ⛔**平均单元覆盖率 %.0f%%**〔失效模式②：覆盖率低则本结论效力相应受限〕" % (100*cov))
print("\n═══ ⭐**核心结果：跨位方占比** ═══")
assert N > 0, "⛔N=0：单元词汇表未生效，先查 zt/pairs 之 zt 字段"
print("  **跨 ≥2 位者：%d／%d ＝ %.1f%%**" % (len(kua), N, 100*len(kua)/N))
wc = Counter(frozenset(r["wei"]) for r in rows)
for k, v in wc.most_common():
    print("    %-18s %3d （%.0f%%）" % ("＋".join(sorted(k)), v, 100*v/N))
# ⛔⭐【拒判闸门·70批立·与67批「低于随机13倍不是发现」同型】
#   词汇表若极度偏向某一位，则「跨位」在构造上就不可能被发现，此时任何结论都是工具产物。
wdist = Counter(w for u in ok.values() for w in u["wei"])
minw = min(wdist.get(k, 0) for k in ("表", "里", "半表半里"))
print("\n⛔[**拒判闸门**]可定位单元之病位分布：%s" % dict(wdist))
if minw < 3 or cov < 0.5:
    print("  ⛔⭐**本测不下结论。** 理由：%s%s" % (
      "**词汇表极度偏斜（最少之位仅 %d 个单元）——跨位在构造上难以被发现**；" % minw if minw < 3 else "",
      "**平均单元覆盖率仅 %.0f%%，过半药味无单元可归**" % (100*cov) if cov < 0.5 else ""))
    print("  ⛔**故「%.1f%% 跨位」是词汇表之产物，不是语料之性质。不得据以证伪用户命题。**"
          % (100*len(kua)/N))
    print("  ⭐**须补之数据**：表位与半表半里之二味单元。**全库二味方中表位仅 2 个、半表半里仅 1 个**——")
    print("     **这本身是一个发现：单状态方（二味方）绝大多数是里位方（13/16）。**")
else:
    print("\n  → **用户命题「叠加通常表里共存」%s**"
          % ("⭐**成立**" if len(kua)/N > 0.6 else "⚠**部分成立**" if len(kua)/N > 0.35 else "⛔**证伪**"))
print("\n[跨位方举例·前 12]")
for r in kua[:12]:
    print("  %-16s %d味 ｜单元：%s ｜位：%s" % (r["f"], r["n"], "＋".join(r["units"][:3]), "／".join(sorted(r["wei"]))))
# ⛔自检〔㊹〕
assert locus(["浮肿", "无汗"]) == {"表"}, "⛔自检失败：表位映射错"
assert strip_neg("心下悸欲得按而无里实证者", ["心下悸","里实"])[0] == ["心下悸"], "⛔自检失败：否定语未剔除"
assert norm("炙甘草") == "甘草" and norm("炒枳实") == "枳实", "⛔自检失败：药名归一无效"
assert norm("干姜") == "干姜" and norm("大黄") == "大黄" and norm("生姜") == "生姜", "⛔自检失败：药名被过度削剥"
assert norm("克炙甘草") == "甘草" and norm("克干姜") == "干姜", "⛔自检失败：单位字未剥"
assert all(len(h) >= 2 for hs in UNIT for h in hs), "⛔协议15：归一产出单字药名"
assert locus(["胃虚", "吐涎沫"]) == {"里"}, "⛔自检失败：里位映射错"
assert not locus(["子虚乌有"]), "⛔自检失败：虚构状态被定位"
print("\n[自检] 表/里映射正确｜虚构状态不被定位 → 有分辨力")
for r in rows: r["wei"] = sorted(r["wei"])
json.dump(dict(n=N, kua=len(kua), cov=cov, wdist=dict(wdist), rows=rows),
          open(os.path.join(B, "term_layer", "_kuawei.json"), "w"), ensure_ascii=False, indent=1)
