#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compiler/lint_rules.py —— Typed IR 硬锁校验（120批·用户令四之七锁）

⛔ 本器实现 `docs/RULE_SCHEMA_V0.md` 第二节之七条硬锁。任一违反即报错，compiler 不得编译。
"""
import json, os, re, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = json.load(open(os.path.join(B, "schema", "rule_v0.json"), encoding="utf-8"))
RULES_DIR = os.path.join(B, "rules")

ENUMS = {k: v.get("enum") for k, v in SCHEMA["properties"].items() if "enum" in v}
REQUIRED = SCHEMA["required"]

# 允许进入 runtime 之 validation 阈值（用户令四·硬锁2）
EXEC_THRESHOLD = {"scope_verified", "counterexample_audited"}


def load_all():
    """只收 Rule IR 形制之档（顶层为 list）。

    ⛔⛔ 123批：`rules/pulse_cells_v0.json` 为**另一形制**（顶层 dict，schema=pulse_cell_v0），
       原 loader 见 `.json` 即 `+=`，读到 dict 便把它的**键名**当规则，
       于是 `r.get` 在字符串上崩。
    ⛔ **不得静默跳过**——静默跳过就等于「有一批规则从来没被 lint 过而无人知道」。
       故本函数**返回被跳过者之清单**，由 main 打印，并由各自之校验器负责。
    """
    return load_all_with_skipped()[0]


def load_all_with_skipped():
    out, skipped = [], []
    for f in sorted(os.listdir(RULES_DIR)):
        if not f.endswith(".json"):
            continue
        d = json.load(open(os.path.join(RULES_DIR, f), encoding="utf-8"))
        if isinstance(d, list):
            out += d
        else:
            # ⛔ 条目数须按各档自己的容器键取；写死 cells/rules 会把
            #   `state_variables_v0.json`（容器键为 variables）显示成「条目 0」——
            #   **一个看起来像空文件的显示，比不显示更坏**（124批 自查）。
            n = 0
            for k in ("cells", "rules", "variables", "items"):
                if isinstance(d.get(k), list):
                    n = len(d[k])
                    break
            skipped.append((f, d.get("schema", "<未声明 schema>"), n))
    return out, skipped


def lint(rules):
    errs, warns = [], []
    seen = set()
    for r in rules:
        rid = r.get("rule_id", "<无id>")
        # schema 必填
        for k in REQUIRED:
            if k not in r:
                errs.append((rid, "缺必填字段 %s" % k))
        # enum
        for k, allowed in ENUMS.items():
            if k in r and r[k] not in allowed:
                errs.append((rid, "%s 值非法：%s" % (k, r[k])))
        if "scope" in r and r["scope"].get("kind") not in \
                SCHEMA["properties"]["scope"]["properties"]["kind"]["enum"]:
            errs.append((rid, "scope.kind 非法"))
        if rid in seen:
            errs.append((rid, "rule_id 重复"))
        seen.add(rid)

        vs, cs, re_ = r.get("validation_status"), r.get("compile_status"), r.get("rule_effect")

        # 锁1：validation != runtime —— IR 内不得出现 runtime_status 字段
        if "runtime_status" in r:
            errs.append((rid, "⛔锁1：规则 IR 不得携带 runtime_status（validation 与 runtime 正交）"))
        # 锁1b：source_verified 不足以进 active
        if cs == "active" and vs not in EXEC_THRESHOLD:
            errs.append((rid, "⛔锁1：compile_status=active 须 validation ∈ %s，今为 %s"
                         % (sorted(EXEC_THRESHOLD), vs)))
        # 锁3：exclude 规则须为 scoped necessary rule
        if re_ == "exclude" and cs == "active":
            if not any(a.get("required_state") == "absent_explicit" for a in r.get("antecedent", [])):
                errs.append((rid, "⛔锁3：exclude 规则须以 absent_explicit 为前件"))
            if vs not in EXEC_THRESHOLD:
                errs.append((rid, "⛔锁3：absent_explicit 只能经【已验证且 scope 匹配之必要规则】产生排除"))
        # 锁5：L5 不得覆盖 L4/L2
        if r.get("source_layer") == "L5_editorial" and cs == "active" and re_ in ("confirm", "exclude"):
            errs.append((rid, "⛔锁5：L5_editorial 不得以 confirm/exclude 之硬效力 active"))
        # 锁7：fail closed
        hard = re_ in ("confirm", "exclude", "contraindicate")
        if hard and r.get("speaker_status") in ("uncertain", None) and cs not in ("fail_closed", "inactive"):
            errs.append((rid, "⛔锁7：硬门规则而 speaker_status=uncertain ⇒ 须 fail_closed"))
        if r.get("scope", {}).get("kind") is None and cs != "fail_closed":
            errs.append((rid, "⛔锁7：scope 未知 ⇒ 须 fail_closed"))
        # 被证伪者不得 active
        if vs in ("falsified_overbroad", "rejected") and cs in ("active", "support_only"):
            errs.append((rid, "⛔ validation=%s 者不得 active/support_only" % vs))
        # disputed 提示
        if r.get("text_status") == "disputed" and cs == "active":
            warns.append((rid, "text_status=disputed 而 active——须人读确认"))
    return errs, warns


def main():
    rules, skipped = load_all_with_skipped()
    errs, warns = lint(rules)
    print("═══ Typed IR lint（120批｜123批加 cell 档声明）═══")
    print("规则 %d 条" % len(rules))
    if skipped:
        print("⚠ 非 Rule IR 形制之档（**本器不校，另有校验器**）：")
        for f, sch, n in skipped:
            print("   %-26s schema=%-16s 条目 %d" % (f, sch, n))
        print("   ⛔ 各档之校验器：")
        for f, _, _ in skipped:
            v = {"pulse_cells_v0.json": "tests/test_pulse_cells.py",
                 "state_variables_v0.json": "tests/test_state_variables.py"}.get(f)
            print("      %-26s → %s" % (f, v or "⛔**无校验器——此即缺口，须报**"))
    print()
    for rid, m in warns:
        print("⚠ %-24s %s" % (rid, m))
    for rid, m in errs:
        print("⛔ %-24s %s" % (rid, m))
    print("\n结果：%s（错 %d｜警 %d）" % ("✅通过" if not errs else "⛔未通过", len(errs), len(warns)))
    from collections import Counter
    print("compile_status：" + "｜".join("%s %d" % (k, v) for k, v in
          Counter(r.get("compile_status") for r in rules).most_common()))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
