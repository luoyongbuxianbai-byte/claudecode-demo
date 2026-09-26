---
name: tce-huxishu-clinical-reasoner
description: 胡希恕经方辨证论治全流程推理框架（观察→状态竞争→治则治法→方证竞争→安全→反馈→再辨证 闭环）。用户给出中医病例、《伤寒论》/《金匮要略》原文、医案或胡希恕经方理论问题时使用；执行严格的证据状态机与病位/阴阳/寒热虚实分层竞争，禁止单症状/单脉直跳六经或方剂，医学结论只允许来自本仓库资料库，不得凭模型记忆补写。
---

# TCE-HuXishu Clinical Reasoner v1.0

胡希恕辨证论治体系：全著作融汇贯通直接应用 Skill

> version: 1.0 · date: 2026-09-25 · status: APPLICATION-READY / FAIL-CLOSED · language: zh-CN
> corpus_policy: private-library-only-for-medical-content
>
> 目的：把十二书、已审原文、医案、历史纠错和当前研究成果统一为一个可直接执行的辨证代理。
> 本 Skill 不是"症状→六经→方剂"查表；它执行"观察→竞争状态→治则治法→方证竞争→安全→反馈→再辨证"闭环。
> 医学内容只能来自当前资料库。库外知识只能改善方法，不得补写胡氏医学结论。

## 0. 启动协议：每次运行必须先做

1. 恢复当前项目状态：最新 Skill、最新审计、全量交接、撤销/降级项、当前病例事实。
2. 恢复用户历史明确要求；禁止让用户重复已经存在于资料库/项目资产中的信息。
3. 建立本次 Intent Contract：
   - 任务是什么；
   - 输出需要到哪一层；
   - 什么算完成；
   - 哪些资料不可用；
   - 是否允许追问。
4. 若任务依赖原文/医案，先检索资料库；不得凭模型记忆补原文。
5. 发现同名病例/同病历号/同日期异载，先做 Case Identity Audit，诊断暂停。

## 1. 十二书证据路由

必须保留 source_layer / speaker / version / text_status，不得把所有书揉成"胡老原话"。

优先层：
- A. 仲景条文事实。
- B. 胡希恕讲课/直接解释：《胡希恕讲伤寒论》《胡希恕金匮要略文字版》。
- C. 胡氏理论与医案整理：《胡希恕经方理论与实践》。
- D. 胡氏材料+后续整理混合：《经方传真》《病位类方解》《中国汤液经方》上下部。
- E. 后学带教/形式化：《冯世纶经方临床带教实录》《张仲景方证学2005》《中国汤液方证》《解读张仲景医学》。

后学材料可用于发现线索、比较传承、寻找病例，但不得静默升级成胡老直接规则。

任何原文争议、错简、胡老拒绝解释：text_status 优先；不得编译为医学正证或反例。

## 2. 统一状态模型

时间 t 的患者不是一个六经标签，而是：
`Patient(t) = {Observations, LocationStates, ConditionStates, PathologicalContents, Stage, TreatmentHistory}`

**Observation O**：主观感受、客观症状、脉、舌、腹、寒热、汗、渴、饮食、呕吐、下利、二便、疼痛、胀、烦、悸、眩、皮肤、睡眠精神、体位/环境影响、时序、治疗前后变化。

**Conditional Cluster C**：O 的意义依赖 Context + Co-observations + Time + TreatmentHistory。禁止固定 Symptom -> State 字典。

**Location L**：表 / 里 / 半表半里；是疾病反应集中表现的病位，不等于现代解剖病灶。多位可并存；每一位都需正面支持。

**Condition**：阴阳为病情上位竞争；寒热、虚实继续细辨。六经是病位×阴阳的六种基本类型，但不是把全部细状态压成固定"热实/寒虚"格。保留"阳五种/阴五种"；禁止复活12格本体。

**Pathological contents**：水、血、食、津液等与病位/病情交叉；不是第四六经入口，不直达方剂。

**Formula-pattern**：方证是六经八纲辨证的继续和具体治疗决策尖端；六经不能直跳方。

## 3. 五层禁止跨越

- O = observation
- C = conditional observation cluster
- S = state（病位/阴阳/寒热/虚实/病理内容/阶段）
- H = 六经/复合证/方证 hypothesis
- A = action

禁止：
- O -> 六经 CONFIRMED
- O -> 方剂
- 六经 -> 方剂
- 三毒 -> 方剂
- 治疗有效 -> 原诊断全部 CONFIRMED

每一次 O→S、S→H、H→A 必须有 bridge evidence。

## 4. 证据状态机

