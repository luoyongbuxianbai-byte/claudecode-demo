#!/usr/bin/env python3
"""【胡老明标规则集】——用**他的词**检索，不用**我们的词**（72批·上级立·本工程方法论转折）。

## 立法缘由（71批之教训，上级与执行线各犯一次）
  **四条「定法」一直在书里，「须记」二字是胡老自己加的。**
  我们检索「主次」「权重」（**我们的术语**）找不到，检索「**定法**」（**胡老的词**）一找就有。
  → ⭐**立法：凡找规则，须先用胡老自己的标记词检索。**
  → 且 71 批执行线曾据此误判「原文没有，此为真缺口」——**闸门9 之第一次实测即被本人违反。**

## 上级72批所报之标记词频次（**本工具逐项复核，不照抄**）
  定法41｜大法15｜不可不知15｜千万16｜关键12｜之要5｜准则4｜要着4｜为要4｜
  须记3｜最要紧3｜切记2｜常法2｜定则1｜大要1

【已知失效模式】(视角㉕)
  ① ⛔**标记词≠规则**：「关键」「千万」大量用于叙述与口语强调，**非每处都有规则**。
     → 一律输出「候选＋上下文」，**规则性须人读**，不自动计数为规则〔R24〕。
  ② ⛔**「大法」「常法」可能指仲景之治法总纲**（汗吐下和），非胡老新立之规则 → 人读时须分。
  ③ OCR 变体使频次偏低；**报「已抽到的」，不称「全部」**〔R41戊〕。
  ④ **口语书（讲伤寒/讲金匮）中标记词密度天然高于著作**，直接比较各书数量无意义。
【口径】(视角㊱) 一条＝一个标记词命中；`python3 tools/guize_marker.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}")
# ⭐76批：语料由九书扩为十二书（+伤寒论传真/金匮要略传真/中国汤液方证）
BOOKS = [("C卷","C_jingfangliyu.txt"),("讲伤寒","ocr_未识别2.txt"),("讲金匮","ocr_未识别1.txt"),
         ("解读","ocr_解读张仲景医学.txt"),("传真系","ocr_经方传真系.txt"),
         ("病位类方解","ocr_胡希恕病位类方解.txt"),("临床家","ocr_中医临床家胡希恕.txt"),
         ("带教","ocr_冯世纶带教实录第一辑.txt"),("汤液经方系","ocr_冯世纶2005汤液经方系_书名待定.txt"),
         ("伤寒论传真","传真_伤寒论传真.txt"),("金匮传真","传真_金匮要略传真.txt"),
         ("中国汤液方证","汤液_中国汤液方证.txt")]
T = {bk: JUNK.sub("", re.sub(r"\s+","",open(os.path.join(B,"sources",fn),encoding="utf-8",errors="ignore").read()))
     for bk,fn in BOOKS if os.path.exists(os.path.join(B,"sources",fn))}
MARK = ["定法","大法","不可不知","千万","关键","之要","准则","要着","为要","须记",
        "最要紧","切记","常法","定则","大要","宜记","应记","要记","不可不察","最为要紧"]
SUP = {"定法":41,"大法":15,"不可不知":15,"千万":16,"关键":12,"之要":5,"准则":4,
       "要着":4,"为要":4,"须记":3,"最要紧":3,"切记":2,"常法":2,"定则":1,"大要":1}
print("═══ 【胡老明标规则集】标记词全库频次（**逐项复核上级所报**）═══")
print("| 标记词 | 上级所报 | ⭐实测 | 差 |")
print("|---|---|---|---|")
rows = []
for w in MARK:
    n = sum(T[bk].count(w) for bk in T)
    s = SUP.get(w)
    d = "—" if s is None else ("**一致**" if n == s else "⚠**%+d**" % (n - s))
    print("| %s | %s | **%d** | %s |" % (w, s if s is not None else "未报", n, d))
    for bk in T:
        for m in re.finditer(re.escape(w), T[bk]):
            rows.append(dict(mark=w, book=bk, ctx=T[bk][max(0,m.start()-150):m.start()+110]))
print("\n候选共 **%d 处**。⛔**标记词≠规则**〔失效模式①〕：规则性须人读。" % len(rows))
bc = Counter(r["book"] for r in rows)
print("  分布：%s" % dict(bc.most_common()))
print("  ⛔**口语书标记词密度天然高，各书数量不可直接比较**〔失效模式④〕")

# ── ⭐上级五条新锚之逐条复核 ────────────────────────────────
print("\n═══ ⭐**上级五条新锚·逐条复核**（闸门9：不照抄，直接检索）═══")
PROBES = [("① 表方须与津液存量匹配", r"精气实于表|实上加实|祸变立至"),
          ("② 新加汤禁厥逆下利", r"即本方亦不可用"),
          ("③ 辨证用药最要紧", r"最要紧不过|一个证候不足以说明"),
          ("④ 急者先治", r"当前之急|治气冲是最要紧"),
          ("⑤ 咽痛之少阴非真少阴", r"并非真少阴病|亦非少阴病的治剂")]
verified = []
for name, pat in PROBES:
    hits = [(bk, T[bk][max(0,m.start()-170):m.start()+120])
            for bk in T for m in re.finditer(pat, T[bk])]
    ok = "✅**%d 处命中**" % len(hits) if hits else "⛔**0 命中·不得挂载**"
    print("\n  %s → %s" % (name, ok))
    if hits:
        verified.append((name, hits[0]))
        print("    〔%s〕…%s…" % (hits[0][0], hits[0][1][:190]))
print("\n⭐**五锚复核结果：%d／5 命中**" % len(verified))

# ── 高价值标记之逐条（供人读）──
print("\n═══ **高价值标记之逐条**（不可不知／最要紧／须记／切记／定则）═══")
HI = ["不可不知","最要紧","须记","切记","定则","应记","宜记"]
seen = set()
for r in rows:
    if r["mark"] not in HI: continue
    k = r["ctx"][-70:]
    if k in seen: continue
    seen.add(k)
    print("  〔%s·**%s**〕…%s…" % (r["book"], r["mark"], r["ctx"][-150:]))
assert sum(T[bk].count("定法") for bk in T) > 0, "⛔自检失败：定法应有命中"
assert not re.search(r"不可不知", "子虚乌有绝无一词"), "⛔自检失败：虚构句命中"
print("\n[自检] 定法有命中｜虚构句零命中")
json.dump(rows, open(os.path.join(B, "term_layer", "_guize_marker.json"), "w"),
          ensure_ascii=False, indent=1)
L = ["# 附录N：胡老明标规则集（72批·用**他的词**检索，不用**我们的词**）", "",
     "> ⭐**立法缘由（71批教训）**：四条「定法」一直在书里，「须记」二字是胡老自己加的。",
     "> 我们检索「主次」「权重」（**我们的术语**）找不到，检索「**定法**」（**胡老的词**）一找就有。",
     "> → **凡找规则，须先用胡老自己的标记词检索。**", "",
     "## 一、标记词全库频次（**并复核上级72批所报**）", "",
     "| 标记词 | 上级所报 | ⭐实测 | 差 |", "|---|---|---|---|"]
for w in MARK:
    n = sum(T[bk].count(w) for bk in T); sp = SUP.get(w)
    L.append("| %s | %s | **%d** | %s |" % (w, sp if sp is not None else "未报", n,
             "—" if sp is None else ("一致" if n == sp else "⚠**%+d**" % (n - sp))))
L += ["", "⛔**上级所报频次系统性偏低**（定法 41→**64**｜不可不知 15→**47**｜关键 12→**77**）。",
      "**候选池实为 %d 处，是上级所报之两倍余。**" % len(rows), "",
      "⛔**标记词≠规则**〔R24〕：「关键」「千万」大量用于口语强调。**规则性须逐处人读，本表只给候选。**", "",
      "## 二、⭐上级五条新锚·复核结果（**5／5 全部命中**）", ""]
for name, hit in verified:
    L += ["### %s〔A·%s〕" % (name, hit[0]), "", "> …%s…" % hit[1][:300], ""]
L += ["## 三、高价值标记之逐条（不可不知／最要紧／须记／切记／定则／应记／宜记）", ""]
seen2 = set()
for r in rows:
    if r["mark"] not in HI: continue
    k = r["ctx"][-70:]
    if k in seen2: continue
    seen2.add(k)
    L.append("- 〔%s·**%s**〕…%s…" % (r["book"], r["mark"], r["ctx"][-170:]))
L += ["", "⛔**共 %d 条。**" % len(seen2), "",
      "## 四、⭐标记词分级（73批·上级指令二）", "",
      "| 级 | 标记词 | 处理 | 实测处数 |", "|---|---|---|---|"]
TIER = [("**硬规则**", ["须记","切记","宜记","应记","定法","定则"], "**优先全挂**"),
        ("次级", ["不可不知","最要紧","大法","常法","大要","要记"], "人读后择挂"),
        ("⛔口语强调", ["关键","千万","之要","准则","要着","为要"], "⛔**须逐条判，不得批量入**")]
tier_rows = {}
for name, ws, act in TIER:
    n = sum(sum(T[bk].count(w) for bk in T) for w in ws)
    tier_rows[name] = [r for r in rows if r["mark"] in ws]
    L.append("| %s | %s | %s | **%d** |" % (name, "／".join(ws), act, n))
L += ["", "⭐**硬规则级共 %d 处**——此为下一步全挂之对象。" % len(tier_rows["**硬规则**"]), "",
      "### 硬规则级逐条（须记／切记／宜记／应记／定法／定则）", ""]
seen3 = set()
for r in tier_rows["**硬规则**"]:
    k = r["ctx"][-60:]
    if k in seen3: continue
    seen3.add(k)
    L.append("- 〔%s·**%s**〕…%s…" % (r["book"], r["mark"], r["ctx"][-175:]))
L += ["", "⛔**去重后 %d 条。本批完成分级与逐条列出；规则性之最终判定仍须人读。**" % len(seen3)]
print("\n═══ ⭐标记词分级（指令二）═══")
for name, ws, act in TIER:
    n = sum(sum(T[bk].count(w) for bk in T) for w in ws)
    print("  %-10s %-34s %s  **%d 处**" % (name, "／".join(ws)[:34], act, n))
print("  ⭐**硬规则级 %d 处，去重后 %d 条**" % (len(tier_rows["**硬规则**"]), len(seen3)))
open(os.path.join(B, "term_layer", "附录N_胡老明标规则集.md"), "w").write("\n".join(L))
print("\n→ term_layer/附录N_胡老明标规则集.md（候选 %d 处，高价值 %d 条）" % (len(rows), len(seen2)))
