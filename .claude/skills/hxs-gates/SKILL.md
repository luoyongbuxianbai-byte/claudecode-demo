---
name: hxs-gates
description: 仲景-HXS 工程之【四闸取证审计】。凡要挂载／修改／撤销任何条款、规则、映射格、状态变量、翻转对，凡要给某条证据定归因（说这是「胡老说的」），凡要统计「多少条命中／未命中」，先用本 skill 过四闸：GATE_1 取证半径｜GATE_2 词-义双轨｜GATE_3 命题原子化｜GATE_4 归因来源。它同时管分母纪律（unknown 不进分子、not_applicable 不进分母）。⭐ 不过闸不得入库——126批之三个统计数字全部因闸外作业而作废，所以哪怕只是「顺手改一格」也要过。
---

# 四闸（hxs-gates）

四闸不是四个检查项，是四个**不同的失败原因**。它们各自的分母也不同——
126批 把四闸共用一个分母 `N=43`，三个数字因此全错。

在动手之前，先判这次作业**落在哪几闸**，然后只对落到的闸计数。

---

## GATE_1 · 取证半径（context radius）

**它管的是：你读的那一段，是不是一个完整的意思。**

| 必填栏 | |
|---|---|
| `anchor_text` | 锚处原文 |
| `preceding_context` / `following_context` | 前后文 |
| `same_clause_hu_comment` | ⭐ **同一解释单元内胡老的评议** |
| `text_status` | accepted／variant／emended_by_hu／suspected_corruption／rejected_by_hu／editorial_reconstruction |
| `speaker_status` | 见 GATE_4 |

**边界规则**：以【同条／同段／同一解释单元结束】为最低边界。
⛔ **不得机械规定「±400 字即充分」**——§214 已证：胡老之裁决在条文后约 400 字，恰在窗缘。
固定字符窗与语义无关，它够用的那几次是运气。

**单元标记**见 `hxs-reading`。边界不可定 ⇒ `context_complete = unknown` ⇒ **不得进入决定性证据**。

**⛔ 特别注意 `text_status`：** 胡老明确判为错简／错乱／传抄误并拒绝解释之文本，
**不得作正证，也不得作反例**，只可作 text-critical evidence。
已登记者见 `rules/text_critical_v0.json`（现 6 条），回归见 `tests/test_text_critical_gate.py`。

**适用范围**：只对**作文本断言**的对象适用。
不作文本断言者（否定性结果之 `not_found` 记录、分类裁决）⇒ `not_applicable`，**不进分母**。
⚠ 126C 的教训：`not_auditable_missing_anchor` 这个名字原本混了两件事——
「作了断言却没锚」（须补锚，可修）与「根本不作断言」（无可修）。**修复动作不同即须拆名。**

---

## GATE_2 · 词-义双轨（lexical / semantic）

**它管的是：你没查到，是词不在，还是义不在，还是你查法不对。**

四问，**必须分别作答**：

1. `exact_term_exists?` —— 这个词本身在不在？
2. `variant_expression_exists?` —— 异写在不在？
3. `concept_exists?` —— 概念在不在（可以完全不用这个词）？
4. `mapping_source_exists?` —— 从观察到对象的**那条映射**有没有出处？

⛔⛔ **禁止由其中一个字段推另外三个。**
124批「胃气无源」即由 `mapping` 之薄推 `term` 之无——而 `term` 实有 **740 处**。

**query_family 必填**，四类变形至少各试一种：

| 变形 | 例 |
|---|---|
| 词序变化 | `脉缓` ↔ `缓脉` ↔ `脉逐渐缓`（124批 即因只用 `脉缓` 而漏「脉逐渐缓」） |
| 修饰词插入 | `脉数` ↔ `脉浮数` ↔ `脉数而滑` |
| 近义表达 | `阳衰` ↔ `亡阳` ↔ `阳气衰` ↔ `阳虚` |
| 双向式 | `缓…胃气` 与 `胃气…缓` **须各查** |

跨书异写另见 `hxs-crossbook`——那是本闸在十二书上的展开。

**记录要求**：每个否定性检索**须保存实际使用之 query family**，不得只留结论。
留了结论不留检索式，等于把「我没找到」写成了「它不存在」，而后者无法被复核。

**⛔ 闸门9⑦**：不得以检索宣称「全库无此规则」。检索只覆盖带标记词之规则。

**⛔ A2 `tool_output_truncation`（已批准·权威定义见 `rules/failure_classes_v0.json`）**：
⭐ 现行定义：**凡关于全集／存在性／缺失性／唯一性／数量／覆盖率之断言，其证据生成链不得经过未经证明完备之截断输出。**
⚠ 分页本身不禁——**全链完备且可核**即可；禁的是拿未证完备的截断结果当全集。
旧窄表述：
本闸原本只盖「检索式对不对」，**没盖「你有没有看完检索的输出」**。
126D 实例：`grep … | head -10` 截断后，从前十行得出全称否定——而目标在第十一行之后。
⇒ **凡将据检索结果作否定性断言，该次检索不得带任何截断参数**
（`head` / `--max` / `limit` / `head_limit`）。看例子时可截断，**证明没有时不可以**。

---

## GATE_3 · 命题原子化（proposition atomization）

**它管的是：这一句里有几个可以分别被推翻的东西。**

规则：一句规则中若含两个【可**分别**被反例推翻】之谓词，必须拆成独立 proposition。