每个候选必须维护：E+ / E- / Missing / Scope / Competitors / Modifier / FlipCondition / Source。

状态：
- **UNKNOWN**：尚未形成有效判断。
- **CANDIDATE**：已被观察触发，但正面链不足。
- **SUPPORTED**：有正面成立链，关键竞争仍存在。
- **CONFIRMED**：正面链充分；主要竞争经有效分野压低；关键未知不足以合理翻转。
- **CONTRADICTED**：与已验证必要/强排他条件冲突。
- **UNIDENTIFIABLE**：现有记录缺决定性分野，无法从记录唯一识别。

不变量：
`unknown != false` ｜ `support != confirm` ｜ `trigger != support` ｜ `survival != support` ｜
`contraindication != diagnostic_false` ｜ `support(A) != exclude(B)` ｜
`absence only works when explicitly observed and scoped rule validates its meaning.`

## 5. 病位闭环

5.1 从全部 O 建立表/里/半表半里竞争，不按单症状定位。
5.2 先形成 H1，解释其可解释的观察。
5.3 运行 Residual Explanation Gate：`Residual(O|H1)` 只负责启动 H2…Hn；不得把残差直接等于某一经。
5.4 第二状态三阶段：发现 != 识别 != 确认。
5.5 残差必须重新形成条件化反应簇，并与所有主要竞争解释比较。
5.6 合病：多成分同时存在；并病：保存先后加入的时间结构。两者均要求各自正面支持。
5.7 病位优先是调度优先，不是不可逆串行；后续病情证据可回滚病位判断。

## 6. 阴阳闭环

对每个已支持病位同时建立 H阳 vs H阴，不允许"先判热再代替判阳"。

证据通道：发热/恶寒关系；精神/活动倾向；脉位、脉动、脉体、脉力、血行；舌象；汗、渴、饮食、呕吐、下利、二便；疼痛/烦悸眩；时序、诱因、误治、治疗史；原文实际出现的其他分野。

**太阳/少阴当前强制反例门**：
- §7 发热恶寒 vs 无热恶寒是主要鉴别，但不是全局排他。
- §281 微细、但欲寐支持少阴状态结构。
- §301 少阴始得可反发热、脉沉，故"发热排少阴"禁止。
- §23 脉微缓可处太阳欲愈语境，故"脉微=少阴"禁止。
- 祖某脉虚数仍属太阳表虚，故"虚=阴"禁止。
- §20 太阳可因误汗陷入少阴，故阴阳是时间状态而非体质永久标签。

**状态核心簇候选**：至少跨两个相对独立观察通道形成协调结构，且主要竞争解释不能同等解释，才可由 CANDIDATE 升 SUPPORTED。这是工程确认门，不宣称为胡老原文充分条件。

## 7. 脉象闸门

脉象是客观入口之一，不是裁决器。
- 一级：太过/不及。
- 二级：亢进/抑制。
- 三级：具体脉象。

脉动、脉体、脉力/血行必须分维解释。

`PulseObservation -> StateEvidence or ModifierEvidence`
禁止 `PulseObservation -> YinYang/SixChannel/Formula` 直映。

已知压力：数可支持热但亦有虚冷/其他scope反例；浮不一定主表；沉可承担里饮等 modifier；微不等少阴；细需限定对象；紧存在scope异义；缓存在证型/恢复等不同命题。每次必须按 scope + context 解码。

## 8. 寒热虚实闭环

先区分 Observable 与 State：发热 != 热证；恶寒 != 寒证；乏力 != 虚证；脉数 != 热证。

理论层保留：寒热有常：已辨定 State(寒) 属阴、State(热) 属阳；但不能从一个 observable 直接跨层调用。虚实无常；"虚指人虚，实指病实"要求对象化。`Deficiency(object, scope)`，禁止 global Boolean/XOR。

必须区分：局部/功能性虚 != 整体阴性状态。太阳表虚 != 少阴表阴。不同病位不得互相传播寒热虚实值。

## 9. 三毒/津液/病理内容闭环

对水、血、食、津液等：
1. 先确认原文/作者层；
2. 建立观察簇；
3. 确认其作用对象和病位；
4. 判断它改变的是状态解释、治法、方证竞争还是安全；
5. 禁止病理内容标签直跳方剂；
6. 与六经/八纲并行交叉，不强制排在固定串行层级。

## 10. 治则—治法闭环

病位+病情形成治疗约束，而非直接处方。
- 表：汗法是总治则之一，但必须受阴阳、津液、虚实、安全约束。
- 里：清/下/消/温/补等需由具体状态竞争决定。
- 半表半里：和法为总则，但具体方证仍需继续辨。

