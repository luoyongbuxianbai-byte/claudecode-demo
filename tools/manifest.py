#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manifest.py —— 关键资产清单（87批·用户令要求④·常设纪律）

事故谱系：82批 scratchpad 全清、83批 容器换新克隆工作区全丢，两次皆事后补救。
本清单之用途：**每批核一次数量与行数**，任何一项行数骤减或消失，即刻可见。

用法：
    python3 tools/manifest.py            # 打印清单
    python3 tools/manifest.py --write    # 写入 MANIFEST.md 并入库
    python3 tools/manifest.py --check    # 与 MANIFEST.md 比对，有减少即非零退出
"""
import hashlib
import os
import subprocess
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "MANIFEST.md")

# (类别, 路径或目录, 是否目录)
ASSETS = [
    ("引擎",       "hxs_engine_v79_full.md",       False),
    ("引擎·执行核", "hxs_engine_执行核.md",          False),
    ("引擎·执行件", "hxs_engine_执行件.md",          False),
    ("白皮书",     "白皮书",                        True),
    ("摘录",       "摘录",                          True),
    ("工具",       "tools",                        True),
    ("语料",       "sources",                      True),
    ("报告",       "reports",                      True),
    ("状态层",     "state_layer",                  True),
    ("术语层",     "term_layer",                   True),
    ("医案层",     "case_layer",                   True),
    ("留出区",     "holdout",                      True),
    ("指令",       "指令",                          True),
    ("检索式",     "检索式",                        True),
]

TEXT_EXT = {".md", ".py", ".txt", ".json", ".csv", ".tsv"}


def _lines(p):
    try:
        with open(p, "rb") as f:
            return f.read().count(b"\n") + 1
    except Exception:
        return 0


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()[:12]


def collect():
    rows = []
    for cat, rel, isdir in ASSETS:
        p = os.path.join(B, rel)
        if not os.path.exists(p):
            rows.append((cat, rel, 0, 0, 0, "⛔缺失"))
            continue
        if isdir:
            n = tot = size = 0
            for root, _, fs in os.walk(p):
                if os.sep + ".git" in root:
                    continue
                for f in fs:
                    if f.startswith("."):
                        continue
                    fp = os.path.join(root, f)
                    n += 1
                    size += os.path.getsize(fp)
                    if os.path.splitext(f)[1] in TEXT_EXT:
                        tot += _lines(fp)
            rows.append((cat, rel + "/", n, tot, size, ""))
        else:
            rows.append((cat, rel, 1, _lines(p), os.path.getsize(p), _sha(p)))
    return rows


def render(rows):
    try:
        head = subprocess.check_output(
            ["git", "-C", B, "rev-parse", "--short", "HEAD"], text=True).strip()
        branch = subprocess.check_output(
            ["git", "-C", B, "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(
            ["git", "-C", B, "status", "--porcelain"], text=True).strip()
    except Exception:
        head = branch = "?"
        dirty = ""
    L = ["# MANIFEST · 关键资产清单",
         "",
         "**87批立（用户令）。每批核一次数量与行数——任何一项骤减或消失，即刻可见。**",
         "生成：`python3 tools/manifest.py --write` ｜ 核对：`--check`",
         "",
         "| 项 | 值 |",
         "|---|---|",
         "| 分支 | `%s` |" % branch,
         "| HEAD | `%s` |" % head,
         "| 工作区 | %s |" % ("**⚠ 有未提交改动**" if dirty else "干净"),
         "",
         "| 类别 | 路径 | 文件数 | 行数 | 字节 | 校验 |",
         "|---|---|---:|---:|---:|---|"]
    for cat, rel, n, ln, sz, sha in rows:
        L.append("| %s | `%s` | %d | %d | %s | %s |"
                 % (cat, rel, n, ln, "{:,}".format(sz), sha))
    L += ["",
          "## 常设纪律（87批·用户令）",
          "",
          "1. **凡丢失后需重做之物，当批结束即 commit**——工具、中间数据、摘录、映射表、"
          "检索式，全部入库，**不得只存 scratchpad**。",
          "2. **每批报告首行报 commit 号与文件清单。**",
          "3. **每批开工第一动作：核对远端与本地是否一致**（闸门9 第五款）。",
          "4. **本清单每批核一次**（`python3 tools/manifest.py --check`）。",
          "5. **凡清洗/转换后报前后字数比，降幅 > 20% 即停并报**"
          "（协议16，实装于 `tools/corpus_guard.py`，"
          "开工预检 `python3 tools/corpus_guard.py --audit`）。",
          ""]
    return "\n".join(L)


def parse_existing():
    if not os.path.exists(OUT):
        return {}
    d = {}
    for ln in open(OUT, encoding="utf-8"):
        if ln.startswith("| ") and "`" in ln and ln.count("|") >= 7:
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            if len(c) >= 5 and c[2].isdigit() and c[3].isdigit():
                d[c[1].strip("`")] = (int(c[2]), int(c[3]))
    return d


# ── 100批新增·产出新鲜度断言 ────────────────────────────────
# 事故谱系：yao_bagang.py 自 76批 起崩溃，附录F 三十余批未生成而历批照引其数；
#   附录E/G/N2/O2/P2 表旧于其工具；附录D 直接缺失。
# ⛔ 本工程之工具失败有两类：①跑了但结果错（assert 与人读能拦一部分）
#   ②**根本没跑／跑崩／产出过期**——**此类此前完全无防护，且是主因。**
# 本检即为②之防护：表比其工具旧 ⇒ 该表所载之数已不可引用。
PRODUCT = [
    ("term_layer/附录D_全局否决索引.md",             "tools/veto_index.py"),   # ⚠100批订正：原写「全判据索引/verdict_extract」，二者皆错
    ("term_layer/附录E_十二书否决与限定全量索引.md",   "tools/veto_full_scan.py"),
    ("term_layer/附录F_方八纲对应表.md",             "tools/yao_bagang.py"),
    ("term_layer/附录H_加减三元组.md",               "tools/jiajian_triple.py"),
    ("term_layer/附录I_方剂结构表.md",               "tools/fang_structure.py"),
    ("term_layer/附录J_部位病位对照表.md",            "tools/buwei_bingwei.py"),
    ("term_layer/附录K2_状态组合表与单状态方表.md",     "tools/zhuangtai_tables.py"),
    ("term_layer/附录L2_功能位与剂量判据层.md",        "tools/gongnengwei.py"),
    ("term_layer/附录M2_三毒与肾虚归属对照表.md",      "tools/sandu_shenxu.py"),
    ("term_layer/附录N2_胡老明标规则集.md",           "tools/guize_marker.py"),
    ("term_layer/附录O2_特异指征反噬表.md",           "tools/tezheng_fanshi.py"),
    ("term_layer/附录P2_服后反证表.md",              "tools/fuhou_fanzheng.py"),
    ("term_layer/必要条件表.md",                    "tools/biyao_tiaojian.py"),   # 102批
    ("term_layer/标记面清单.md",                    "tools/biaoji_mian.py"),      # 104批
    ("state_layer/方剂组成.json",                  "tools/fang_compose.py"),     # 106批
]


# ⛔ 手工件（无产出工具，故无法重跑、无从验证是否随语料更新）——本身即为一类风险，单列
MANUAL = [("term_layer/附录G_八纲三毒客观判定表.md",
           "56批手写·62行·⛔无产出工具，语料由九书增至十二书后从未随之更新"),
          ("term_layer/统一对应表.md",
           "106批立·⭐用户令之核心表：症候×八纲×六经×三毒×药物，五类判据合一。"
           "工具 tongyi_yansuan.py 读其编码副本（TONGYI 常量），本文为人读正本。"
           "⛔三毒栏 1/16 有值，为全表最大缺口，每批须报其填充进度。"),
          ("term_layer/显隐映射表_人读判定.md",
           "104批立·⭐人读判定册（显隐映射 148 条）。工具不得写入。"
           "每批须报『已读/命中』比例。"),
          ("term_layer/必要条件表_人读判定.md",
           "103批立·⭐人读判定册，工具不得写入。与 `必要条件表.md`（工具候选池）分离，"
           "因 102批 将判定写在工具产出内，重跑即被覆盖——乙类事故同型。"
           "本册无新鲜度约束（人读之物不随语料自动过期），但每批须报『已读/候选池』比例。")]


def fresh():
    print("== 产出新鲜度（表须不旧于其工具，否则其数不可引用）==\n")
    bad = miss = 0
    for prod, tool in PRODUCT:
        pp, tp = os.path.join(B, prod), os.path.join(B, tool)
        name = os.path.basename(prod)
        if not os.path.exists(tp):
            print("  %-34s ⛔工具缺失 %s" % (name[:32], tool)); bad += 1; continue
        if not os.path.exists(pp):
            print("  %-34s ⛔产出缺失——工具在而表不在，疑跑崩" % name[:32]); miss += 1; continue
        dp, dt = os.path.getmtime(pp), os.path.getmtime(tp)
        if dp < dt:
            print("  %-34s ⛔表旧于工具 %.1f 小时——须重跑，其数暂不可引用"
                  % (name[:32], (dt - dp) / 3600)); bad += 1
        else:
            print("  %-34s ✅" % name[:32])
    print("\n结果：%d/%d 新鲜｜⛔过期 %d｜⛔缺失 %d"
          % (len(PRODUCT) - bad - miss, len(PRODUCT), bad, miss))
    if MANUAL:
        print("\n⚠ 手工件（无工具，不可重跑，其数须人读复核）：")
        for m, why in MANUAL:
            print("   %-34s %s" % (os.path.basename(m)[:32], why))
    if bad or miss:
        print("⛔ 有过期或缺失项——**引用其数前须先重跑**。")
    return 1 if (bad or miss) else 0


def main():
    rows = collect()
    if "--fresh" in sys.argv:
        return fresh()
    if "--check" in sys.argv:
        old = parse_existing()
        if not old:
            print("⚠ 无 MANIFEST.md 可比对，先跑 --write")
            return 1
        bad = 0
        for cat, rel, n, ln, sz, sha in rows:
            if rel in old:
                on, ol = old[rel]
                if n < on or ln < ol:
                    print("⛔ %s `%s` 减少：文件 %d→%d，行 %d→%d" % (cat, rel, on, n, ol, ln))
                    bad += 1
        print("核对完毕：%s" % ("⛔ %d 项减少，先查明再动" % bad if bad else "✅ 无减少"))
        return 1 if bad else 0
    txt = render(rows)
    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write(txt)
        print("已写入 %s" % OUT)
    else:
        print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
