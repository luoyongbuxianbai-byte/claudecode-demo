#!/usr/bin/env python3
"""R22·取证前置探针——把「辨证之前必须先取证」变成机械闸门，而非叮嘱。

故障机制（㉚批查获）：**模型在取证之前已经偷偷完成了辨证**，然后再去找支持证据。
本工具强制反过来：先对病例每个症状逐项检索指定知识库，出证据表，**再**开始辨证。

检索顺序（上级㉚批指令四）：
  ① C卷《经方理论与实践》＝主干
  ② 《伤寒》《金匮》及胡老讲义 ＝ 条文锚
  ③ 胡老医案／临床家／带教实录 ＝ 验证集

⚠**「0 处」的正确读法**（上级㉚批亲自修正的关键一条）：
  C卷是**主干库，不是全集**。故 0 处**不得**读作「该症状在胡老体系中无意义」，
  只能标：**「当前指定知识库无直接证据，不得用于生成胡老方证规则」**。
  两者的区别是：前者是关于医学的断言（我们无权作），后者是关于我们证据状态的断言。

【已知失效模式】(视角㉕)
  ① 字面检索。OCR 变形（"小柴朐""茨苓"）与同义异写（"口干"vs"口燥"）**一律漏检**，
     **不做同义合并**（除非原文明确建立关系）——漏检计入缺口，不猜。
  ② 命中次数**不代表重要性**：条文原文与胡老讲解重复引用会抬高计数。
     故本工具同时报**分书计数**，供人判断是"胡老反复强调"还是"同一句被引多次"。
  ③ 上下文窗口固定 ±60 字，跨句因果读不到——那是人的事，工具只提供材料。
  ④ 等级只机械分 A（条文/注解段）／B（验案段）；C（序言/他人转述）须人工标。
【弃件条件】查询词 <2 字者拒绝（噪声过大）。
【口径】(视角㊱) 一处＝一个源文件行内的一次命中；`python3 tools/evidence_probe.py 词1 词2 …`
"""
import re, os, sys, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIERS = [("①主干·C卷", [("C卷", "C_jingfangliyu.txt")]),
         ("②条文锚·讲义", [("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
                        ("解读张仲景医学", "ocr_解读张仲景医学.txt"),
                        ("病位类方解", "ocr_胡希恕病位类方解.txt"),
                        ("经方传真", "ocr_经方传真系.txt")]),
         ("③验证集·医案", [("中医临床家", "ocr_中医临床家胡希恕.txt"),
                        ("带教实录", "ocr_冯世纶带教实录第一辑.txt"),
                        ("2005汤液经方", "ocr_冯世纶2005汤液经方系_书名待定.txt")])]
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com")
FANG = re.compile(r"[一-鿿]{2,16}(?:汤|散|丸|饮|煎)")

_cache = {}
def load(fn):
    if fn not in _cache:
        p = os.path.join(B, "sources", fn)
        _cache[fn] = open(p, encoding="utf-8", errors="ignore").read().split("\n") if os.path.exists(p) else []
    return _cache[fn]

def probe(word):
    out = []
    for tier, books in TIERS:
        incase = False
        for bk, fn in books:
            for i, raw in enumerate(load(fn)):
                l = JUNK.sub("", re.sub(r"\s+", "", raw))
                if not l: continue
                if "【验案】" in l or re.search(r"例\s*\d+.{0,12}(?:男|女)", l): incase = True
                elif re.search(r"【(方解|注解|辨证要点|原文|条文|用法)", l): incase = False
                j = l.find(word)
                if j < 0: continue
                out.append(dict(tier=tier, book=bk, line=i + 1, lvl="B" if incase else "A",
                                ctx=l[max(0, j - 60):j + 60],
                                fang=sorted(set(FANG.findall(l[max(0, j - 60):j + 60])))))
    return out

def report(words):
    L = ["# R22 取证前置·证据表", "",
         "> 生成：`tools/evidence_probe.py`（文件头含【已知失效模式】与口径）。",
         "> **本表须在辨证开始之前产出。** 先有本表，才允许进入八纲/六经/方证。", "",
         "> ⚠**0 处 ≠ 该症状无医学意义**——只表示「当前指定知识库无直接证据，",
         "> 不得用于生成胡老方证规则」。C卷是主干库，不是全集。", ""]
    summ = []
    for w in words:
        if len(w) < 2:
            print("拒绝(查询词<2字):", w); continue
        hits = probe(w)
        bybook = Counter(h["book"] for h in hits)
        bylvl = Counter(h["lvl"] for h in hits)
        fangs = Counter(f for h in hits for f in h["fang"])
        grade = "N·无证据" if not hits else ("A" if bylvl["A"] else "B")
        summ.append((w, len(hits), grade, [f for f, _ in fangs.most_common(3)]))
        L += ["## 「%s」——命中 **%d** 处｜等级 **%s**" % (w, len(hits), grade), ""]
        if not hits:
            L += ["> **当前指定知识库无直接证据。**",
                  "> 按 R22：**不得用于生成胡老方证规则**；",
                  "> **亦不得据此断言该症状在医学上无意义**（本工具无权作此断言）。", ""]
            continue
        L += ["分书：%s ｜ 分级：A(条文/注解) %d ／ B(验案) %d" %
              (dict(bybook), bylvl["A"], bylvl["B"]),
              "共现方名前三：%s" % ("／".join(f for f, _ in fangs.most_common(3)) or "无"), "",
              "| 层 | 出处 | 级 | 上下文 | 同段方名 |", "|---|---|---|---|---|"]
        for h in hits[:12]:
            L.append("| %s | %s L%d | %s | …%s… | %s |" %
                     (h["tier"], h["book"], h["line"], h["lvl"],
                      h["ctx"].replace("|", "／"), "／".join(h["fang"][:3]) or "—"))
        if len(hits) > 12: L.append("| … | 余 %d 处见 json | | | |" % (len(hits) - 12))
        L.append("")
    L += ["---", "", "## 汇总（这张表决定哪些症状**有资格**进入方证判断）", "",
          "| 症状 | 命中 | 等级 | 常见共现方 | 可否入判据 |", "|---|---|---|---|---|"]
    for w, n, g, fs in summ:
        L.append("| %s | %d | %s | %s | %s |" % (
            w, n, g, "／".join(fs) or "—",
            "**否·无锚**" if g == "N" else "可入(须核上下文)"))
    return "\n".join(L), summ

if __name__ == "__main__":
    ws = sys.argv[1:] or ["耳鸣", "齿痕", "手足心热", "嗳气", "口干舌燥", "口苦", "痘", "黄涕", "汗黏"]
    txt, summ = report(ws)
    out = os.path.join(B, "term_layer", "R22_证据表.md")
    open(out, "w", encoding="utf-8").write(txt)
    print("已写出 %s\n" % out)
    for w, n, g, fs in summ:
        print("  %-10s %4d 处  %-6s  %s" % (w, n, g, "／".join(fs) or "—"))
