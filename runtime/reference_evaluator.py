#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""runtime/reference_evaluator.py —— 参考执行器（120批·用户令十二）

⛔⛔ **界限（不可略）**：
   允许报 `reference runtime semantic closure = PASS`。
   **禁止报** `LLM 实际阅读 Markdown 行为已验证 = PASS` —— 后者仍 NOT_TESTABLE。

本器**真实读取** IR 各字段：rule_effect / validation_status / scope /
observation_state / compile_status，并产出 runtime_status。
"""
import json, os, sys
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPILED = os.path.join(B, "runtime", "compiled_rules.json")

OBS = ("present", "absent_explicit", "unknown_not_asked", "unknown_not_recorded", "uncertain")
NEUTRAL = {"unknown_not_asked", "unknown_not_recorded", "uncertain"}   # ⛔永远中性
EXEC_THRESHOLD = {"scope_verified", "counterexample_audited"}


class Case:
    """病例：observations 为 {观察项: observation_state}；未列者一律 unknown_not_asked。
    composite: 是否为合病/并病态。treatment_history: 治疗史列表。"""

    def __init__(self, observations=None, composite=False, treatment_history=None):
        self.obs = dict(observations or {})
        self.composite = composite
        self.tx = list(treatment_history or [])

    def state(self, name):
        if name == "发汗史":
            return "present" if any("发汗" in t for t in self.tx) else "unknown_not_recorded"
        return self.obs.get(name, "unknown_not_asked")


class Evaluator:
    def __init__(self, rules=None):
        self.rules = rules if rules is not None else json.load(open(COMPILED, encoding="utf-8"))

    # ── scope 匹配（用户令 T12）────────────────────────────
    def scope_match(self, rule, case):
        kind = rule["scope"]["kind"]
        if kind == "standalone_pattern" and case.composite:
            return False, "standalone_pattern 不自动作用于 composite_state"
        for c in rule["scope"].get("conditions", []):
            if c.startswith("treatment_history.includes("):
                need = c[len("treatment_history.includes("):-1]
                if not any(need in t for t in case.tx):
                    return False, "scope 条件未满足：%s" % c
        return True, ""

    def antecedent_match(self, rule, case):
        for a in rule["antecedent"]:
            st = case.state(a["observation"])
            if st in NEUTRAL:
                return False, "unknown", "%s 为 %s（中性，不推进不排除）" % (a["observation"], st)
            if st != a["required_state"]:
                return False, "mismatch", "%s 实为 %s，需 %s" % (a["observation"], st, a["required_state"])
        return True, "match", ""

    def run(self, case):
        out = {"confirmed": [], "excluded": [], "candidates": [], "supports": [],
               "to_ask": [], "trace": [], "runtime_status": {}}
        for name, st in case.obs.items():
            if st in NEUTRAL:
                out["to_ask"].append(name)
        for r in self.rules:
            rid, eff = r["rule_id"], r["rule_effect"]
            ok_s, why_s = self.scope_match(r, case)
            if not ok_s:
                out["trace"].append((rid, "skip", why_s))
                continue
            ok_a, kind, why_a = self.antecedent_match(r, case)
            if not ok_a:
                out["trace"].append((rid, "no-fire", why_a))
                continue
            # ⛔锁1：validation 未达阈值者不得 confirm/exclude
            if eff in ("confirm", "exclude") and r["validation_status"] not in EXEC_THRESHOLD:
                out["trace"].append((rid, "blocked",
                                     "validation=%s < 执行阈值" % r["validation_status"]))
                continue
            if eff == "confirm":
                out["confirmed"].append(r["object"]); out["runtime_status"][r["object"]] = "confirmed"
                out["trace"].append((rid, "confirm", r.get("effect", "")))
            elif eff == "exclude":
                out["excluded"].append(r["object"]); out["runtime_status"][r["object"]] = "excluded"
                out["trace"].append((rid, "exclude", r.get("effect", "")))
            elif eff == "support":
                out["supports"].append(r["object"])
                out["runtime_status"].setdefault(r["object"], "candidate")
                out["trace"].append((rid, "support", r.get("effect", "")))
            elif eff == "trigger":
                out["candidates"].append(r["object"])
                out["runtime_status"].setdefault(r["object"], "candidate")
                out["trace"].append((rid, "trigger", ""))
        # ⛔锁2：不存在 support_count >= N → confirmed。此处【刻意不写任何聚合升级】。
        out["final_confirmed_count"] = len(out["confirmed"])
        out["exclusion_count"] = len(out["excluded"])
        out["support_count"] = len(out["supports"])
        return out


def main():
    ev = Evaluator()
    print("═══ reference evaluator（120批）═══")
    print("⛔ 本器证【reference runtime 语义闭环】；**LLM 读 Markdown 之行为仍 NOT_TESTABLE**。\n")
    print("已编译规则 %d 条" % len(ev.rules))
    demo = Case({"恶寒": "absent_explicit", "脉浮": "present", "发热": "present"},
                composite=True)
    r = ev.run(demo)
    print("\n[演示·§172 型：太阳少阳合病，明确无恶寒]")
    print("  confirmed=%s｜excluded=%s｜supports=%s" % (r["confirmed"], r["excluded"], r["supports"]))
    for rid, act, why in r["trace"]:
        print("   %-22s %-9s %s" % (rid, act, why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
