# RULE_SCHEMA_V0 —— Typed IR 规范（120批立·用户令四、十）

⛔ **立此规范之由**：119批 之 `assertion_type` 七类**把四件事混在一个字段里**——
规则在推理中做什么／规则被验证到什么程度／患者观察状态／本病例运行时结论。
**最危险者是 `confirmed`**：它同时可指「这条文献规则已确认」与「患者这个证已确认」。
**二者不是一回事。**

---

## 一、五维正交（用户令四）

```
rule_effect       规则在推理中做什么
validation_status 规则本身被验证到什么程度
observation_state 患者某观察项之状态
runtime_status    本病例运行时之结论
source_layer      provenance
```

### 1. `rule_effect`
`trigger`｜`support`｜`confirm`｜`exclude`｜`contraindicate`

### 2. `validation_status`
`candidate`｜`source_verified`｜`scope_verified`｜`counterexample_audited`｜
`disputed`｜`rejected`｜`falsified_overbroad`

### 3. `observation_state`
`present`｜`absent_explicit`｜`unknown_not_asked`｜`unknown_not_recorded`｜`uncertain`

### 4. `runtime_status`
`candidate`｜`confirmed`｜`excluded`｜`undetermined`

### 5. `source_layer`
`L1_fact`｜`L2_hu_behavior`｜`L3_response`｜`L4_hu_theory`｜`L5_editorial`｜`L6_engine`

**并附**：
- `speaker_status`：`hu_direct`｜`hu_notes`｜`editor_attributed_to_hu`｜`editorial`｜`uncertain`
- `text_status`：`accepted`｜`disputed`｜`suspected_corruption`｜`rejected_by_hu`｜`unresolved`

---

## 二、⛔ 硬锁（违者 compiler 报错）

```
1. validation_status != runtime_status
   `source_verified` 绝不自动产生 `runtime_status=confirmed`。
   **「规则有出处」不是「患者已符合该结论」。**

2. ⛔删除「两个 supporting_evidence 可解除七禁」
   不存在任何全局 `support_count >= N → confirmed`。
   两个弱证据不等于一个充分条件；一百个也不等于。
   确认只能由 `rule_effect=confirm` 之规则驱动：
     antecedent满足 ∧ scope_match ∧ rule_effect=confirm
     ∧ validation ≥ 执行阈值 → runtime confirmed

3. absent_explicit 本身不得触发排除
   absence_can_exclude IFF
     存在 validated_scoped_necessary_rule (Y ⇒ X)
     ∧ observation_state(X)=absent_explicit
     ∧ scope_match
   **`absent_explicit` 只是一个可参与反证的观察状态，不是天然的 exclusion operator。**

4. compound_antecedent != validated_rule
   三项、四项合取仍可能 source错／scope错／object错／后学倒灌／
   support被写成confirm／典型证被写成充分条件／方证规则被上提为六经规则／存在同域反例。
   **「复合所以合法」不得作为 reason。**

5. L5_editorial 不得静默覆盖 L4_hu_theory / L2_hu_behavior
   冲突时 → `text_status=disputed`（版本化并列），不得删其一。

6. unknown 三态永远中性
   `unknown_not_asked` / `unknown_not_recorded` / `uncertain`：
   不加分、不扣分、不触发 hard exclusion。

7. legacy 默认 fail closed
   未进入 Typed IR ∨ 缺 schema 字段 ∨ validation 不足 ∨ scope 未知
   ∨ (source 主体未知 ∧ 规则为硬门) → `compile_status=fail_closed`
```

---

## 三、Rule IR 字段（`schema/rule_v0.json` 为其 JSON Schema）

```
rule_id                  proposition              object
scope{kind,conditions,exclusions}                 antecedent[]
rule_effect              effect                   validation_status
source_author            source_layer             source_version
speaker_status           source_refs[]            counterexamples[]
revision_relation        text_status              observation_requirements[]
compile_status
```

### `scope.kind`
`standalone_pattern`｜`composite_component`｜`formula_pattern`｜
`stage_conditional`｜`differential`｜`cross_scenario`

⛔ **`standalone_pattern` 之规则不得自动作用于 `composite_state`**，除非 `scope_match=true`。

### `compile_status`
`active`｜`support_only`｜`inactive`｜`fail_closed`｜`manual_review`

---

## 四、执行链（用户令十）

```
学术 Markdown ──compiler/compile_rules.py──▶ Typed IR (rules/*.json)
                                              │
                              compiler/lint_rules.py（硬锁校验）
                                              │
                          runtime/reference_evaluator.py ──▶ case trace
```

⛔ **允许报**：`reference runtime semantic closure = PASS`
⛔ **禁止报**：`LLM 实际阅读 Markdown 行为已验证 = PASS`
后者仍 **NOT_TESTABLE**，只能以后做隔离盲测估计可靠度。
