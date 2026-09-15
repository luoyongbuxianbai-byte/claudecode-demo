#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_index.py —— 《学术报告主线索引》之生成与自检（126S·上级令）。

上级 126S 令：
  「在仓库建立《学术报告主线索引》，链接现有读记、证据册和研究纲领，
    **不复制重造证据矩阵**。按研究问题登记：当前命题、支持与反证、适用范围、
    状态、来源锚、拟进入报告的位置。**每批只更新受影响条目。**
    已撤回判断保留历史，但**不得继续作为现行结论被引用**。」

⛔ 本工具**只做三件事**：渲染、锚可达性检查、撤回引用检查。
⛔ 它**不判定**任何命题之真假，⛔ 不改 status——status 由人写入 JSON。

用法：
    python3 tools/report_index.py            # 渲染 + 自检
    python3 tools/report_index.py --check    # 只自检（不写文件），有红项则退出码 1
"""
import json
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(B, "rules", "report_index_v0.json")
OUT = os.path.join(B, "reports", "学术报告_主线索引.md")

STATUS_MARK = {
    "current": "⭐ 现行",
    "partial": "⚠ 部分（缺口已写明）",
    "open": "⛔ 未决",
    "retracted_registry": "⛔⛔ 撤回登记",
    "superseded": "⛔ 已被取代",
}


def anchor_path(a):
    """把 `path::locator` 之 locator 去掉，返回仓库相对路径。"""
    return a.split("::", 1)[0]


def check(d):
    """返回 (红项列表, 统计)。⛔ 只查可机械查者。"""
    red = []
    seen = set()
    n_anchor = 0
    for ch in d["chapters"]:
        for e in ch["entries"]:
            if e["id"] in seen:
                red.append("重复条目编号：%s" % e["id"])
            seen.add(e["id"])
            for a in e["anchors"]:
                n_anchor += 1
                p = anchor_path(a)
                if not os.path.exists(os.path.join(B, p)):
                    red.append("锚不可达：%s（条目 %s）" % (a, e["id"]))
            if e["status"] not in STATUS_MARK:
                red.append("status 非法：%s（条目 %s）" % (e["status"], e["id"]))
            # ⛔ 凡附注里写了「撤回」，须注明**哪一批**撤的 —— 无批次之撤回说明
            #    日后无法回查，等于把撤回变成一句无主的话。
            note = e.get("note", "")
            if "撤回" in note and not re.search(r"12[0-9][A-Z]", note):
                red.append("条目 %s 之附注写了「撤回」而未注明批次" % e["id"])
    # ⛔ 撤回登记必须存在——否则「保留历史」无处可放
    if not any(e["status"] == "retracted_registry"
               for ch in d["chapters"] for e in ch["entries"]):
        red.append("全表无 retracted_registry 条目：撤回历史无处保留")
    return red, dict(entries=len(seen), anchors=n_anchor)


def render(d):
    L = []
    L.append("# %s" % d["title"])
    L.append("")
    L.append("> ⛔ **本册由 `python3 tools/report_index.py` 从 `rules/report_index_v0.json` 确定性生成，勿手改。**")
    L.append("> 手改会与 JSON 分叉，而分叉正是「摘录变成断言」的起点。")
    L.append("")
    L.append("## 〇、最终交付")
    L.append("")
    L.append(d["deliverable"])
    L.append("")
    L.append("**本索引之用途**：%s" % d["purpose"])
    L.append("")
    L.append("### 纪律")
    L.append("")
    for x in d["discipline"]:
        L.append("- %s" % x)
    L.append("")
    # 目录
    L.append("### 章目与条目数")
    L.append("")
    L.append("| 章 | 研究问题 | 条目 | 现行 | 部分 | 未决 |")
    L.append("|---|---|---:|---:|---:|---:|")
    for ch in d["chapters"]:
        es = ch["entries"]
        cnt = lambda s: sum(1 for e in es if e["status"] == s)
        L.append("| **%d %s** | %s | %d | %d | %d | %d |"
                 % (ch["no"], ch["title"], ch["question"], len(es),
                    cnt("current"), cnt("partial"), cnt("open")))
    L.append("")
    L.append("---")
    for ch in d["chapters"]:
        L.append("")
        L.append("# 第 %d 章　%s" % (ch["no"], ch["title"]))
        L.append("")
        L.append("> **研究问题**：%s" % ch["question"])
        for e in ch["entries"]:
            L.append("")
            L.append("## `%s`　%s" % (e["id"], STATUS_MARK[e["status"]]))
            L.append("")
            L.append("| 项 | 内容 |")
            L.append("|---|---|")
            L.append("| **当前命题** | %s |" % e["proposition"])
            L.append("| **支持** | %s |" % e["support"])
            L.append("| **反证／缺口** | %s |" % e["counter"])
            L.append("| **适用范围** | %s |" % e["scope"])
            L.append("| **来源锚** | %s |" % "<br>".join("`%s`" % a for a in e["anchors"]))
            L.append("| **拟入报告位置** | %s |" % e["report_position"])
            if e.get("note"):
                L.append("| ⚠ **附注** | %s |" % e["note"])
    L.append("")
    return "\n".join(L) + "\n"


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    red, stat = check(d)
    only_check = "--check" in sys.argv
    if not only_check:
        open(OUT, "w", encoding="utf-8").write(render(d))
        print("已写 %s" % OUT)
    print("条目 %d｜锚 %d｜版本 %s" % (stat["entries"], stat["anchors"], d["version"]))
    if red:
        print("\n⛔ 红项 %d：" % len(red))
        for r in red:
            print("   · %s" % r)
        sys.exit(1)
    print("自检：✅ 锚全部可达，编号无重复，status 合法")
    print("⛔ 本自检**只查可机械查者**——它不证明命题为真，不证明证据充分。")


if __name__ == "__main__":
    main()
