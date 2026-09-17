#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「首位」之五种地位分列（126AL 立·上级令二）

⛔⛔ **本工具之唯一职责：把上级所列之五种「首位」【分开测量】，并报其【不一致】。**
　　⛔ **它⛔ 不判断哪一种是「主要矛盾」，⛔ 不作任何医学推论。**

上级 126AL 原话：
> 「要把几个可能不同的『首位』分开：**方名首药｜组成首药｜最大用量｜作者所称主药｜决定选方的因素**。
> **它们何时一致、何时分离，正是要研究的关系，⛔ 不能预先视为同一件事。**」

本工具只测**前三种**（可机械测者）：

| 地位 | 本工具 | 何以 |
|---|---|---|
| **方名首药** | ✅ 测 | 方名内**首个出现之药名**；⛔ 方名无药名者记 `无`（⭐ 承气汤即此类） |
| **组成首药** | ✅ 测 | C卷【方剂组成】块之**书写顺序第一味** |
| **最大用量** | ⚠ **有条件测** | 见下「⛔⛔ 量之三重限度」 |
| **作者所称主药** | ⛔ **不测** | 须**人读**作者原文（「主要的还是……」「以 X 为主」）⇒ 本工具只给**检索入口** |
| **决定选方的因素** | ⛔ **不测** | 须读**换方／禁方／加减**之论述 ⇒ ⛔ 机械不可得 |

⛔⛔ **量之三重限度（⛔ 须与任何「最大用量」结论同读）**
  ① **C卷之剂量是【克】，而原方是【两／升／枚】** —— ⭐ **克是编者之换算，本身即一次编辑行为**。
     ⇒ 上级所要者是「**原方相对剂量**」（其例：当归**三两**、芍药**一斤**）；
     ⛔ **本工具所测是【C卷换算后之克】，⛔ 不是原方两数。**
  ② **单位不可通约**：`枚`（大枣4枚）、`合`、`升`、`把`、`分`⛔ 与 `克` 不可比 ⇒
     ⭐ **凡方内含不可通约单位者，本工具标 `量·不可比`，⛔ 不给最大用量。**
  ③ **C卷身份为 `uncertain`（P0）** —— 见 `docs/C卷_provenance调查_126批.md`。
     ⇒ ⛔ **由本工具所得之「组成首药／最大用量」，其归属只可记 `source_unattributed`，
        ⛔ 不得记作「胡老之方」。**

用法：
    python3 tools/shouwei_diwei.py                # 全表 ＋ 不一致统计
    python3 tools/shouwei_diwei.py --disagree     # 只报三地位不一致者
    python3 tools/shouwei_diwei.py --name 当归芍药散
