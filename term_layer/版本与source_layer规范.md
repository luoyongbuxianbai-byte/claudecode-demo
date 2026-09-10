# 版本与 source_layer 规范（120批·用户令八）

## 一、六层 provenance

| 层 | 含义 |
|---|---|
| `L1_fact` | 患者原始事实 |
| `L2_hu_behavior` | 胡老实际判定/处方 |
| `L3_response` | 治疗反馈 |
| `L4_hu_theory` | 胡老本人理论解释 |
| `L5_editorial` | 弟子/编者整理、解读、重新归经 |
| `L6_engine` | 本引擎之抽象（含 `[推演]` 标记者） |

## 二、说话主体与文本状态

```
speaker_status: hu_direct | hu_notes | editor_attributed_to_hu | editorial | uncertain
text_status   : accepted | disputed | suspected_corruption | rejected_by_hu | unresolved
```

## 三、⛔ 硬规则

```
L5_editorial 不得静默覆盖 L4_hu_theory / L2_hu_behavior
冲突时 → text_status = disputed（版本化并列），不得删其一
```
**lint 实装**：`compiler/lint_rules.py` 锁5——`L5_editorial` 之规则不得以 `confirm`/`exclude` 之硬效力 `active`。
**测试**：`tests/test_version_conflict.py`。

## 四、已登记之版本冲突

| 对象 | L4/L2（胡老） | L5（后学） | 处置 |
|---|---|---|---|
| **厥阴之判定** | 〔C卷·12662〕「凡阴证除外表里者，当然即属半表半里的阴证」；并云厥阴提法「更成问题」「不可专凭提纲」 | 〔解读·261497〕「即厥阴病**以上热下寒为主证**」 | `disputed` ＋ `inactive`；**两造皆保留** |
| ⭐**§172 之太阳成分是否恶寒** | 〔讲伤寒·188178〕「**它并不恶寒**」 | 〔C卷·125102〕「**太阳病之发热恶寒**……同时出现」 | ⭐**此为【胡老自身两读】，不是 L4 vs L5**——`text_status=disputed`，**且足以使全称式 fail closed** |
| **苓桂术甘「无气冲则不验」** | — | 〔传真系·38229〕**【临床应用】栏，体例未界定** | `speaker_status=uncertain` ⇒ `fail_closed` |
| **柴胡桂枝干姜汤归经** | 胡老早期「邪郁少阳」〔C卷·131846〕 | 后学「半表半里阴证＝厥阴」〔金匮传真·45969〕 | ⚠ **编者前言自承「后期笔记与早期有明显不同」**〔传真系·1930〕⇒ `revision_relation` 待建 |

## 五、⛔ 待办

- `source_version` 字段现多为空——**胡老早期/后期笔记之版本标注尚未建立**。
- `revision_relation` 只在 `JUEYIN-SHANGREXIAHAN` 填了一条。
