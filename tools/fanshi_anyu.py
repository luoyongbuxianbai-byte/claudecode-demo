#!/usr/bin/env python3
"""【特异指征反噬表·按语路径】(76批·清账②之余项·74批所定之正确路径)。

## 74批之结论与本批之条件变化
  74批：「**反噬关系多在【按语】里，不在【辨证要点】里。本工具只读要点，结构上够不着。**」
    → 当时 C卷 之【按】计数为 **0**（C卷用无括号之「按：」），故按语路径做不了。
  ⭐**76批：用户补入《伤寒论传真》《金匮要略传真》两书，共 352 个【按】块** → 路径打通。
  ⭐**且 74批 漏召之金标准，在新书中逐字命中**：
    「**心下急甚者，则痞硬，与人参所主的心下痞硬有虚实之别，须参照其余脉证辨之。**」

## 做法
  ① 抽【按】块（传真二书 352 个）＋ C卷之「按：」块；
  ② 保留含**鉴别语**者（鉴别/之别/不同/相似/相类/须辨/区别/之分）；
  ③ 逐条抽出「**被鉴别之同一指征**」与「**两向之归属**」；
  ④ ⛔**不自动定性**——输出「指征＋两向＋原文」，**归属以原文自述为准**。

【已知失效模式】(视角㉕)
  ① 「不同」大量用于泛指（「与…不同」可指方、指证、指人）→ **须句中含指征词方收**。
  ② 一条按语可含多组鉴别 → 不强拆，整条照录。
  ③ 传真二书系[冯]编次层之整理本，**其【按】多标「胡希恕老师提示」** → **须标层级**。
【口径】(视角㊱) 一条＝一个含鉴别语之按语块；`python3 tools/fanshi_anyu.py` 复跑。
"""
import re, os, json
from collections import Counter
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = [("伤寒论传真","传真_伤寒论传真.txt"),("金匮传真","传真_金匮要略传真.txt"),
       ("C卷","C_jingfangliyu.txt"),("解读","ocr_解读张仲景医学.txt")]
T = {n: re.sub(r"\s+","",open(os.path.join(B,"sources",f),encoding="utf-8",errors="ignore").read())
     for n,f in SRC if os.path.exists(os.path.join(B,"sources",f))}
AN = re.compile(r"(?:【按】|按：)(.{10,420}?)(?=\d{1,3}[．.]|【|《|$)")
JX = re.compile(r"鉴别|之别|不同|相似|相类|须辨|宜辨|辨之|区别|之分|有别")
ZHENG = ["心下痞硬","心下痞","心下急","心下满痛","腹满而喘","喘满","腹满","腹痛",
         "发热恶寒","发热不恶寒","往来寒热","潮热","身大热","身重","下利","协热利",
         "大便硬","小便不利","小便清","小便赤","渴欲饮水","但欲漱水不欲咽","口渴","不渴",
         "背恶寒","口中和","口舌干燥","头痛发热","喘家","鼻衄","谵语","目直视",
         "热在表","热在里","热在半表半里","热在胃","热在血分"]
assert all(len(w)>=2 for w in ZHENG), "⛔协议15：指征词表出现单字"
ZH = re.compile("|".join(map(re.escape, sorted(ZHENG,key=len,reverse=True))))
tot, rows, drop = 0, [], Counter()
for n in T:
    for m in AN.finditer(T[n]):
        tot += 1; t = m.group(1)
        if not JX.search(t): drop["无鉴别语"] += 1; continue
        zs = list(dict.fromkeys(ZH.findall(t)))
        if not zs: drop["有鉴别语但无指征词"] += 1; continue   # ⛔失效模式①
        rows.append(dict(book=n, zheng=zs, txt=t,
                         layer="[冯]编次层" if "传真" in n and "老师" in t else "[HXS]"))
print("═══ 【特异指征反噬表·按语路径】═══")
print("按语块 **%d**（%s）｜含鉴别语且含指征词者 **%d**｜⛔弃：%s"
      % (tot, "／".join("%s %d" % (n, len(list(AN.finditer(T[n])))) for n in T), len(rows), dict(drop)))
# ⛔金标准复核〔㊹〕
gold = [r for r in rows if "心下痞硬" in r["zheng"] and "虚实" in r["txt"]]
print("\n⛔⭐[**金标准复核**]74批漏召之「心下痞硬·大柴胡(实) vs 人参(虚)」：**%s**"
      % ("✅召回" if gold else "**仍漏**"))
if gold: print("   〔%s〕「%s」" % (gold[0]["book"], gold[0]["txt"][:120]))
zc = Counter(z for r in rows for z in r["zheng"])
print("\n⭐**被鉴别之指征·频次**：%s" % dict(zc.most_common(14)))
print("\n═══ 逐条（**归属以原文自述为准，不自动定性**）═══")
for r in rows:
    print("  〔%s·%s〕指征：%s\n     %s" % (r["book"], r["layer"], "／".join(r["zheng"]), r["txt"][:190]))
assert not ZH.findall("子虚乌有绝无一词"), "⛔自检失败：虚构句命中指征词"
assert ZH.findall("心下痞硬"), "⛔自检失败：真指征未命中"
print("\n[自检] 虚构句零命中｜真指征命中")
json.dump(rows, open(os.path.join(B,"term_layer","_fanshi_anyu.json"),"w"), ensure_ascii=False, indent=1)
L = ["# 附录O2（改版）：特异指征反噬表·按语路径（76批·清账②完成）","",
     "> ⛔**74批之结论**：「反噬关系多在【按语】里，不在【辨证要点】里。本工具只读要点，够不着。」",
     "> ⭐**76批条件变化**：用户补入《伤寒论传真》《金匮要略传真》，共 **352 个【按】块** → 路径打通。",
     "> ⭐**且 74批漏召之金标准，在新书中逐字命中**：",
     "> 「**心下急甚者，则痞硬，与人参所主的心下痞硬有虚实之别，须参照其余脉证辨之。**」","",
     "## 一、产出", "",
     "| 项 | 值 |","|---|---|",
     "| 按语块总数 | **%d** |" % tot,
     "| 含鉴别语且含指征词者 | **%d** |" % len(rows),
     "| 金标准（心下痞硬虚实之别） | **%s** |" % ("✅召回" if gold else "仍漏"),"",
     "## 二、逐条（**归属以原文自述为准，不自动定性**）",""]
for r in rows:
    L += ["### %s〔%s·%s〕" % ("／".join(r["zheng"]), r["book"], r["layer"]), "", "> %s" % r["txt"][:400], ""]
L += ["## 三、执行含义","",
      "**凡上表所列之指征，⛔单独出现时不得作任何方之准入，须先取原文所指之鉴别项。**",
      "→ 与执行核 1.4【背恶寒同症二机制】、3.4【特异指征反噬】同源。"]
open(os.path.join(B,"term_layer","附录O2_特异指征反噬表.md"),"w").write("\n".join(L))
print("→ term_layer/附录O2_特异指征反噬表.md（改版）")