"""
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, "tools"))
import corpus_guard  # noqa: E402

# ⛔ 与 fang_compose.py 同一词表（⛔ 不另立，避免两处各改各的）。
YAO = (r"(桂枝|芍药|白芍|甘草|生姜|干姜|大枣|麻黄|杏仁|石膏|柴胡|黄芩|半夏|人参|附子|白术|苍术|"
       r"茯苓|泽泻|猪苓|大黄|芒硝|厚朴|枳实|栀子|黄连|黄柏|当归|川芎|芎䓖|地黄|阿胶|细辛|五味子|"
       r"吴茱萸|龙骨|牡蛎|葛根|栝蒌根|瓜蒌根|栝蒌|瓜蒌|贝母|桔梗|防己|黄芪|薏苡仁|桃仁|丹皮|知母|竹叶|"
       r"旋覆花|代赭石|滑石|车前子|乌梅|川椒|蜀漆|皂荚|葶苈子|射干|紫菀|款冬花|白头翁|"
       r"秦皮|赤石脂|禹余粮|升麻|鳖甲|水蛭|虻虫|大戟|甘遂|芫花|巴豆|瓜蒂|赤小豆|文蛤|粳米|"
       r"知母|麦冬|天冬|竹茹|生地|玄参|牡丹皮|王不留行|丹参|茵陈|乌头|细辛|"
       # ⭐ 126AL 补：以下皆为**逐条过目不一致表时**发现之词表缺项，
       #   ⛔ 缺一味就会使「方名首药」解析到**后一味**上，制造**假的不一致**。
       r"薏苡|薤白|薙白|橘皮|羊肉|通草|百合|蜃虫|䗪虫|败酱|葵子|柏叶|文蛤)")

# ⭐ 异写归一（⛔ 只归**同物异名**，⛔ 不归同类不同物）
ALIAS = {"栝蒌": "瓜蒌", "栝蒌根": "瓜蒌根", "白芍": "芍药", "芎䓖": "川芎", "牡丹皮": "丹皮",
         # ⭐ 126AL 补（皆逐条过目所得，⛔ 不是猜的）：
         "薏苡": "薏苡仁", "薙白": "薤白", "生地": "地黄", "瓜蒌根": "瓜蒌"}

# ⛔⛔ **方名口径之限度**：下列形态之方名，其「首药」⛔ **不可与单方同口径比较**。
#   ⭐ 126AL 逐条过目所得 —— 不标出它们，就会把**口径问题**误报成**实质不一致**。
COMPOUND = re.compile(r"加|去|合|[一二三四五六七八九十]汤|新加|或丸")
ABBREV = re.compile(r"^(苓桂|苓甘|苓姜|柴胡桂枝干姜|桂枝二|桂枝麻黄)")

# ⛔ 与「克」不可通约之单位
INCOMPARABLE = "枚合升把分斗石尺片字"


def norm(y):
    """⛔⛔ **须【链式】归一** —— 126AL 实测之一处 bug：
    `栝蒌根 → 瓜蒌根` 与 `瓜蒌根 → 瓜蒌` 分作两条，而单次 `ALIAS.get` **只走一步**，
    于是方名之「栝蒌」归到 `瓜蒌`、组成之「栝蒌根」只归到 `瓜蒌根` ⇒ **误报为不一致**。
    ⇒ 迭代到不动点（⛔ 设上限防环）。
    """
    for _ in range(4):
        n = ALIAS.get(y, y)
        if n == y:
            return y
        y = n
    return y


def parse_blocks():
    """从 C卷【方剂组成】块取【保序】之药味与剂量。

    ⛔ **保序是本工具存在的理由** —— `state_layer/方剂组成.json` 之值是
    **排序后的集合**（实测 `桂枝汤 => ['大枣','桂枝','甘草','生姜','芍药']`，
    字典序），⇒ ⭐ **组成顺序已被销毁**，故⛔ 不能用它答「组成首药」。
    """
    c = corpus_guard.load_one("C卷")
    rows = re.findall(r"([一-鿿]{2,14}(?:汤|散|丸|饮))方?\s*【方剂组成】([^【]{4,240})", c)
    out = []
    for name, comp in rows:
        items, seen = [], set()
        for m in re.finditer(YAO + r"(?:（[^）]{0,8}）)?\s*(\d{0,3}(?:\.\d)?)\s*([克枚合升把分两])?", comp):
            y = norm(m.group(1))
            if y in seen:            # ⛔ 同方内重出只取首见（⛔ 不累加：可能是注文复述）
                continue
            seen.add(y)
            qty = m.group(2)
            unit = m.group(3) or ""
            items.append((y, float(qty) if qty else None, unit))
        if items:
            out.append((name, items))
    return out


def name_first_drug(name):
    """方名首药 ＝ 方名内**首个出现之药名**；⛔ 方名无药名者 ⇒ None。

    ⭐ **承气汤即 None**（上级 126AL 特别注明：「方名没有以大黄开头」）。
    ⚠ 「小柴胡汤」之首药记 **柴胡**（⭐ 取**首个药名**，⛔ 不取首字——「小」非药）。
    """
    m = re.search(YAO, name)
    return norm(m.group(1)) if m else None


def name_caveat(name):
    """⭐ 126AL 立：**方名口径之警示**，⛔ 不改判，只标。

    ⛔⛔ **为何必须有这一格**：逐条过目 126AL 首轮之 44 条「不一致」，
      发现其中一大批**根本不是实质不一致**，而是**方名口径不可比**：
      · **加减方／合方**（白虎**加**桂枝汤、桂枝**去**桂加白术汤、桂枝二麻黄一汤）——
        ⭐ 其名之首药常是**所加之药**，⛔ 不是该方之首药；
      · **简称方**（**苓桂**五味甘草汤、**苓甘**五味姜辛…）——
        ⭐ 「苓」「甘」是**缩写**，⛔ 不是完整药名，正则解析必错；
      · **OCR 残名**（「加芍药生姜各一两人参三两新加汤」本应作「桂枝加芍药…」）。
    ⇒ ⭐ **凡带本警示者，其「方名首药」一栏⛔ 不得计入一致／不一致之统计。**
    """
    tags = []
    if COMPOUND.search(name):
        tags.append("加减／合方")
    if ABBREV.search(name):
        tags.append("简称")
    if len(name) >= 10:
        tags.append("长名·疑 OCR")
    return tags


def max_dose(items):
    """最大用量。⛔ 三种情形返回 (None, 理由)：
       ① 方内有**不可通约单位**（枚／合／升…）⇒ ⛔ 不给
       ② 有药**无剂量**⇒ ⛔ 不给
       ③ **并列最大**（两味同量）⇒ 返回全部并列者
    """
    units = {u for _, _, u in items if u}
    if units & set(INCOMPARABLE):
        return None, "量·不可比（含 %s）" % "／".join(sorted(units & set(INCOMPARABLE)))
    if any(q is None for _, q, _ in items):
        miss = [y for y, q, _ in items if q is None]
        return None, "量·缺（%s）" % "、".join(miss[:3])
    mx = max(q for _, q, _ in items)
    win = [y for y, q, _ in items if q == mx]
    return win, "%.0f克" % mx


def main():
    av = sys.argv[1:]
    only_dis = "--disagree" in av
    pick = av[av.index("--name") + 1] if "--name" in av else None

    data = parse_blocks()
    print("═══ 「首位」五种地位之分列测量（126AL）═══")
    print("C卷【方剂组成】块 **%d** 个｜⛔ C卷身份 `uncertain`(P0) ⇒ 归属只可记 `source_unattributed`\n" % len(data))
    print("⛔⛔ 本工具**只测前三种**；**作者所称主药**与**决定选方的因素**须**人读**，⛔ 机械不可得。\n")

    n_name_none = 0
    n_caveat = 0
    agree12 = dis12 = 0
    agree13 = dis13 = 0
    nomax = 0
    dis_rows = []
    for name, items in data:
        if pick and pick != name:
            continue
        nf = name_first_drug(name)
        cf = items[0][0]
        mx, why = max_dose(items)
        cav = name_caveat(name)
        if cav:                      # ⛔ 口径不可比 ⇒ 不进任何统计
            n_caveat += 1
        if nf is None:
            n_name_none += 1
        elif not cav:
            if nf == cf:
                agree12 += 1
            else:
                dis12 += 1
        if mx is None:
            nomax += 1
        elif nf is not None and not cav:
            if nf in mx:
                agree13 += 1
            else:
                dis13 += 1
        bad = (not cav and nf is not None
               and (nf != cf or (mx is not None and nf not in mx)))
        if bad:
            dis_rows.append((name, nf, cf, mx, why))
        if pick or (not only_dis) or bad:
            print("· %-16s 方名首药=%-6s 组成首药=%-6s 最大用量=%-14s %s%s"
                  % (name, nf or "⛔无", cf, ("、".join(mx) if mx else "⛔" + why),
                     ("　⚠ 不一致" if bad else ""),
                     ("　⛔ 口径不可比：" + "／".join(cav) if cav else "")))

    if pick:
        return 0
    print("\n── 统计（⛔ 只是计数，⛔ 不是结论）──")
    print("  ⛔ **方名口径不可比**（加减／合方／简称／疑 OCR）：**%d** 方 ⇒ ⛔ **已排除出下列统计**" % n_caveat)
    print("  方名**无药名**者（⭐ 承气汤类）：**%d** 方 ⇒ ⛔ 该类**无「方名首药」可言**" % n_name_none)
    print("  方名首药 vs 组成首药：一致 **%d**｜**不一致 %d**" % (agree12, dis12))
    print("  方名首药 vs 最大用量：一致 **%d**｜**不一致 %d**｜⛔ 不可测 **%d**"
          % (agree13, dis13, nomax))
    print("\n⛔⛔ **量之三重限度**（见 docstring）：①C卷之克是**编者换算**，⛔ 非原方两数；"
          "②`枚/合/升` 不可通约；③C卷身份 `uncertain`。")
    print("⛔ **以上数字⛔ 不支持任何「首药＝主药」之结论** —— 它们只说明**三种地位并不重合**。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