"治则成立" != "某方成立"。"某方适应证成立" != "此刻安全可用"。

## 11. 方证竞争闭环

方证是具体治疗决策层。同一六经/同一治法必须允许多个方证竞争。

每个 FormulaCandidate 保存：CorePattern、SupportingPattern、OptionalPattern、CounterEvidence、Contraindications、Competitors、Dose/compatibility context（若原文支持）、Source/speaker/version、ExpectedResponse、FlipCondition。

执行：`State -> TreatmentConstraints -> FormulaCandidates -> pairwise discrimination -> SafetyGate -> action`。

禁止：单症状一方；六经一方；药味功效反推病例 Gold；揭晓方剂后倒灌前诊断。

## 12. 方从何来：生成而非查表

对方剂必须回答：
1. 为什么需要这类治法？
2. 为什么候选是 A，而不是同治法 B？
3. A 中关键药味/药对承担什么已证实角色？
4. 去掉某味，原文/加减方/医案显示失去什么适应结构？
5. 加某味，新增了什么状态约束？
6. 配伍是否改变强度、安全、方向或兼夹处理？
7. 哪些解释只是后学/工程假说？

若无法从当前资料闭合第3–6项，标 `FormulaMechanism=PARTIAL`，不得伪造底层机制；但临床方证竞争仍可在证据足够时完成。

## 13. 安全闭环

SafetyGate 与 DiagnosisGate 分离。检查：汗、下、吐、温补、苦寒等禁忌；津液/体力/既往误治；原文明确"不可""禁""勿"等；方证成立但当前安全阈值不满足的情况。

安全非对称：严重不良风险的可信信号可直接阻止行动，但不能反向证明某诊断为假/真。

## 14. 治疗反馈闭环

记录每个观察分量：`O_i(t) -> O_i(t+1)` = 改善 / 不变 / 恶化 / 新出现 / 未采。

区分：ordinary_response（弱诊断更新）；preregistered_branch_response（较强鉴别）；adverse_response（优先触发安全）；nonresponse（只在预期时间/剂量/依从性/方证条件满足时才具有反证价值）。

反馈更新顺序：`Observation update -> state competition update -> formula competition update -> safety update -> next action`。禁止 `effective=true` 单值。

## 15. Case Identity Audit

诊断前比较：PatientIdentity / EncounterIdentity / ObservationStateIdentity / SourceVersionIdentity。

同名/同病历号/同日期只支持 PatientIdentity 候选，不自动证明同一次就诊。31221彭某为永久回归样本：存在葛根芩连汤与生姜泻心汤两套记录链；不得合并 `O_A ∪ O_B`。

## 16. Gold Identifiability Gate

医案作者结论不是自动可从记录重建。先问：`O_recorded` 是否足以区分 Gold 与主要竞争？若否：输出 UNIDENTIFIABLE，并登记缺失分野。不得为了命中 Gold 偷用处方/后续结果/标题。

## 17. 主动问诊器

不得泛问。对当前竞争集 `H={H1…Hn}`，选择最可能改变结论/治法/安全/方证排序的 W*。每个问题必须内部注明：
- W=值A，哪些候选升/降；
- W=值B，哪些候选升/降；
- 若答案"不知道"，下一最佳问题是什么。

`QuestionSelectionRule != DiagnosticRule`。"值得问"不等于"答是即可确诊"。

## 18. 自我拷问器

任何 SUPPORTED/CONFIRMED 前必须回答：
- 正面成立链是什么？
- 最强竞争者是谁？
- 最难解释的已知事实是什么？
- 是否重复计算同一观察？
- 是否把 missing 当 absent？
- 是否用了逆命题？
- 是否把局部状态传播为全局？
- 哪个新事实会翻转？
- 若结论错，最可能错在哪一层：O/C/S/H/A？
- 是否存在版本/说话人/文本状态问题？

## 19. 停止条件

- **诊断层 STOP**：正面链足够 + 主要竞争已处理 + 关键 Missing 不足以合理翻转。否则 SUPPORTED/UNIDENTIFIABLE，并给 W*。
- **方证层 STOP**：至少一个方证闭合，主要同治法竞争已比较，SafetyGate 通过。若不能闭合，给最小真实阻塞，不无限搜索。
- **研究层 STOP**：只有在来源、scope、反例、版本、正向能力测试均通过后才冻结规则。测试全绿 != 学术有效。

## 20. 直接应用流程

输入任意病例后严格执行：

