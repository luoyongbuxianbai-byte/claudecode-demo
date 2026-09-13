---
name: hxs-batch
description: 仲景-HXS 工程之【开工五检与收工三件套】（封装闸门9⑭ ＋ 协议17）。每批开工第一动作、每批收工之前，用本 skill。开工五检：语料 audit｜清单 check｜TAIL｜可达性｜产出新鲜度；收工三件套：报告 `reports/报告_第N批.md` → commit → 送件。凡要开新一批、凡要写报告、凡要 commit 收工，先用它。⭐ 纪律靠「我记得」执行是会衰减的——本 skill 把它变成一串可以真的跑失败的命令。
---

# 开工五检 · 收工三件套（hxs-batch）

## 开工五检（闸门9⑭）

按顺序跑，**任一项不过即停，不得带着红项开工**。

```bash
# ① 语料完备性与协议16（清洗降幅 >20% 即停；偏离冻结基线 >2% 即停）
python3 tools/corpus_guard.py --audit

# ② 资产清单核对（任一项骤减即可见）
python3 tools/manifest.py --check

# ③ TAIL：远端与本地是否一致（闸门9 第五款）
git fetch origin "$(git rev-parse --abbrev-ref HEAD)" && git status -sb | head -1
git log --oneline -1

# ④ 可达性：冻结件 diff 必须为空
git diff HEAD --stat -- V8/ runtime/ rules/core_v0.json

# ⑤ 产出新鲜度：证据册是否落后于其生成器（闸门9⑮）
python3 tools/audit_population_census.py   # 重跑后 git diff 若有改动 ⇒ 上一批的册是旧的
```

⚠ ⑤ 常被跳过而它最容易出事：**引附录／证据册里的数之前，先确认那份册是这次跑出来的。**

### 并报一句现行相位

```bash
python3 -c "import json;d=json.load(open('rules/failure_classes_v0.json'));print(d['phase']['current']);print(d['phase']['order'])"
```

⛔ 现为 **Phase 0（理论重构／构念发现）**。
在 Phase 0 里，**不写规则、不挂条款、不跑三重攻击**——见 `rules/failure_classes_v0.json :: phase`。

## 收工三件套（协议17）

### ① 报告

写 `reports/报告_第N批.md`。**首行报账**必含：

```
开工 HEAD `xxxxxxx`｜语料 12/12｜清单 --check 无减少｜测试 __/__｜冻结件 diff = 0
```

⛔⛔ **测试全绿不作为完成证明**（126批 令八）。
测试只能证明**已经编码进去的错误模型**没有违反自己；它不能证明**遗漏的语义条件**不存在。
⇒ 报告里必须另有一节，写**本批的实质证明是什么**（逐项锚文核对／逐条原文照录）。

报告必含的两节，缺一不可：

| 节 | 为什么不能省 |
|---|---|
| **未做** | 逐项列，**不写「其余」**。且要标哪些被令冻结、哪些是本批自己制造的新债 |
| **我对本批的判断** | 含至少一条**对自己的否定**——本批哪里没有证据、哪里只是记录而非解决 |

### ② commit

```bash
git add -A && git commit -F - <<'EOF'
<N批>·<一句话说清本批实得>

<正文：逐条，含自己犯的错>

Co-Authored-By: ...
EOF
```

⛔ 「凡丢失后需重做之物，当批结束即 commit」（87批·用户令）——
工具、中间数据、摘录、映射表、检索式，全部入库，**不得只存 scratchpad**。
⚠ 本会话跑在可回收容器里：**没 commit 的东西，下一批就不存在。**

### ③ 送件

`SendUserFile` 送报告与本批主要产出。
⚠ 同时更新 `docs/交接包_给上级线.md`：

```bash
python3 tools/handoff_pack.py
```

⇒ 跨线交接**由脚本生成，不由人转述**。转述会丢限定词，
而「C卷同族」硬化成断言、「63组」变成幽灵，都是这么来的。

## 收工前的三个自问

1. **我这批报出的每一个数，分母是怎么来的？**
   （`not_applicable`／无锚不进分母；`unknown` 不进分子；分母须由枚举产生）
2. **我这批有没有作过否定性断言？如果有，那次检索带截断参数了吗？**（A2）
3. **我有没有把「本批已改」当成修复？** 修复的单位是**类**，不是条 ⇒ 见 `hxs-postmortem`。
