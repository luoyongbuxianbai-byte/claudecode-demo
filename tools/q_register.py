#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/q_register.py —— Q 系列待查问题之**出现位置索引**（126L 立）

⛔⛔ 本工具之能力边界，须先读：

  它做的**只有一件事**：在 evidence/ 与 reports/ 内，对形如 `Q-0NN` / `P0-0NN` / `T-<批>-N`
  之**字符串**做出现位置索引，并报每个编号**首见于何文件**、**共见几处**。

  ⛔ 它**不**判断该问题是否已解决；
  ⛔ 它**不**抽取问题内容（只取同段落首句作提示，⚠ 提示可能截错）；
  ⛔ 它**不**证明「编号已穷举」——凡未用此写法（如写作「Q14」「问题十四」）者，**一律漏检**。
     ⇒ 这是 **B 类 lexical_false_negative** 之已知暴露面，⛔ 报数时必须一并声明。

  ⇒ 因此本工具之输出**只能**回答「**某编号在哪些文件里被提到过**」，
    ⛔ **不能**回答「共有多少个待查问题」或「哪些已闭合」。

⛔⛔ 126L 自查（本工具**两版皆错**，如实留档）：
  初版设一栏名「**可判死**」，据「编号附近是否出现『失败条件』『搁置条件』**字样**」判定。
  ⇒ 这是**词面检测**，栏名却是**语义判断**——**GATE_2「四问不得互推」之违规**。
  实证：Q-015／Q-016 之失败条件写在 126K §四之**表格列内**，不含该四字字样，
        且距编号行 >6 行 ⇒ 初版误报「⛔无」**两个假阴性**。
  **第二版**：改栏名为「近处见闭合语」并加大窗口，⛔ **仍不够**——立册当批，
  `evidence/待查登记_Q系列_126L.md`（八条**提案**）与本批报告都在逐条讨论这些条件，
  ⇒ 工具随即把 28 个编号**全部**刷成「见」，⭐ **全绿而实际一条未裁**。
  试以「排除提案册」补救，亦失败：**报告文件同样在讨论提案，词面无从区分
  【陈述已裁之条件】与【讨论提案中之条件】**。
  ⚠ 并与 126E 之 G 类同型：**我自己写的提案，被我自己的工具当成了已完成之证据**。

  ⇒ ⭐⭐ **第三版之结论：这是语义判定，词面永远做不到** ⇒ **停止用词面推语义**。
    判定移交 `rules/q_status_v0.json`（**人工维护**），本工具**只做出现位置索引并读取该表**。
    ⛔ 本工具永不判定、永不改写该表。这是 GATE_2「四问不得互推」之正面执行。

⛔⛔ 126M 再订（上级线令二驳回 126L 之单一 status 枚举）：
  ①问题分三类，各有各的完成判据，**不共用一套**：
     hypothesis            ⇒ 可检验预测 ＋ 反驳条件
     attribution_definition⇒ 证据要求   ＋ 阶段性停止条件（⛔ 不是证伪条件）
     survey_task           ⇒ 范围       ＋ 完成标准（⛔ 本就不该有证伪条件）
  ②「条件已写出」「条件已审定」「问题已解决」是**三个独立维度**，⛔ 不得共用一格
     ⇒ 现读 condition_written／ratified／resolved 三字段。
  ③`ratified` 须有**具体裁决出处**，⛔ 不因 Code 当批写了条件便自动成为已审定。
  ④⛔ **撤回 126L 之「无失败条件 ⇒ 不是研究项，是债务」**——
     上级令二：**开放问题暂时没有证伪条件，不等于没有研究价值**。
  ⑤`unassessed` 只说明**本登记册**尚未评估，⛔ 不能反推历史上从未评估。
     ⚠ 实证：126L 把 Q-011／Q-011b/c/d 记为 unassessed，
     而 126I:246-258 中 Q-011 明标「作废，拆为四」且四子项**各自写明失败条件**
     ⇒ 那是**以新表重写历史**，不是发现缺口。

用法：
  python3 tools/q_register.py            # 索引全部
  python3 tools/q_register.py --missing  # 只列**近处未见闭合语字样**者 ⇒ ⛔ 这是人工核验清单，不是结论
