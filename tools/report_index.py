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


def anchor_split(a):
    """`path::locator` ⇒ (path, locator or None)。"""
    if "::" in a:
        p, loc = a.split("::", 1)
        return p, loc
    return a, None


# ⛔ 上级 126T：定位符**逐步补检**，⛔ 不为此造大型工具。
#    现只认两种可机械判定的形态；其余一律记 not_checkable，⛔ 不冒充已检。
def locator_status(path, loc):
    """返回 'ok' | 'missing' | 'not_checkable'。"""
    if loc is None:
        return "not_checkable"          # 无定位符 ⇒ 本就只到文件级
    try:
        txt = open(os.path.join(B, path), encoding="utf-8").read()
    except Exception:
        return "missing"
    # 形态一：JSON 之顶层 key 或 items 之 key，写作 `::KEY` 或 `::a::b`
    if path.endswith(".json"):
        for part in loc.split("::"):
            for k in re.split(r"[,，]", part):
                k = k.strip()
                if not k:
                    continue
                if ('"%s"' % k) not in txt:
                    return "missing"
        return "ok"
    # 形态二：Markdown 之 §编号，写作 `::§8.7` / `::§二` / `::§3.1,§七` / `::§2.1-2.2`
    # ⚠⚠ 本册之标题行形如「## ⭐⭐ 七、…」「#### ⭐⭐⭐ 5.2b‴ …」「> ## ⛔⛔⛔ §〇 …」——
    #    编号前有标记、有时整行在引用块内。故**取出全部标题行，再看编号是否出现在某一标题行内**。
    # ⛔ 这是**包含**匹配，不是精确节号匹配：标题行里别处出现同一串亦算命中。
    #    ⇒ 报账时须照实说是「出现在某条标题行内」，⛔ 不得说成「该节存在且支持命题」。
    if loc.startswith("§"):
        heads = re.findall(r"^(?:>\s*)?#{1,6}\s+.*$", txt, re.M)
        parts = [x.strip() for x in re.split(r"[,，\-]", loc.replace("§", "")) if x.strip()]
        for k in parts:
            if not any(k in h for h in heads):
                return "missing"
        return "ok"
    return "not_checkable"


def check(d):
    """返回 (红项列表, 统计)。⛔ 只查可机械查者。"""
    red = []
    seen = set()
    n_anchor = 0
    n_file_missing = 0
    n_loc = {}
    for ch in d["chapters"]:
        for e in ch["entries"]:
            if e["id"] in seen:
                red.append("重复条目编号：%s" % e["id"])
            seen.add(e["id"])
            for a in e["anchors"]:
                n_anchor += 1
                p, loc = anchor_split(a)
                if not os.path.exists(os.path.join(B, p)):
                    red.append("锚之**文件**不存在：%s（条目 %s）" % (a, e["id"]))
                    n_file_missing += 1
                    continue
                st = locator_status(p, loc)
                n_loc[st] = n_loc.get(st, 0) + 1
                if st == "missing":
                    red.append("锚之**定位符**在该文件内未找到：%s（条目 %s）" % (a, e["id"]))
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
    return red, dict(entries=len(seen), anchors=n_anchor,
                     file_missing=n_file_missing, loc=n_loc)


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
    loc = stat["loc"]
    # ⛔⛔ 上级 126T 令一：报账措辞须与实际所查者一致。
    #     旧版印「锚全部可达」——实际只查了**文件是否存在**。
    print("自检通过（⛔ 只及于下列三项，⛔ 不及其余）：")
    print("   ① 编号无重复；② status 合法；③ 撤回附注已注明批次")
    print("   ④ 锚之**文件路径**全部存在：%d/%d" % (stat["anchors"] - stat["file_missing"],
                                            stat["anchors"]))
    print("   ⑤ 锚之**定位符**：已核 %d 条（§编号／JSON 键），"
          "⛔ 无定位符或形态未支持而**未核** %d 条"
          % (loc.get("ok", 0), loc.get("not_checkable", 0)))
    print("")
    print("⛔⛔ **本自检不做、也不能做的三件事**：")
    print("   ⛔ 不验证该定位符所指之段落**支持**该命题；")
    print("   ⛔ 不验证命题为真、证据充分、范围正确；")
    print("   ⛔ 不验证被撤回之判断是否仍被别处当作现行结论引用。")


if __name__ == "__main__":
    main()
