---
name: hxs-census
description: 仲景-HXS 工程之【全集普查先于统计】。凡要报任何比率、覆盖率、完备性、「多少条命中／未命中」、「全部类型如下」、「共有 N 个对象」，先用本 skill 建分母。它强制：N 由枚举产生（discovery query → inclusion → exclusion → object IDs 全链留痕）；枚举不出者记 `population_gap` 且不得作为待办计数；并区分 `repository_known` 与 `theory_construct` 两种 population。⭐ 「63 组候选」曾被五份报告引用而从未存在；阳五型／阴五型 胡老明列而工程一百二十六批未发现——**前者是分母造假，后者是分母根本不存在**。
---

# 全集普查（hxs-census）

## 两种 population，**先说清你在用哪一种**

这是本 skill 最要紧的一条，也是 126E 才被分清的：

| population | 是什么 | 现状 |
|---|---|---|
| `repository_known` | **仓库里已经被构造出来**的对象集合 | **N = 66**，已冻结（126E） |
| `theory_construct` | **理论实际拥有**的构念集合 | ⛔ **尚未建立** |

⛔⛔ **把前者当后者，是 F 类 `construct_population_conflation`。**

66 个对象即便**全部**通过三重攻击，也只证明**这 66 个**经得起攻击。
它不能证明没有第 67、68 个**我们根本没构造出来**的重要构念。

**实证**：胡老明写「所谓阳证，可有或热、或实、或亦热亦实、或不热不实、或热而虚者」
〔A·讲伤寒·389357〕——**一百二十六批无人发现**，而 66 个对象里没有任何一个承载「经内五型」这一层。
⇒ 这不是某个对象判错，是**整层缺失**。

⇒ 所以：**在 `theory_construct` 建立之前，任何「覆盖率」「完备」之断言都没有分母。**
现在能说的只有：「在 repository-known 的 66 个对象中，……」

## 建分母的五步（126B 令一）

```
① discovery query   —— 你是用什么把对象找出来的？逐条写
② inclusion         —— 什么条件算一个对象
③ exclusion         —— 排除了什么，逐条附理由
④ object IDs        —— 全部列出，不写「等」
⑤ population_gap    —— 找不到持久化资产者，单列
```

现行实装：`tools/audit_population_census.py`，产出 `evidence/审计全集普查与分母修复_126B.md`。

```bash
python3 tools/audit_population_census.py
```

### ⛔ 关于 `population_gap`

> **凡报告中称引之对象集合，须能在 repository 中被枚举出来；
> 枚举不出者记 `population_gap`，不得作为待办计数。**

已登记之幽灵：

| 名 | 实情 |
|---|---|
| `PHANTOM-63FLIP`（「63 组机器候选」） | 五份报告引用，仓库内枚举不出，**从未存在** |
| 「28 条 `validation=candidate`」 | 现行 `rules/*.json` 中 `candidate` 为 **0** 条 |

⇒ **不制造不存在的债务。**

## 分母纪律

```
not_applicable                  → 不进分母（本闸对该对象不适用）
not_auditable_missing_anchor    → 不进分母（可评价性缺失，须补锚）
unknown_pending_review          → 进分母，⛔ 不进分子
audited_no_issue                → 进分母，不进分子
issue_found                     → 进分母，进分子
```

⛔ **每闸各自算分母，不许共用**（126批 三个数字即毁于共用 N=43）。
⛔ **字段级状态不得冒充对象级裁决**；对象级只可
`survives`／`downgraded`／`partially_retracted`／`retracted`／`unknown_pending_audit`，
且同一对象不得重复计数。

⚠ 并注一处**名字本身的误导**：`survives` 对「不作文本断言」的对象（分类裁决、否定性结果）
是误导的——四闸对它们本就问不到什么。**「四闸皆无 issue」≠「证据充分」。**

## E 类扫描：报「不存在」之前先查自己的资产

> **「查不到 X」在报出之前，须先证明本工程内没有第二份该对象的表。**

126C 实例：锚在 `tools/fanzhuandui.py::PAIRS`，而 `jiegou_buqi_123.G` 没有；
审计扫了没锚那份，于是把**我方未接线**报成了**证据不存在**（E 类 `asset_fork_unlinked`）。

```bash
# 同一 ID 在工程内出现在几个文件里？⛔ 不得带截断参数
grep -rln "<对象ID>" tools/ rules/ evidence/ term_layer/ state_layer/ case_layer/
```

## ⛔ A2：建分母的检索，不得截断

**任何关于全集、存在性、缺失性、唯一性、数量、覆盖率之断言，
其证据生成链不得经过未经证明完备之截断输出。**

截断不只制造「没有」，也制造「只有这些」「主要是这些」「全部类型如下」。

```bash
grep -rln "X" .            # ✅ 建分母用这个
grep -rln "X" . | head -10 # ⛔ 这个只能用来看例子
```

## 报数模板

```
population 类型：repository_known ／ theory_construct   ← 必填
N = __   （discovery query 见 <文件>§__）
population_gap = __   （逐个列名）

| 闸 | issue | eligible 分母 | 无锚 | n/a | unknown |
```

⛔ 不填 population 类型的数，**不得进入任何报告**。
