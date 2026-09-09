#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""zichan_ditu.py —— 【全系统资产地图】(112批·用户令：暂停加规则，先做资产地图)

## 用户 112批 令（逐字）
「**暂停继续增加R规则。**否则很可能再做50批还是同一个问题。」
「第一任务不是改规则，而是做一张**全系统资产地图**……然后逐条判断：
 保留／合并／下沉／升格／降级／删除／隔离／待核。」

## ⛔ 用户五处指控，执行线逐条核实：**全部属实**
① v7.9 头部与 **v7.4 残留同存**：L6344「引擎 v7.4.1 完整版」｜L6456「底层公理集 v7.4」｜
   L15136「诊断框架 v7.4·三步主干」——**7 处 v7.4 结构块活在 v7.9 文件里。**
② **测试数据在执行文件内**：L300/L15485「98.0%」｜L15558「遮盖真值 66.7%」｜L15560「保守下界 60.0%」。
③ ⛔⛔**最重一处**：L6311「首选：三物黄芩汤｜置信度 35%」**至今仍在**；
   而 **L1919 引擎自己已写**：「**本案已有 B 级最硬证据未被纳入：G13「苓桂术甘汤→眩显著缓解」
   ＝治疗反应＝干预实验……以形态类比推翻一个已被治疗反应证实的轴，是降级不是升级。**」
   ⇒ **引擎不但错，而且【自己已经写下自己错了】，写下之后那条错的排序至今未改。**
   ⇒ **此非「不知道」，是「知道了而没有回改」。比不知道严重。**

用法：python3 tools/zichan_ditu.py            # 出资产地图
     python3 tools/zichan_ditu.py --r         # 只出 R1–R104 逐条分类
"""
import os, re, sys
from collections import Counter, OrderedDict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENG = os.path.join(B, "hxs_engine_v79_full.md")
OUT = os.path.join(B, "term_layer", "资产地图.md")

# 用户 112批 所立之七层
LAYER = OrderedDict([
 ("L0 原始资料", r"逐字|原文|〔A·|仲景|《伤寒论》第|《金匮"),
 ("L1 概念本体", r"定义|即指|是指|所谓|何谓|八纲|六经之名|太过|不及"),
 ("L2 观察证据", r"脉|舌|汗|恶寒|恶热|渴|大便|小便|腹诊|证象|观察项"),
 ("L3 辨证算法", r"演算|排除|幸存|候选|三步|主干|流程|步骤|调度"),
 ("L4 方证知识", r"方证|辨证要点|【方解】|加减|合方|鉴别"),
 ("L5 时间反馈", r"传变|合病|并病|初诊|二诊|治疗反应|服后|瞑眩"),
 ("L6 安全", r"禁忌|不可|绝不可|红旗|安全|误治|坏病"),
 ("L7 测试", r"G\d+|W-\d|盲测|留出|通过率|金标准|遮盖|复现率"),
])
# 须隔离/删除者之特征
FLAG = OrderedDict([
 ("⛔版本冲突", r"v7\.[0-8]"),
 ("⛔测试资产入执行", r"通过率|98\.0%|66\.7%|60\.0%|金标准|G1[0-6]|W-1|W-2"),
 ("⛔臆造数值", r"置信度\s*\d+%|\+\d+%|×0\.\d"),
 ("⛔历史修正记录", r"[⑴-⿻]批|第\d+批|批订正|批撤|历批"),
])


def main():
    L = open(ENG, encoding="utf-8").read().split("\n")
    N = len(L)
    # R 条款切段
    # ⛔112批 自查之 bug 及其修正：初版以「下一 R 行」为界，致 R104 之后全文（方证卡片＋附录
    #   ＋测试记录，约 1 万行）被计入 R104，遂报「R 占 98.9%」。**此数错。**
    #   修正：R 块止于下一个【顶级块起始】——^R\d+ ／ ^【 ／ ^## ／ ^v7 ／ ^附录 ／ ^■ 皆为界。
    TOP = re.compile(r"^(R\d+[ 　]|【|##|v7\.|附录|■|框架版本)")
    idx = [i for i in range(N) if re.match(r"^R\d+[ 　]", L[i])]
    rs = []
    for k, i in enumerate(idx):
        j = i + 1
        while j < N and not TOP.match(L[j]):
            j += 1
        head = L[i]
        body = "\n".join(L[i:j])
        rid = re.match(r"^(R\d+)", head).group(1)
        rs.append((rid, i + 1, j - i, head.strip(), body))

    if "--r" in sys.argv:
        print("== R1–R%d 逐条分类（%d 条）==\n" % (len(rs), len(rs)))
        for rid, ln, sz, head, body in rs:
            lay = [k for k, p in LAYER.items() if re.search(p, body)]
            fl = [k for k, p in FLAG.items() if re.search(p, body)]
            print("%-6s L%-6d %4d行  层:%-28s %s"
                  % (rid, ln, sz, "/".join(x[:2] for x in lay) or "?",
                     "｜".join(fl)))
        return 0

    # 全文分区计量
    print("== 全系统资产地图（112批·用户令）==\n")
    print("引擎 %d 行。R 条款 %d 条，占 %d 行（%.1f%%）。\n"
          % (N, len(rs), sum(r[2] for r in rs), 100 * sum(r[2] for r in rs) / N))

    print("── 一·⛔ 须【隔离】者（用户所指之六类混装）──")
    for k, p in FLAG.items():
        hit = [i + 1 for i in range(N) if re.search(p, L[i])]
        print("  %-16s %5d 行  首见 L%-6d 末见 L%s"
              % (k, len(hit), hit[0] if hit else 0, hit[-1] if hit else "-"))
    print()

    print("── 二·各层行数分布（同一行可属多层，故合计 > 100%）──")
    for k, p in LAYER.items():
        n = sum(1 for x in L if re.search(p, x))
        print("  %-14s %6d 行 (%.1f%%)" % (k, n, 100 * n / N))
    print()

    print("── 三·⛔ 版本冲突之具体位置 ──")
    for i in range(N):
        if re.search(r"v7\.[0-8]", L[i]) and re.search(r"版|框架|公理|核心", L[i]):
            print("  L%-6d %s" % (i + 1, L[i].strip()[:76]))
    print()

    print("── 四·⛔ 引擎自承之错而未回改者（最重）──")
    print("  L1919  引擎自写：「本案已有 B 级最硬证据未被纳入：G13『苓桂术甘汤→眩显著缓解』」")
    print("  L6311  而错的排序至今仍在：「首选：三物黄芩汤｜置信度 35%」")
    print("  ⇒ **知道了而没有回改。此为本工程最严重之单点。**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
