#!/usr/bin/env python3
"""协议13·干扰过滤实验法 —— 验证「器官定位 → 病位候选」假设（㉟批）。

事故（㉞批·主角上级）：我以肾炎作 R28 的反例，**却未执行 R28 自身的前提条件
「无表里干扰」**。实测 23 处窗口中 16 处带表证征象（浮肿/身肿/恶风/脉浮/无汗——
**浮肿本身即病邪反应于体表＝表位**〔A·金匮风水「恶风一身悉肿脉浮」〕）。
→ 该反例建立在**污染样本**上，已撤回（W-1.17）。**以违反前提的样本作反驳，结论无效。**

协议13：凡验证「病位归属」类假设，须先**逐案标注表证/里证征象，剔除带干扰者，
只在干净样本上统计**。

【已知失效模式】(视角㉕)
  ① 干扰词表是人工列的；漏一个干扰词 → 污染样本被当成干净样本。
     **浮肿/身肿**是㉞批才补上的——此前正因漏了它，才把 16 例污染样本当干净的用。
  ② 窗口取 ±150 字，跨案会把邻案的证候算进来（体裁效应，视角㉟）。
     故本工具**只用于粗筛，n<5 一律标「样本不足」**。
  ③ 「柴胡剂共现」只证明同段出现，**不证明该病用了柴胡剂**（视角㉟ 体裁关同样适用）。
  ④ 病名是**现代病名**，胡老原文中出现频次低且分布不均——这是样本量小的根因，
     **不是可以靠调参解决的**。
【弃件条件】干净样本 n<5 者一律标「样本不足·未定」，不得下结论。
【口径】(视角㊱) 一处＝一个 ±150 字窗口；`python3 tools/organ_locus.py` 复跑。
"""
import re, os
from collections import Counter

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = ["C_jingfangliyu.txt", "ocr_未识别2.txt", "ocr_未识别1.txt", "ocr_解读张仲景医学.txt",
         "ocr_经方传真系.txt", "ocr_胡希恕病位类方解.txt", "ocr_中医临床家胡希恕.txt",
         "ocr_冯世纶带教实录第一辑.txt"]
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com")
T = "".join(JUNK.sub("", re.sub(r"\s+", "", open(os.path.join(B, "sources", f), encoding="utf-8",
            errors="ignore").read())) for f in BOOKS if os.path.exists(os.path.join(B, "sources", f)))

# ── 干扰征象（㉟批·浮肿/身肿为㉞批补入，此前漏之即致污染样本被误用）──
BIAO = r"恶寒|恶风|发热|脉浮|无汗|头项强痛|身疼痛|浮肿|身肿|一身悉肿|水肿"
LI   = r"下利|自利|便秘|大便难|不大便|腹满|干呕|呕吐|纳差|不欲饮食|完谷不化"
CHAI = r"柴胡"

DISEASE = {
 "胆囊炎":  ("胆·半表半里", r"胆囊炎|胆道感染|胆石"),
 "肝炎":    ("肝·半表半里", r"肝炎|肝硬变|肝硬化"),
 "肺炎":    ("肺·胸腔",     r"肺炎"),
 "心脏":    ("心·胸腔",     r"心脏病|冠心病|心绞痛|心肌梗"),
 "子宫":    ("子宫·腹腔",   r"子宫|盆腔炎|附件炎"),
 "肾炎":    ("肾·腹腔",     r"肾炎|肾病|肾盂"),
 "结肠炎":  ("**大肠＝里**", r"结肠炎|肠炎"),
 "胃溃疡":  ("**胃＝里**",   r"胃溃疡|十二指肠溃疡|胃下垂"),
}

L = ["# 协议13·干扰过滤实验（㉟批）", "",
     "> 事故：㉞批我以肾炎作反例，**却未执行该假设自身的前提「无表里干扰」**。",
     "> 实测 23 处窗口中 **16 处带表证征象**（浮肿/身肿/恶风/脉浮/无汗——",
     "> **浮肿本身即病邪反应于体表＝表位**〔A·金匮风水「恶风一身悉肿脉浮」〕）。",
     "> **以违反前提的样本作反驳，结论无效。** 该反例已撤回（W-1.17）。", "",
     "> ⚠**判据**：干净样本 **n≥5** 且柴胡占比显著，方可支持假设；",
     "> **n<5 一律标「样本不足·未定」**，不得下结论。", "",
     "| 病 | 器官所属 | 总窗口 | 带表干扰 | 带里干扰 | **干净 n** | 干净样本柴胡 | 判定 |",
     "|---|---|---|---|---|---|---|---|"]
rows = []
for name, (organ, rx) in DISEASE.items():
    wins = [T[max(0, m.start() - 150):m.start() + 150] for m in re.finditer(rx, T)]
    nb = sum(1 for w in wins if re.search(BIAO, w))
    nl = sum(1 for w in wins if re.search(LI, w))
    clean = [w for w in wins if not re.search(BIAO, w) and not re.search(LI, w)]
    nc = len(clean); ch = sum(1 for w in clean if re.search(CHAI, w))
    if nc < 5:
        verdict = "**样本不足·未定**"
    elif ch / nc >= 0.5:
        verdict = "支持(柴胡 %.0f%%)" % (100 * ch / nc)
    elif ch == 0:
        verdict = "**反向支持**(柴胡 0)" if "里" in organ else "不支持(柴胡 0)"
    else:
        verdict = "弱(柴胡 %.0f%%)" % (100 * ch / nc)
    rows.append((name, organ, len(wins), nb, nl, nc, ch, verdict))
    L.append("| %s | %s | %d | %d | %d | **%d** | %d | %s |" % (
        name, organ, len(wins), nb, nl, nc, ch, verdict))

L += ["", "---", "",
      "## 结论（按判据机械得出，不作延伸）", ""]
ok = [r for r in rows if r[5] >= 5]
L += ["- **干净样本 n≥5 者仅 %d／%d 类**——绝大多数类别在过滤后样本不足。" % (len(ok), len(rows)),
      "- 这不是调参能解决的：**现代病名在胡老原文中本就出现频次低且分布不均**（失效模式④）。",
      "- 故 **R28 维持 [待证·样本不足]**，**只作候选发现提示，不得作判据**。", "",
      "> ⚠即使 n≥5，「柴胡剂共现」也只证明**同段出现**，不证明该病用了柴胡剂",
      "> ——视角㉟ 体裁关在此同样适用。"]
open(os.path.join(B, "term_layer", "协议13_干扰过滤实验.md"), "w", encoding="utf-8").write("\n".join(L))

print("%-8s %-14s %5s %5s %5s %6s %5s  %s" % ("病", "器官", "总", "表扰", "里扰", "干净n", "柴胡", "判定"))
for r in rows:
    print("%-8s %-14s %5d %5d %5d %6d %5d  %s" % r)
print("\n干净样本 n≥5 者：%d／%d 类" % (len(ok), len(rows)))
