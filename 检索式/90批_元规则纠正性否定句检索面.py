#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""90批·元规则开采法：纠正性否定句检索面（上级立法，本方执行）

隐性规则＝元规则，规定「如何读其他规则」，多以纠正性否定句出现。
⛔ 用法纪律（闸门9 第九款）：每一处须先判「谁在说」，再判效力层级，二判皆须人读。
   本脚本只负责取出候选，不做分类——机械分类会把「读者来信之反方论点」
   误判为胡老元规则（90批上级第四例即此）。
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from corpus_guard import load_one, BOOKS          # 闸门9 第六款：统一入口

PATS = ["不是.{0,12}而是", "并非", "不可不知", "不要以为", "不能.{0,10}看",
        "误解", "殊不", "其实.{0,8}并非", "非指", "这都是错的", "曲解",
        "非谓", "后世.{0,8}曲解", "实为误解", "勿以为", "不得谓"]

def main():
    T = {b: load_one(b) for b, _ in BOOKS}
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for p in PATS:
        if only and only != p:
            continue
        hits = [(b, m.start(), T[b][max(0, m.start() - 90):m.end() + 90])
                for b in T for m in re.finditer(p, T[b])]
        print("=== 「%s」全库 %d ===" % (p, len(hits)))
        if only:
            for b, s, c in hits:
                print("〔%s·%d〕%s" % (b, s, c))
        print()

if __name__ == "__main__":
    main()