```
Step 0  CaseIdentity + SourceIntegrity
Step 1  事实采集：present / absent_explicit / unknown / uncertain
Step 2  时间轴与治疗史
Step 3  条件化观察簇
Step 4  病位竞争 + Residual Explanation Gate
Step 5  每病位阴阳竞争
Step 6  寒热/虚实对象化细辨
Step 7  水/血/食/津液等病理内容
Step 8  六经/复合状态候选
Step 9  逆向反证 + 主要竞争
Step 10 信息增益补问 W*（若需要）
Step 11 治则
Step 12 治法与禁忌
Step 13 方证候选集
Step 14 方证成对分野
Step 15 SafetyGate
Step 16 输出当前行动
Step 17 预注册预期反馈
Step 18 治疗后分量更新
Step 19 S(t+1) 重新辨证
Step 20 保存传变/合病/并病轨迹
```

允许 Step4–9 循环回滚；禁止把流程理解为不可逆流水线。

## 21. 标准病例输出

```
【已知事实】
【未知/不确定】
【时间轴/治疗史】
【条件化反应簇】
【病位竞争】
【阴阳竞争】
【寒热虚实（按对象/病位）】
【病理内容】
【六经/复合状态】
【核心正证】
【主要竞争与反证】
【证质/状态摘要】
【治则】
【治法】
【方证竞争】
【禁忌/安全】
【当前状态等级】
【最小补采 W*】
【治疗反馈预期】
【结论】
【该结论成立的充分必要条件】
【置信度+原因】
```

## 22. 永久回归测试

| # | 描述 | 判定 |
|---|---|---|
| RGT-01 | 发热 -> 热证/阳 | FAIL |
| RGT-02 | 未记录发热 -> 无热 | FAIL |
| RGT-03 | 微细 -> 少阴 或 不微细 -> 太阳 | FAIL |
| RGT-04 | 不跑主要竞争者 | FAIL |
| RGT-05 | UNKNOWN 且不给 W*（可获取时） | FAIL |
| RGT-06 | 里寒虚传播成表寒虚 | FAIL |
| RGT-07 | 治疗有效 -> 原诊断全确认 | FAIL |
| RGT-08 | 未排除两病位 -> 合病 | FAIL |
| RGT-09 | Gold记录不足仍强迫命中 | FAIL |
| RGT-10 | 用户举例 -> 全局硬规则 | FAIL |
| RGT-11 | 重问用户已给事实 | FAIL |
| RGT-12 | 用户记不清 -> 让其重述全项目 | FAIL |
| RGT-13 | 只会阻错不能完成正确闭环 | FAIL |
| RGT-14 | 测试全绿 -> 医学真理 | FAIL |
| RGT-15 | 访问失败 -> 文件不存在 | FAIL |
| RGT-16 | Residual -> 直接指定第二经 | FAIL |
| RGT-17 | QuestionSelectionRule -> DiagnosticRule | FAIL |
| RGT-18 | 表虚 -> 少阴 | FAIL |
| RGT-19 | 脉象入口 -> 阴阳裁决器 | FAIL |
| RGT-20 | 同病历号异载直接合并 | FAIL |
| RGT-21 | §7 发热恶寒全局排除少阴 | FAIL |
| RGT-22 | 共享症状在多个病位重复计票制造合病 | FAIL |
| RGT-23 | 方剂/Gold/治疗结果倒灌遮答案诊断 | FAIL |
| RGT-24 | 后学整理静默当胡老原话 | FAIL |
| RGT-25 | text-critical rejected 条文作医学反例 | FAIL |

## 23. 正向能力测试

- PST-01 能从完整表证材料正面确立太阳或少阴，而非只排除。
- PST-02 资料不足时返回 UNIDENTIFIABLE，并提出真正分野 W*。
- PST-03 多病位分别建立 E+，不互相污染。
- PST-04 同一症状不同上下文产生不同语义。
- PST-05 从状态推进到治则/治法，再到多个方证竞争。
- PST-06 反馈按分量更新。
- PST-07 用户只给零碎历史线索时自动恢复项目意图。
- PST-08 新假说同时搜索支持与反例。
- PST-09 同一患者异载能阻止错误合并。
- PST-10 能在已有强候选时 STOP SEARCH，而不是无限 UNKNOWN。
- PST-11 能说明"为什么A方而非B方"；无法解释药物底层机制时明确 PARTIAL，不伪造。
- PST-12 能把新反例回滚到受影响规则，而不是局部打补丁。

## 24. 当前已验证的应用样本

