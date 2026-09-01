#!/usr/bin/env python3
"""【服后反证表】——**服药后的反应可反证原判**（78批·上级新增判据类型·引擎从未有过）。

## 立表锚（A级·逐字·已验）
  〔§243〕「食谷欲呕，属阳明也，吴茱萸汤主之。**得汤反剧者，属上焦也。**」
  〔胡老注〕「属阳明，**这里是指胃，不是指阳明病**……若**服吴茱萸汤而呕反增剧者，
    是误犯上焦有热的呕，不当用本方治之**。」
  〔胡老按〕「**属上焦是暗示小柴胡汤证**，由于欲呕为二方的共有证，故特提出教人临证时要细心辨别。」
  → ⭐**这不是普通禁忌，是「特定方的特定反应，指向特定的替代方证」——比医源反证精细一级。**

## 与既有判据之别
  · **禁忌**：用前即知不可用。
  · **医源反证**（R54/坏病）：误治后状态改变，须重新辨。
  · ⭐**服后反证（本表）**：**用后之反应，回过头否定原判，并指向替代方证。**
    → **它把「治疗」变成「诊断工具」**〔与 §209 小承气试之「虽说试之，实即治之」同族〕。

【已知失效模式】(视角㉕)
  ① 「反剧/愈甚」亦可指**瞑眩**（药中病之暝眩反应）——**二者方向相反，绝不可混。**
     → **须句中含「不当用／非其治／误」类否定语方收为反证；含「瞑眩／中病」者另列。**
  ② 服后反应之描述常在【按】中，而按语体例各书不同〔76批已验〕。
  ③ 反应词表必不全；报「已抽到的」，不称「全部」〔R41戊〕。
【口径】(视角㊱) 一条＝一处服后反应句；`python3 tools/fuhou_fanzheng.py` 复跑。
"""
import re, os, json
from collections import Counter
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = {}
for f in sorted(os.listdir(os.path.join(B, "sources"))):
    if f.endswith(".txt") and f != "MD5SUMS.txt":
        T[f.replace(".txt", "")] = re.sub(r"\s+", "", open(os.path.join(B, "sources", f),
                                          encoding="utf-8", errors="ignore").read())
# ⛔78批首跑精确率过低（「药后少食稀粥」「服后诸证已」皆被收入）：
#   **反证之定义是「反应与预期相反」，不是任何服后描述。** 故 REACT 只收**不良/相反**反应。
REACT = re.compile(r"((?:得汤|服之|服后|药后|服[^，。]{0,8}汤[^，。]{0,4})"
                   r"(?:反|则|而)?[^，。；]{0,6}"
                   r"(?:反剧|增剧|愈甚|益甚|不止|不解|反烦|则厥|则痉|则死|反重|转剧|加剧|反甚))")
# ⛔否定语须在**反应之后 60 字内**，否则是别处的「误」被误捕
NEG = re.compile(r"不当用|非其治|误犯|不可与|不宜|非本方|属上焦|此为逆|为坏病")
MX  = re.compile(r"瞑眩|暝眩|瞑眠|中病|药中病")
rows, mx, drop = [], [], Counter()
for bk in T:
    for m in REACT.finditer(T[bk]):
        ctx = T[bk][max(0, m.start() - 150):m.start() + 170]
        if MX.search(ctx): mx.append((bk, m.group(0), ctx)); continue      # ⛔失效模式①
        post = T[bk][m.end():m.end() + 60]      # ⛔否定语须紧随反应之后
        if not NEG.search(post): drop["反应后60字内无否定语"] += 1; continue
        rows.append(dict(book=bk, hit=m.group(0), ctx=ctx))
seen, uniq = set(), []
for r in rows:
    k = r["ctx"][-70:]
    if k in seen: continue
    seen.add(k); uniq.append(r)
print("═══ 【服后反证表】═══")
print("服后反应句候选 %d ｜⛔剔「反应后60字内无否定语」%d ｜⛔另列「瞑眩/中病」%d（方向相反，不得混）"
      % (len(rows) + drop["反应后60字内无否定语"], drop["反应后60字内无否定语"], len(mx)))
print("⭐**书内去重后 %d 条**" % len(uniq))
# ⭐跨书去重：同一条文在十二书中重出，按书去重会把 1 类数成 N 条〔67批同型〕
import hashlib
xs, xd = set(), []
for r in uniq:
    key = re.sub(r"[^一-鿿]", "", r["ctx"])[:26]
    k2 = hashlib.md5(key.encode()).hexdigest()[:8]
    if k2 in xs: continue
    xs.add(k2); xd.append(r)
