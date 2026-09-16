#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill 整合之验收（126AJ 立·上级令三）

上级 126AJ：「**保留全部既有编号、原始错案、现行约束与历史版本。
正文留当前动作，历史长案例移至可追溯记录并链接。
用『旧条款位置→现行位置→效力是否改变』表验收，⛔ 不能以压缩为由删除限定词。**」

⇒ ⭐ **「不能删限定词」这件事必须可机器验**，否则整合本身就是一次无记录的改写。

本工具做三件（⛔ 只此三件）
--------------------------
① **原文完整性**：`docs/skill历史错案_可追溯记录.md` 内每个代码块，
   与 `docs/skill整合_移出清单.json` 所记之 SHA-256 **逐条比对**。
   ⛔ 不符 ⇒ 原文被改动过 ⇒ **整合作废，须回滚**。
② **链接未断**：被移出之处，skill 正文须仍含指向本册之链接（`#H-0x`）。
③ **入口未丢**：八个 skill 之 `description` 皆非空（⇒ 入口仍可被触发）。

⛔⛔ **本工具之限度**
  ① 它验**字节**，⛔ **不验语义** —— 正文里「失效点描述」是否忠实于被移出的原文，
     ⛔ **本工具判断不了**，须人读。
  ② ⛔ 它**不检查**被移出的内容是否本就该移 —— 那是判断，不是校验。
  ③ ⛔ 它**不覆盖**未登记在移出清单里的改动 ——
     即：**我若改了 skill 而不登记，本工具查不出来。**
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC = os.path.join(ROOT, "docs", "skill历史错案_可追溯记录.md")
LIST = os.path.join(ROOT, "docs", "skill整合_移出清单.json")
SKILLDIR = os.path.join(ROOT, ".claude", "skills")


def main():
    red = []
    if not (os.path.isfile(REC) and os.path.isfile(LIST)):
        print("⛔ 缺 %s 或 %s" % (REC, LIST))
        return 2
    moved = json.load(open(LIST, encoding="utf-8"))
    body = open(REC, encoding="utf-8").read()

    # ① 原文完整性
    blocks = re.findall(r'```text\n(.*?)\n```', body, re.S)
    print("① 原文完整性：记录内代码块 %d 个｜清单 %d 条" % (len(blocks), len(moved)))
    shas = {hashlib.sha256(b.encode()).hexdigest() for b in blocks}
    for m in moved:
        ok = m["sha"] in shas
        print("   %s `%s`　%s　%s" % ("✅" if ok else "⛔", m["id"], m["batch"], m["title"][:36]))
        if not ok:
            red.append("`%s` 之原文 SHA 不符 ⇒ **原文被改动过**" % m["id"])

    # ② 链接未断
    print("② 链接未断：")
    all_skill = ""
    for d in sorted(os.listdir(SKILLDIR)):
        f = os.path.join(SKILLDIR, d, "SKILL.md")
        if os.path.isfile(f):
            all_skill += open(f, encoding="utf-8").read()
    for m in moved:
        ok = ("#" + m["id"]) in all_skill
        print("   %s `%s` 之链接" % ("✅" if ok else "⛔", m["id"]))
        if not ok:
            red.append("`%s` 之链接在 skill 正文内已断" % m["id"])

    # ③ 入口未丢
    print("③ 入口未丢：")
    n = 0
    for d in sorted(os.listdir(SKILLDIR)):
        f = os.path.join(SKILLDIR, d, "SKILL.md")
        if not os.path.isfile(f):
            continue
        n += 1
        t = open(f, encoding="utf-8").read()
        mo = re.search(r'^description:\s*(\S.*)$', t, re.M)
        ok = bool(mo and len(mo.group(1)) > 10)
        if not ok:
            red.append("`%s` 之 description 缺失或过短" % d)
        print("   %s %s" % ("✅" if ok else "⛔", d))
    print("   共 %d 个 skill" % n)

    print()
    if red:
        print("⛔⛔ 红项 %d：" % len(red))
        for r in red:
            print("   · %s" % r)
        return 1
    print("✅ 三项通过。")
    print("⛔⛔ **但本工具只验字节，⛔ 不验语义** —— 正文之「失效点描述」是否忠实于被移出的原文，")
    print("   ⛔ 须人读；且**未登记在移出清单里的 skill 改动，本工具查不出来**（限度③）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