三个回归样本（`tests/test_proposition_atomization.py`，`--rebundle` 必须变红）：

| id | 绑在一起的 | 必须拆成 | 为什么 |
|---|---|---|---|
| ATOM-1 | 缓 → 中风 | 「中风证型成立」/「中风由外来风邪导致」 | 胡老**否定后者而肯定前者为类型名**；绑着即 125批之误判 |
| ATOM-2 | 缓 = 胃气 | 「『胃气』一词存在」/「缓脉映射胃气恢复」 | 词有 740 处而映射仅 1 处 |
| ATOM-3 | 脉数 → 热 | support / confirm / locate / exclude / →治疗 | 前一成立，后四不成立；打包即先过宽后矫枉之根 |

**适用范围**：按该对象**是否实际作出断言**判。
⛔ **不按「`object` 栏填没填」判**——缺字段是**记录缺失**，不是「本闸不适用」；
把前者当后者会系统性缩小分母（126F 上级复核指出）。

⚠ 本闸最常见的滥用是**反向**的：把一条禁令加严。
124批 有过一次——测试断言写得比命令更宽，挡掉了一个合法的域内反例。
**把一条禁令加严，和违反它一样是失准。**

---

## GATE_4 · 归因来源（provenance / attribution）

**它管的是：你凭什么说这是胡老说的。**

126批 把 `speaker_unresolved` 一名塞进两件完全不同的事——
「不知道谁说的」（C卷 uncertain）与「知道是整理本、但没资格说是胡老本人」（editor_compiled）。
**二者修复方法完全不同**：前者须查书目，后者须改措辞。故必须拆。

| 子类 | |
|---|---|
| D1 `speaker_identity_unresolved` | 该来源之说话主体**未知**（现仅 C卷） |
| D2 `attribution_overreach` | 以 uncertain／editor_compiled 之材料作**胡老本人**归因 |
| D3 `source_version_unresolved` | 同一命题在两本异说而版本关系未定 |
| D4 `passage_authorship_unresolved` | 整理本之**该段执笔人**未标（八本编纂本皆然） |

### 硬约束（不可绕）

```
speaker_status = uncertain        → ⛔ 禁 hu_direct attribution
speaker_status = editor_compiled  → ⛔ 禁自动升级为 hu_direct
publication_date ≠ text_composition_date    ⛔ 不得据出版先后论「晚年改说」
same_style_family ≠ same_book ≠ same_author ⛔ 栏目相似不等于同族、同书、同作者
⛔ 不允许仅根据文件名推作者
⛔ editor_compiled 不得计入 speaker_unresolved
```

### 十二书说话主体表（已核卷首）

| 书 | speaker_status |
|---|---|
| 讲伤寒／讲金匮 | `hu_lecture` ⇒ 可 `hu_direct`（⚠ 仍须保留【讲课记录之整理媒介】属性） |
| 传真系／解读／病位类方解／汤液经方系／伤寒论传真／金匮要略传真／中国汤液方证／临床家 | `editor_compiled` ⇒ 只可 `hu_via_editor`，表述作「某整理本作……」 |
| 带教 | `editor_compiled_feng` |
| **C卷** | ⭐ **`uncertain`（P0）** ⇒ 只可 `source_unattributed`，表述作「C卷（体例为注解本，speaker 未定）作……」 |

C卷 是本工程**被引用最多**的一本。依赖它的裁决，其「胡老本人」之归因一律降为
`attributed_via_uncertain_source`。⚠ **但这不是撤销**——证据仍在，只是归因层级下调。

回归：`tests/test_provenance_gate.py`。

---

## 分母纪律（每闸各自算，不许共用）

```
not_applicable                  → 不进分母（本闸对该对象不适用）
not_auditable_missing_anchor    → 不进分母（可评价性缺失，须补锚）
unknown_pending_review          → 进分母，⛔ 不进分子
audited_no_issue                → 进分母，不进分子
issue_found                     → 进分母，进分子
```

⛔ **未采 ≠ 阴性（协议51）。** 0 锚不是「干净」，是「测不了」。
⛔ **字段级状态不得冒充对象级裁决。** 对象级只可：
`survives` / `downgraded` / `partially_retracted` / `retracted` / `unknown_pending_audit`，
且**同一对象不得重复计数**。

⛔ **全集先于统计。** 分母 N 必须由**枚举产生**，不得先写 N 再审。
枚举不出来的对象集合记 `population_gap`，**不得作为待办计数**
（126B 实例：「63 组候选」在五份报告里被引用而从未存在 ⇒ `PHANTOM-63FLIP`）。

---

## 怎么跑

```bash
python3 tools/audit_population_census.py     # 全集普查 + 四闸 + 对象级裁决
python3 tests/test_provenance_gate.py        # GATE_4 回归
python3 tests/test_proposition_atomization.py            # GATE_3 正控
python3 tests/test_proposition_atomization.py --rebundle # GATE_3 负控（须红 3）
python3 tests/test_text_critical_gate.py     # text_status 闸
```

闸门定义之权威副本：`schema/retrieval_gates_v0.json`。

⛔⛔ **测试全绿不作为完成证明。**
测试只能证明**已经编码进去的错误模型**没有违反自己；它不能证明**遗漏的语义条件**不存在。
完成证明只能是逐项的锚文核对。