KEY = {}
for r in uniq:
    core = ("吴茱萸汤·得汤反剧" if "反增剧" in r["ctx"] or "得汤反剧" in r["hit"] else
            "大青龙汤·服之则厥逆筋惕肉瞤" if "筋惕" in r["ctx"] else "其他")
    KEY.setdefault(core, []).append(r["book"])
print("⭐⭐**跨条文归类后实为 %d 类**（同一条文在十二书中重出）：" % len(KEY))
for k, v in KEY.items(): print("   · **%s** —— 见于 %d 书" % (k, len(set(v))))
print("⛔**故「服后反证」在本语料中是稀有判据类型，不是成规模的一层。如实报。**")
print("\n═══ 逐条 ═══")
for r in uniq[:20]:
    print("  〔%s〕**%s**\n     …%s…" % (r["book"], r["hit"][:16], r["ctx"][-190:]))
print("\n═══ ⛔另列：瞑眩/中病（药中病之反应，**与反证方向相反**）═══")
for bk, h, c in mx[:6]:
    print("  〔%s〕**%s** …%s…" % (bk, h[:14], c[-150:]))
# ⛔自检〔㊹〕
assert REACT.search("得汤反剧者属上焦也"), "⛔自检失败：真反证句未命中"
assert not REACT.search("子虚乌有绝无一词"), "⛔自检失败：虚构句命中"
assert MX.search("此为瞑眩，药中病也"), "⛔自检失败：瞑眩未被识别"
assert MX.search("此为瞑眩，药中病也"), "⛔自检失败：瞑眩未被识别"
assert not REACT.search("服后诸证已"), "⛔自检失败：向愈之反应被误收为反证"
assert REACT.search("服吴茱萸汤而呕反增剧者"), "⛔自检失败：金标准未召回"
print("\n[自检] 金标准召回｜向愈反应被剔｜瞑眩另列｜虚构句零命中")
json.dump(dict(fanzheng=uniq, mingxuan=[dict(book=b, hit=h, ctx=c) for b, h, c in mx]),
          open(os.path.join(B, "term_layer", "_fuhou.json"), "w"), ensure_ascii=False, indent=1)
L = ["# 附录P：服后反证表（78批·上级新增判据类型·引擎从未有过）", "",
     "> ⭐**立表锚**〔A·§243＋胡老注按·逐字〕",
     "> 「食谷欲呕，属阳明也，吴茱萸汤主之。**得汤反剧者，属上焦也。**」",
     "> 注：「属阳明，**这里是指胃，不是指阳明病**……若**服吴茱萸汤而呕反增剧者，是误犯上焦有热的呕，不当用本方治之**。」",
     "> 按：「**属上焦是暗示小柴胡汤证**，由于欲呕为二方的共有证，故特提出教人临证时要细心辨别。」", "",
     "## ⭐ 与既有判据之别", "",
     "| 类型 | 时点 | 作用 |", "|---|---|---|",
     "| 禁忌 | **用前** | 不可用 |",
     "| 医源反证（坏病） | 误治后 | 状态改变，重新辨 |",
     "| ⭐**服后反证（本表）** | **用后** | **反应回过头否定原判，并指向替代方证** |", "",
     "→ ⭐**它把「治疗」变成「诊断工具」**（与 §209 小承气试之「虽说试之，**实即治之**」同族）。", "",
     "⛔**瞑眩（药中病之反应）与本表方向相反，已另列，绝不可混。**", "",
     "## 一、反证句（去重 %d 条）" % len(uniq), "",
     "| 出处 | 反应 | 原文 |", "|---|---|---|"]
for r in uniq:
    L.append("| %s | **%s** | …%s… |" % (r["book"], r["hit"][:18], r["ctx"][-150:].replace("|", "｜")))
L += ["", "## 二、⛔另列：瞑眩／中病（%d 条·方向相反）" % len(mx), ""]
for bk, h, c in mx:
    L.append("- 〔%s〕**%s** …%s…" % (bk, h[:16], c[-150:]))
L += ["", "## 三、执行含义", "",
      "**方已投而反应与预期相反者，⛔不得径判「药力不足」或「病重药轻」，",
      "须先按本表复核原判——特定方之特定反应，可指向特定替代方证。**",
      "〔样本：吴茱萸汤服后呕反剧 → 非胃寒，乃上焦热 → 转小柴胡汤〕"]
open(os.path.join(B, "term_layer", "附录P_服后反证表.md"), "w").write("\n".join(L))
print("→ term_layer/附录P_服后反证表.md")