"""
import os, re, sys, collections

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ["evidence", "reports"]
PAT = re.compile(r"\b(Q-\d{3}[a-d]?|P0-\d{3}|T-[0-9]{3}[A-Z]?-\d+)\b")
# ⛔ 下列写法**不被本式覆盖**，须在报头声明
UNCOVERED = ["Q14 / Q-14（无前导零）", "「问题十四」等中文序号", "跨行断开之编号", "编号出现在 rules/、schema/、term_layer/ 内者（本工具不扫这些目录）"]
STATUS_FILE = "rules/q_status_v0.json"   # ⭐ 人工维护之状态表；⛔ 本工具只读不写


def scan():
    hits = collections.defaultdict(list)   # id -> [(relpath, lineno, line)]
    files = 0
    for d in DIRS:
        root = os.path.join(B, d)
        if not os.path.isdir(root):
            continue
        for fn in sorted(os.listdir(root)):
            if not fn.endswith(".md"):
                continue
            files += 1
            rel = os.path.join(d, fn)
            with open(os.path.join(root, fn), encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    for m in set(PAT.findall(line)):
                        hits[m].append((rel, i, line.strip()))
    return hits, files


def sortkey(q):
    m = re.search(r"(\d+)", q)
    return (q.split("-")[0], int(m.group(1)) if m else 0, q)


def main():
    only_missing = "--missing" in sys.argv
    hits, files = scan()
    import json
    sf = os.path.join(B, STATUS_FILE)
    status = json.load(open(sf, encoding="utf-8"))["items"] if os.path.exists(sf) else {}

    print("═══ Q/P0/T 编号出现位置索引（126L 立）═══")
    print("⛔ 本表只报**编号在何处被提到**。⛔ 不报「共有多少待查问题」，⛔ 不报「哪些已闭合」。")
    print("⛔ 未覆盖之写法（⇒ 必有漏检，B 类）：")
    for u in UNCOVERED:
        print("   ·", u)
    print("扫描：%s 下 %d 个 .md\n" % ("／".join(DIRS), files))

    rows = []
    for q in sorted(hits, key=sortkey):
        occ = hits[q]
        first = occ[0]
        # ⛔ 此处只做**字样**匹配。⛔ 阳性不证明有失败条件，阴性不证明没有。
        it = status.get(q)
        if it is None:
            kind, cond, rat, res = "unregistered", "-", "-", "-"
        else:
            kind = it.get("kind", "?")
            cond = it.get("condition_written") or "⛔未写"
            rat = "✔" if it.get("ratified") else "⛔未审"
            res = it.get("resolved", "?")
        rows.append((q, len(occ), first[0], first[1], kind, cond, rat, res))

    shown = [r for r in rows if (not only_missing) or (r[5] == "⛔未写")]
    print("⭐ 下列四栏全部读自**人工维护**之 %s；⛔ 本工具不作任何判定。" % STATUS_FILE)
    print("⛔ 三栏正交：条件写出 ≠ 条件审定 ≠ 问题已解决。")
    print("%-10s %4s  %-22s %-8s %-6s %-8s %s" % ("编号", "处数", "类", "条件写于", "已审", "状态", "首见"))
    print("-" * 96)
    for q, n, rel, ln, kind, cond, rat, res in shown:
        print("%-10s %4d  %-22s %-8s %-6s %-8s %s:%d" % (q, n, kind, cond, rat, res, rel, ln))

    import collections as _c
    print("\n索引到编号 %d 个（⛔ 此数不是待查问题总数，见报头）。" % len(rows))
    # ⛔⛔ 126N 订正：126M 报告把**本工具之分布**当作**登记表之分布**抄走，
    #    把 survey_task 报成 3（实为 4——Q-019 只在 rules/ 里，本工具不扫该目录故未索引到）。
    #    ⇒ 分布须以**登记表**为准；本工具之索引结果另行分列，⛔ 二者不得互代。
    print("\n── 类别分布（⭐ 以**登记表** %s 为准，共 %d 项）──" % (STATUS_FILE, len(status)))
    print("   " + "｜".join("%s %d" % (k, v) for k, v in
                           sorted(_c.Counter(v.get("kind", "?") for v in status.values()).items())))
    print("── 状态分布（同上，以登记表为准）──")
    print("   " + "｜".join("%s %d" % (k, v) for k, v in
                           sorted(_c.Counter(v.get("resolved", "?") for v in status.values()).items())))
    _unindexed = sorted(set(status) - {r[0] for r in rows})
    if _unindexed:
        print("⚠ 登记表中有 %d 项**本工具未索引到**（只扫 evidence/、reports/ 之 .md）：%s"
              % (len(_unindexed), "、".join(_unindexed)))
        print("   ⛔ 故上面『索引到 %d 个』**小于**登记表实数 %d ⇒ ⛔ 不得以索引数替代表内实数。"
              % (len(rows), len(status)))
    nocond = [r[0] for r in rows if r[5] == "⛔未写"]
    if nocond:
        print("⚠ 下列 %d 个**尚未写出条件**：" % len(nocond) + "、".join(nocond))
        print("  ⛔ 这**不表示它们不是研究项**（126M 上级令二）——开放问题暂无证伪条件，仍可有研究价值。")
        print("  ⇒ 它们只是**还不能被判完成**；条件须按其 kind 分类拟定。")
    unrat = [r[0] for r in rows if r[6] == "⛔未审"]
    print("⛔ 条件**未经独立审定**者 %d 个 ⇒ ⛔ 不得以『Code 写过』充抵审定。" % len(unrat))
    print("⛔ 本表之 unregistered／未写，只说明**本登记册**尚未覆盖，")
    print("   ⛔ 不能反推历史读记中从未处理过——须回原读记实核。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