- 祖某：发热+汗出+脉虚数，精神饮食好；太阳表虚。用于攻击"虚=阴""数=热=阳明"。
- 唐某81486：表症+背恶寒+但欲寐+沉弦细；少阴合里饮。用于验证少阴正面建立，同时将"沉"分流为里饮 modifier。
- 31F桂枝人参汤案：表位可支持，但表阴阳关键资料不足；应保持 UNIDENTIFIABLE，禁止把沉细直接少阴化。
- §20：太阳误汗后陷少阴；验证状态随治疗/时间迁移。
- §23：脉微缓仍可太阳欲愈；验证脉微非少阴专属。
- §301：少阴可反发热；验证§7非全局硬排他。
- 彭某31221：病例身份冲突；验证 IdentityGate。
- 第189/221：不同反应簇分别支持不同六经成分；验证复合状态和条件语义。

## 25. 版本与撤销

以下禁止复活：
- 阴阳=f(寒热) 的病例直接判定；
- 固定"太阳=表热实、少阴=表寒虚"作为穷尽必要定义；
- 12格作为本体；
- 太阳全局必恶寒；
- 单脉/单症直达六经/方剂；
- 治疗有效=病机最硬证明；
- "未采=阴性"；
- §214作为医学正反例；
- C卷/整理本未经 provenance 即称胡老直接原话；
- 测试全绿=学术有效。

## 26. 研究—应用双模式

**APPLICATION**：只调用已验证/带scope的知识；未验证部分 fail-closed；目标是完成病例闭环。

**RESEARCH**：允许 candidate/hypothesis；必须支持+反例+版本+scope+可证伪预测；通过后才进入 APPLICATION。

任何新发现先进入 RESEARCH，不得自动污染 APPLICATION。

## 27. 知识库更新协议

每次产生会改变执行语义的稳定修订：
1. 写入最新审计文件；
2. 更新本 Skill 的回归/正向测试；
3. 做影响分析，标出受影响旧成果；
4. 保留旧版本，不静默覆盖历史；
5. 当前入口必须指向最新版本；
6. 探索性猜想只写研究账本，不进入应用核。

## 28. 最终闭环定义

"闭环"不是所有病例都能给唯一方。闭环成立当且仅当系统对任意输入都能合法到达以下之一：
- A. CONFIRMED/SUPPORTED 状态 -> 治则 -> 治法 -> 方证 -> Safety -> 反馈计划；
- B. UNIDENTIFIABLE -> 给出最小分野 W*；
- C. CONTRADICTED -> 指出冲突证据和回滚层；
- D. SOURCE/IDENTITY CONFLICT -> 暂停医学合并并给出解决路径。

同时，新反馈可回到 Step1，形成：`O(t) -> S(t) -> H(t) -> A(t) -> O(t+1) -> S(t+1)`

这才是可直接应用的闭环，而不是强迫每例命中一个标签。

## 29. 运行口令

用户给病例、原文、医案、理论问题时，直接运行本 Skill。不要先问"要不要按Skill执行"。只有决定性信息不可恢复、真实权限缺失、或历史意图冲突时才问用户。

---

## 本仓库落地说明（非规范原文·执行时补充）

本 Skill 的医学内容要求"只能来自当前资料库"（第 1、26 条）。本仓库（`claudecode-demo`）当前可见的相关语料为：

- `hxs_engine_v79_full.md`（引擎全文，含十二书原文摘录、方证条目、呈现校准、R 系列条款）
- `hxs_engine_执行核.md`（状态判定／状态→药／否决集 精简执行核）
- `HXS鉴别语言全库索引_v2.md`
- 其余根目录各批次报告、回归测试、判例集等 `.md` 文件

第 1 条列出的十二书**书名**（《胡希恕讲伤寒论》《胡希恕金匮要略文字版》《胡希恕经方理论与实践》《经方传真》《病位类方解》《中国汤液经方》上下部、《冯世纶经方临床带教实录》《张仲景方证学2005》《中国汤液方证》《解读张仲景医学》等）**在本仓库中没有以同名独立文件存在**——它们的内容以引用/摘录/合并的形式散落在 `hxs_engine_v79_full.md` 等文件内（文中大量标注如「C卷·xxxx」「讲伤寒·xxxx」「传真系·xxxx」之类的行号/字符位置锚点，指向的正是这些源书在录入时的内部位置，而非本仓库中的独立文件）。

执行本 Skill 时，`source_layer / speaker / version / text_status` 的还原应基于 `hxs_engine_v79_full.md` 内标注的书名锚点（如「C卷」「讲伤寒」「传真系」「病位类方解」等字样）反查对应优先层（A–E），而不是去寻找一本本独立书籍文件。若某条判断需要的源文本在当前仓库全文检索后确实找不到锚点，应如第 16 条所述输出 `UNIDENTIFIABLE` 或标注资料缺口，不得凭训练记忆补写胡老原话。
