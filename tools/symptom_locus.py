#!/usr/bin/env python3
"""【症状→病位】全量对照表（R24·㉛批立）。

根因锚（逐字，讲伤寒 L3281-3283 页132）：
  「那么怎么叫做阳明合病呢？它是同时发作的太阳病，而又有下利，**下利属于里呀，
   这个里就是胃肠之里呀。那么胃肠之里，阳性证就是阳明病，阴性证就是太阴病**。」

该段同时给出三件事：
  ① 症状先归**病位**（下利→里），再由病位＋阴阳定经；
  ② **同一症状可见于多经**——归位 ≠ 归经；
  ③ **归位不因治法取消**：葛根汤从表治，但「里」这个病位从未被删除。

本工具产出：每个症状 token 在全库的分布 —— 命中数／与各六经名共现／与各方名共现，
用以回答「这个症状**首先反映哪个病位**」与「它在**各经**分别以什么形态出现」。

【已知失效模式】(视角㉕)
  ① **共现 ≠ 因果**。「下利」与「太阳」共现，可能是合病，也可能是同段讨论别的事。
     本表只报**共现分布**，**不报归属判定**——判定须人读上下文。
  ② 字面检索，OCR 变形与同义异写漏检；**不做同义合并**。
  ③ 窗口取整行；一行含多经名时全部计入，会高估共现。
【弃件条件】token <2 字拒绝。
【口径】(视角㊱) 一处＝一行内一次命中；`python3 tools/symptom_locus.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读张仲景医学", "ocr_解读张仲景医学.txt"), ("经方传真", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt")]
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com")
JING = ["太阳", "阳明", "少阳", "太阴", "少阴", "厥阴"]
FANG = re.compile(r"[一-鿿]{2,16}(?:汤|散|丸)")

# 病位定义（胡老原文·解剖分区）
LOCUS = {
 "里(食道胃小肠大肠·消化管道)": ["下利", "自利", "便溏", "大便溏", "大便稀", "便秘", "大便难", "不大便",
                    "腹满", "腹痛", "纳差", "不欲饮食", "嗳气", "呕", "干呕", "吐", "心下痞",
                    "心下硬", "肠鸣", "完谷不化", "下利清谷", "食谷欲呕"],
 "表(皮肤肌肉筋骨)": ["恶寒", "恶风", "发热", "头项强痛", "身疼痛", "骨节疼痛", "项背强", "无汗", "自汗出"],
 "半表半里(胸腹两大腔间诸脏器所在)": ["口苦", "咽干", "目眩", "往来寒热", "胸胁苦满", "胸满", "心烦",
                       "默默不欲饮食", "喜呕", "胁下痞硬"],
}

lines = {}
def load(fn):
    if fn not in lines:
        p = os.path.join(B, "sources", fn)
        lines[fn] = open(p, encoding="utf-8", errors="ignore").read().split("\n") if os.path.exists(p) else []
    return lines[fn]

def scan(tok):
    n = 0; jc = Counter(); fc = Counter(); bc = Counter(); ex = []
    for bk, fn in BOOKS:
        for i, raw in enumerate(load(fn)):
            l = JUNK.sub("", re.sub(r"\s+", "", raw))
            if tok not in l: continue
            n += 1; bc[bk] += 1
            for j in JING:
                if j in l: jc[j] += 1
            fc.update(FANG.findall(l))
            if len(ex) < 3: ex.append("%s L%d｜%s" % (bk, i + 1, l[:70]))
    return n, jc, fc, bc, ex

L = ["# 【症状→病位】全量对照表（R24·㉛批）", "",
     "> 根因锚（逐字·讲伤寒 L3281-3283 页132）：",
     "> 「**下利属于里呀，这个里就是胃肠之里呀。那么胃肠之里，阳性证就是阳明病，",
     "> 阴性证就是太阴病。**」", "",
     "> 该段同时给出三件事：①症状先归**病位**再由病位＋阴阳定经；",
     "> ②**同一症状可见于多经——归位 ≠ 归经**；",
     "> ③**归位不因治法取消**（葛根汤从表治，但「里」这个病位从未被删除）。", "",
     "> ⚠**本表只报共现分布，不报归属判定**——共现 ≠ 因果，判定须人读上下文。", ""]
data = {}
for loc, toks in LOCUS.items():
    L += ["## 病位【%s】" % loc, "",
          "| 症状 | 全库命中 | 与六经名共现分布 | 高频共现方 | 分书 |", "|---|---|---|---|---|"]
    for t in toks:
        n, jc, fc, bc, ex = scan(t)
        data[t] = dict(locus=loc, n=n, jing=dict(jc), fang=dict(fc.most_common(5)), book=dict(bc))
        L.append("| **%s** | %d | %s | %s | %s |" % (
            t, n, "／".join("%s%d" % (k, v) for k, v in jc.most_common()) or "—",
            "／".join(k for k, _ in fc.most_common(3)) or "—",
            "／".join("%s%d" % (k, v) for k, v in bc.most_common(3))))
    L.append("")

# 下利专表——本批根因所在，单列
L += ["---", "", "## 专表·下利在六经的分布（本批根因）", "",
      "> **六经全部可见下利** —— 故「便溏→太阴」是最粗暴的一种归因。", "",
      "| 经 | 形态 | 锚 |", "|---|---|---|",
      "| **太阳(合病)** | 太阳与阳明合病必自下利→葛根汤；不下利但呕→葛根加半夏汤 | §32／§33 |",
      "| **阳明** | 热利／下利谵语(小承气)／热结旁流 | §374 等 |",
      "| **太阴** | 自利不渴、自利益甚 | §273／§277 |",
      "| **少阴** | 下利清谷／下利便脓血(桃花汤) | §306 等 |",
      "| **厥阴** | 热利下重(白头翁汤)／下利谵语 | §371 |",
      "| **少阳** | 太阳与少阳合病自下利→黄芩汤 | §172 |",
      "| **误治** | 协热利／利遂不止 | §163 等 |", ""]
json.dump(data, open(os.path.join(B, "term_layer", "_locus_raw.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(B, "term_layer", "症状病位对照表.md"), "w", encoding="utf-8").write("\n".join(L))
tot = sum(v["n"] for v in data.values())
print("症状 token %d 个｜全库命中合计 %d 处" % (len(data), tot))
for loc in LOCUS:
    s = [(t, v["n"]) for t, v in data.items() if v["locus"] == loc]
    print("  %-34s %2d token｜命中 %5d｜0命中者：%s" %
          (loc[:32], len(s), sum(n for _, n in s), [t for t, n in s if n == 0] or "无"))
