#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compiler/compile_rules.py —— 只编译合法 IR（120批·用户令十、十一）

⛔ **legacy 默认 fail closed**（用户令十一）：
   未进入 Typed IR 之 Markdown 文本，**一律不进 runtime**。
   本器只输出 `runtime/compiled_rules.json`，evaluator 只吃这一份。
"""
import json, os, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, "compiler"))
from lint_rules import load_all, lint, EXEC_THRESHOLD
OUT = os.path.join(B, "runtime", "compiled_rules.json")


def compile_rules():
    rules = load_all()
    errs, warns = lint(rules)
    if errs:
        raise SystemExit("⛔ lint 未通过（%d 错），拒绝编译。" % len(errs))
    active, dropped = [], []
    for r in rules:
        cs = r.get("compile_status")
        if cs in ("active", "support_only"):
            active.append(r)
        else:
            dropped.append((r["rule_id"], cs, r.get("validation_status")))
    return active, dropped, warns


def main():
    active, dropped, warns = compile_rules()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(active, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("═══ compile（120批）═══")
    print("✅ 编译入 runtime：%d 条" % len(active))
    for r in active:
        print("   %-22s effect=%-8s status=%-12s validation=%s"
              % (r["rule_id"], r["rule_effect"], r["compile_status"], r["validation_status"]))
    print("\n⛔ 未编译（fail closed / inactive / manual_review）：%d 条" % len(dropped))
    for rid, cs, vs in dropped:
        print("   %-22s compile=%-14s validation=%s" % (rid, cs, vs))
    print("\n⛔ **legacy Markdown 文本一律不进 runtime**——evaluator 只吃 %s。"
          % os.path.relpath(OUT, B))
    print("已写入 %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
