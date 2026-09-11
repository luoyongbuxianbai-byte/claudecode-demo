#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manifest.py —— 关键资产清单（87批·用户令要求④·常设纪律）

事故谱系：82批 scratchpad 全清、83批 容器换新克隆工作区全丢，两次皆事后补救。
本清单之用途：**每批核一次数量与行数**，任何一项行数骤减或消失，即刻可见。

用法：
    python3 tools/manifest.py            # 打印清单
    python3 tools/manifest.py --write    # 写入 MANIFEST.md 并入库
    python3 tools/manifest.py --check    # 与 MANIFEST.md 比对，有减少即非零退出
"""
import hashlib
import os
import subprocess
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "MANIFEST.md")

# (类别, 路径或目录, 是否目录)
ASSETS = [
    ("引擎·V7.9",  "hxs_engine_v79_full.md",       False),   # 114批起：只读·迁移源
    ("引擎·V8",    "V8",                           True),    # ⭐114批起：当前结构底座
    ("规范",       "docs",                         True),    # 120批
    ("IR·schema",  "schema",                       True),    # 120批
    ("IR·规则",    "rules",                        True),    # 120批
    ("编译器",     "compiler",                     True),    # 120批
    ("参考执行器",  "runtime",                      True),    # 120批
    ("测试",       "tests",                        True),    # 120批
    ("研究层证据",  "evidence",                     True),    # ⭐121批：研究层，禁入 runtime
    ("引擎·执行核", "hxs_engine_执行核.md",          False),
    ("引擎·执行件", "hxs_engine_执行件.md",          False),
    ("白皮书",     "白皮书",                        True),
    ("摘录",       "摘录",                          True),
    ("工具",       "tools",                        True),
    ("语料",       "sources",                      True),
    ("报告",       "reports",                      True),
    ("状态层",     "state_layer",                  True),
    ("术语层",     "term_layer",                   True),
    ("医案层",     "case_layer",                   True),
    ("留出区",     "holdout",                      True),
    ("指令",       "指令",                          True),
    ("检索式",     "检索式",                        True),
]

TEXT_EXT = {".md", ".py", ".txt", ".json", ".csv", ".tsv"}


def _lines(p):
    try:
        with open(p, "rb") as f:
            return f.read().count(b"\n") + 1
    except Exception:
        return 0


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()[:12]


def collect():
    rows = []
    for cat, rel, isdir in ASSETS:
        p = os.path.join(B, rel)
        if not os.path.exists(p):
            rows.append((cat, rel, 0, 0, 0, "⛔缺失"))
            continue
        if isdir:
            n = tot = size = 0
            for root, _, fs in os.walk(p):
                if os.sep + ".git" in root:
                    continue
                for f in fs:
                    if f.startswith("."):
                        continue
                    fp = os.path.join(root, f)
                    n += 1
                    size += os.path.getsize(fp)
                    if os.path.splitext(f)[1] in TEXT_EXT:
                        tot += _lines(fp)
            rows.append((cat, rel + "/", n, tot, size, ""))
        else:
            rows.append((cat, rel, 1, _lines(p), os.path.getsize(p), _sha(p)))
    return rows


def render(rows):
    try:
        head = subprocess.check_output(
            ["git", "-C", B, "rev-parse", "--short", "HEAD"], text=True).strip()
        branch = subprocess.check_output(
            ["git", "-C", B, "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(
            ["git", "-C", B, "status", "--porcelain"], text=True).strip()
    except Exception:
        head = branch = "?"
        dirty = ""
    L = ["# MANIFEST · 关键资产清单",
         "",
         "**87批立（用户令）。每批核一次数量与行数——任何一项骤减或消失，即刻可见。**",
         "生成：`python3 tools/manifest.py --write` ｜ 核对：`--check`",
         "",
         "| 项 | 值 |",
         "|---|---|",
         "| 分支 | `%s` |" % branch,
         "| HEAD | `%s` |" % head,
         "| 工作区 | %s |" % ("**⚠ 有未提交改动**" if dirty else "干净"),
         "",
         "| 类别 | 路径 | 文件数 | 行数 | 字节 | 校验 |",
         "|---|---|---:|---:|---:|---|"]
    for cat, rel, n, ln, sz, sha in rows:
        L.append("| %s | `%s` | %d | %d | %s | %s |"
                 % (cat, rel, n, ln, "{:,}".format(sz), sha))
    L += ["",
          "## 常设纪律（87批·用户令）",
          "",
          "1. **凡丢失后需重做之物，当批结束即 commit**——工具、中间数据、摘录、映射表、"
          "检索式，全部入库，**不得只存 scratchpad**。",
          "2. **每批报告首行报 commit 号与文件清单。**",
          "3. **每批开工第一动作：核对远端与本地是否一致**（闸门9 第五款）。",
          "4. **本清单每批核一次**（`python3 tools/manifest.py --check`）。",
          "5. **凡清洗/转换后报前后字数比，降幅 > 20% 即停并报**"
          "（协议16，实装于 `tools/corpus_guard.py`，"
          "开工预检 `python3 tools/corpus_guard.py --audit`）。",
          ""]
    return "\n".join(L)


def parse_existing():
    if not os.path.exists(OUT):
        return {}
    d = {}
    for ln in open(OUT, encoding="utf-8"):
        if ln.startswith("| ") and "`" in ln and ln.count("|") >= 7:
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            if len(c) >= 5 and c[2].isdigit() and c[3].isdigit():
                d[c[1].strip("`")] = (int(c[2]), int(c[3]))
    return d


# ── 100批新增·产出新鲜度断言 ────────────────────────────────
# 事故谱系：yao_bagang.py 自 76批 起崩溃，附录F 三十余批未生成而历批照引其数；
#   附录E/G/N2/O2/P2 表旧于其工具；附录D 直接缺失。
# ⛔ 本工程之工具失败有两类：①跑了但结果错（assert 与人读能拦一部分）
#   ②**根本没跑／跑崩／产出过期**——**此类此前完全无防护，且是主因。**
# 本检即为②之防护：表比其工具旧 ⇒ 该表所载之数已不可引用。
PRODUCT = [
    ("term_layer/附录D_全局否决索引.md",             "tools/veto_index.py"),   # ⚠100批订正：原写「全判据索引/verdict_extract」，二者皆错
    ("term_layer/附录E_十二书否决与限定全量索引.md",   "tools/veto_full_scan.py"),
    ("term_layer/附录F_方八纲对应表.md",             "tools/yao_bagang.py"),
    ("term_layer/附录H_加减三元组.md",               "tools/jiajian_triple.py"),
    ("term_layer/附录I_方剂结构表.md",               "tools/fang_structure.py"),
    ("term_layer/附录J_部位病位对照表.md",            "tools/buwei_bingwei.py"),
    ("term_layer/附录K2_状态组合表与单状态方表.md",     "tools/zhuangtai_tables.py"),
    ("term_layer/附录L2_功能位与剂量判据层.md",        "tools/gongnengwei.py"),
    ("term_layer/附录M2_三毒与肾虚归属对照表.md",      "tools/sandu_shenxu.py"),
    ("term_layer/附录N2_胡老明标规则集.md",           "tools/guize_marker.py"),
    ("term_layer/附录O2_特异指征反噬表.md",           "tools/tezheng_fanshi.py"),
    ("term_layer/附录P2_服后反证表.md",              "tools/fuhou_fanzheng.py"),
    ("term_layer/必要条件表.md",                    "tools/biyao_tiaojian.py"),   # 102批
    ("term_layer/标记面清单.md",                    "tools/biaoji_mian.py"),      # 104批
    ("state_layer/方剂组成.json",                  "tools/fang_compose.py"),     # 106批
    ("term_layer/格子表.md",                      "tools/gezi_biao.py"),        # 108批
    ("term_layer/资产地图.md",                     "tools/zichan_ditu.py"),      # 112批
    ("term_layer/同题双答表.md",                   "tools/tongti_shuangda.py"),   # 116批
    ("term_layer/必要条件_适用域候选类型.md",        "tools/shiyongyu_fenji.py"),   # 118批重写
    ("term_layer/P0真实下游依赖审计.md",           "tools/chuanbo_shenji.py"),    # 119批重写
    ("term_layer/P0真实下游依赖审计_120批.md",     "tools/yilai_shenji_120.py"),  # 120批·76/76 全读
    ("term_layer/P0复合前件合法性复核.md",         "tools/yilai_shenji_120.py"),  # 120批
    ("runtime/compiled_rules.json",             "compiler/compile_rules.py"),  # 120批
    ("evidence/最小翻转对证据集.md",              "tools/fanzhuandui.py"),       # 121批
    ("evidence/二味方低复杂度验证集.md",           "tools/fanzhuandui.py"),       # 121批
    ("evidence/翻转组_三组五栏重编码.md",          "tools/wuceng_chongbian.py"),  # 122批
    ("evidence/翻转组_结构补齐_123批.md",          "tools/jiegou_buqi_123.py"),   # 123批
    ("term_layer/P0候选确认类型传播矩阵.md",       "tools/chuanbo_shenji.py"),    # 119批
    ("term_layer/unknown_false审计.md",          "tools/unknown_shenji.py"),    # 119批
    ("term_layer/资产索引_供上级审查.md",            "tools/zichan_suoyin.py"),     # 116批
]


# ⛔⛔ 人录件（**有产出工具，但工具里的数据是人手录入的**）——单列，不得与 MANUAL 混
#    与 MANUAL 之别：MANUAL 无工具，重跑不能；本类**能重跑，但重跑只重排版，不重取证**。
#    ⇒ 故 `--fresh` 对本类之「新鲜」只证【排版是新的】，**不证【证据是新查的】**。
HANDCODED = [
    ("evidence/最小翻转对证据集.md", "tools/fanzhuandui.py",
     "121批立·⭐**研究层**·11 组翻转组＋4 型反例。"
     "⛔⛔**122批 已改名并加勘误横幅，引用前必读该横幅**："
     "①原名【最小翻转对】之『最小』未证，已撤——真正单观察项且无须施治者**只 FLIP-01／FLIP-05 两组**；"
     "②**四模型计数 0/6、1/4、0/8、9/0 全部作废**（M2/M3 被我定成稻草人，M4 述得过宽）；"
     "③CE-02「胡老未给分野项」**事实相反，已撤**〔讲金匮·113444 明给呕逆／心下痞坚〕。"
     "⛔**研究层证据未经反例攻击不得进入 Typed IR runtime**（令十）——`rules/`、`runtime/` 一字未改。"),
    ("evidence/翻转组_结构补齐_123批.md", "tools/jiegou_buqi_123.py",
     "123批·11 组 ×14 栏。⭐Stage 已拆三栏（process_stage／treatment_history／state_transition）。"
     "⛔**反例检索 11 组全部未做**——`falsifier` 栏写的是「什么能推翻本组」，不是「查过没有」。"
     "⇒ 依令十不得入 Typed IR runtime。"
     "⛔最小性：真「单项且无须施治」者只 FLIP-01／FLIP-05 两组；"
     "带预设鉴别分支之诊断性干预只 FLIP-03／FLIP-08 两组。"),
    ("evidence/residual_台账_123批修订.md", "（人录·无工具）",
     "123批·**R4 更名 `SCHEMA-GAP-ORDINAL`**：是【工程表示缺口】不是【理论结构缺口】——"
     "原文本有程度结构（热多/寒多、脓未成熟/将成/已成）。"
     "⛔ ordinal 取值只七枚，`numeric_scale_forbidden` 恒 true，**不得编 0–10 数值**。"
     "⚠ 已编码变量只 3 个，其中『疼痛程度』为**未取锚之占位**。"),
    ("term_layer/脉象裸映射审计_123批.md", "（人录·无工具）",
     "123批·三格逐条审。⭐`阳明气分` 与 `心血虚` **十二书全数检索，总命中 0** ⇒ 以【无源】否决，"
     "非以反例否决。⛔`结代→炙甘草汤` 直映撤销（〔C卷·145807〕「平人脉结并不足虑，即不服药亦可自愈」）。"
     "⛔`数=热` **未改为「数≠热」**——肠痈反例只证伪【数/洪→热实→可攻下】跨层直通。"
     "⚠ 同表另有五格（浮/紧/缓/细/微）同型而**本批未审**，一律 fail_closed。"),
    ("evidence/组合判定元规则_125批.md", "（人录·无工具）",
     "125批·令九。⭐**答案是『是』，且胡老正是对脉说的**：〔讲伤寒·112879〕「**不能光凭脉，必须脉证结合起来看**」"
     "「**不问证候就给开调胃承气汤，那是不行的**」。十二书检得 14 段，其中 6 段为 `hu_lecture`。"
     "⇒ 八格脉象 cell 之 fail_closed **由【我方谨慎】变为【照胡老说的办】**。"
     "⛔但此条不得替代逐格审计——它说【不得单凭】，不说【脉与某状态无关】。⛔不进 runtime。"),
    ("docs/说话主体与版本_十二书体例_125批.md", "（人录·无工具）",
     "125批·令七。⭐卷首实查：**讲伤寒／讲金匮＝胡老讲课记录**；"
     "**经方传真（2008）／解读张仲景医学（2006）＝冯世纶、张长恩主编之整理本**，各条注解之执笔人书中未标。"
     "⇒ FLIP-08 之归因改写，**不得写「胡老自身两本说法相反」**。"
     "⛔⛔并报一处缺口：**C卷（引用最多的一本）全书无编者信息，speaker 未定**。"),
    ("rules/text_critical_v0.json", "（人录·无工具）",
     "125批·令八。text-critical gate 首批二样本：**§214 `rejected_by_hu`**（胡老「其中必有错乱，**故不释**」）"
     "＋§25 洪大 `emended_by_hu`。⛔硬规则：胡老判为错简/错乱/传抄误并拒绝解释之文本，"
     "**不得作正证或反例，只可作 text-critical evidence**。回归 `tests/test_text_critical_gate.py`。"),
    ("evidence/反例攻击_四组_124批.md", "（人录·无工具）",
     "124批·令十一。⛔**125批 勘误：实为四组动【二】组**——FLIP-03 之 scope_split 已撤（所据第214条被胡老判为错乱而不释）。⭐原文：**四组一攻动三组**：FLIP-01 `scope_split`（胡老「他这个不可下，这个脓已成，**要活看**」）｜"
     "FLIP-03 `scope_split`（§214 同一试治同一观察而 decision 不同，且多一支【里虚·为难治】）｜"
     "FLIP-08 `disputed`（**注解本作迁移、讲课本作共存，两本相反**）｜FLIP-05 未命中但查出 source_layer 判错。"
     "⛔凡未命中者一律写 `not_found_within_audited_scope` 并附检索式，**不写「无反例」**。"),
    ("evidence/FLIP-03_FLIP-08_重编码_124批.md", "（人录·无工具）",
     "124批·令四、令五。⛔**撤销「燥屎形成阶段」**——我把【火候】（用药时机）读成了【病理阶段】"
     "〔讲伤寒·262358「作为用大承气汤的火候或标准，**不为大便硬而设**」〕。"
     "⭐但另在 **§251（非 §209）** 查得真形成关系：未定成硬→屎定硬，两档＋机制（小便利）＋等待（须…乃可）。"
     "⛔FLIP-08 `transition_status=disputed`，不得强写 state_transition=true。"),
    ("term_layer/脉象裸映射审计_124批.md", "（人录·无工具）",
     "⛔**125批 勘误：其第四节「八格里四格对象词十二书零命中」之统计已作废**——「胃气」实有 740 处，「心血虚」概念以『血不足以养心』22 处表达，「阳衰」在编纂本有 21 处。重算见 `rules/pulse_cells_v0.json` 之 `term_audit_125`。｜124批·令六、令七、令十。⭐`洪大` 已拆两命题：A(→阳明气分)**无源** vs B(→热盛于里)**五处锚**——"
     "⛔不得因 A 无源而连 B 一起删。⭐`数=热` 对象层级审计：35 处严式命中归并后"
     "**无一处是独立断言**，全是当场自限或须与他项合用。⭐余五格已逐格审："
     "`缓` 与 `微` **二格无源**（缓之「胃气」零命中、微之「阳衰」在胡老本人两部零命中），"
     "`浮` 被胡老明文自限（「浮不一定主表的」），`紧` 在肠痈域所主为【实】非【寒】，"
     "`细` 唯一 source_verified。**八格仍全部 fail_closed／inactive／support_only，无一放行。**"),
    ("docs/故障源计数口径_v0.md", "（人录·无工具）",
     "124批·令九。⛔**撤回 123批「主要故障源已迁移」之说**——没有统一分母不得排序。"
     "现行准许之表述：「测试器／审计工具错误已成为高频且不可忽略的独立故障源。」"
     "⚠并记：本工程现在**连自己的错误率都算不出来**（四项口径一项不齐），此本身即一项缺口。"),
    ("evidence/翻转组_三组五栏重编码.md", "tools/wuceng_chongbian.py",
     "122批立·上级令 B 之重编码。⛔**未照「五层」写，改为【三组五栏】**——"
     "Observable／LatentState／Stage 是状态本体，Intervention 是测量手段，Decision 是决策输出，"
     "三类不同的东西不得排成一列（即上级本批纠正 R1 时所指之同一种混层）。"
     "⛔并载本批两处我方判错：FLIP-02 与 CE-02 之「原文未给入口」皆为**取证半径太小**所致，"
     "已改判并立自约束。⛔121批 之四模型计数（0/6、1/4、0/8、9/0）**全部作废，不得引用**。"),
    ("evidence/residual_台账_122批修订.md", "（人录·无工具）",
     "122批·residual 由 5 条减至 **1 条（只余 R4 程度非二值）**。"
     "⛔**该减法不是进展**：R1/R2/R3 只是换到正确的栏，R5 是发现本来就有归处"
     "（`source_layer`，120批 已立而 121批 未用）。"),
    ("evidence/二味方低复杂度验证集.md", "tools/fanzhuandui.py",
     "121批立·5 首二味方逐首人读（桔梗汤｜芍药甘草汤｜甘草干姜汤｜桂枝甘草汤｜枳术汤）。"
     "⛔**本批不解释药性**（用户令七）；表中功能语皆原文逐字。"
     "⛔并记本批一处测量失误：初以正则数药味得「C卷二味方 31 首」，**该数错**"
     "（桂枝汤 5 味被误计），**未报该数，改逐首人读**；全库二味方实数**至今未点**。"),
]

# ⛔ 手工件（无产出工具，故无法重跑、无从验证是否随语料更新）——本身即为一类风险，单列
MANUAL = [("docs/RULE_SCHEMA_V0.md",
           "120批立·⭐**Typed IR 规范**（用户令四、十）。五维正交："
           "rule_effect／validation_status／observation_state／runtime_status／source_layer。"
           "⛔七条硬锁由 `compiler/lint_rules.py` 实装。"
           "**最要紧者：validation_status != runtime_status——「规则有出处」不是「患者已确诊」。**"),
          ("schema/rule_v0.json",
           "120批·Rule IR 之 JSON Schema。"),
          ("rules/core_v0.json",
           "120批·⭐首批 Typed IR 规则 5 条。含 `NEC-TAIYANG-WUHAN`（**falsified_overbroad·inactive**，"
           "§172 反例已挂）、`S70-HANHOU-SHI`（**stage_conditional·发汗后 scope 已锁**）、"
           "`NEC-LGZG-QICHONG`（speaker uncertain ⇒ fail_closed）、"
           "`JUEYIN-SHANGREXIAHAN`（L5 vs L4 ⇒ disputed·inactive）。"),
          ("term_layer/太阳提纲_作用域与反例矩阵.md",
           "120批·⛔**撤销 119批 之「太阳病⇒恶寒 D5 硬门」与「本工程第一条完成四条件者」二说**。"
           "反例〔讲伤寒·188178 §172〕；⭐并新发现**同一 §172 胡老另一书作相反之读**"
           "〔C卷·125102「太阳病之发热恶寒」〕⇒ text_status=disputed。"),
          ("term_layer/§70_病程适用域审计.md",
           "120批·§70 恢复【发汗后】scope；T15/T15b 已证 scope 真实生效于 reference runtime。"),
          ("term_layer/版本与source_layer规范.md",
           "120批·六层 provenance ＋ speaker_status ＋ text_status；L5 不得静默覆盖 L4/L2。"),
          ("term_layer/苓桂术甘_说话主体与反例状态.md",
           "120批·维持 fail_closed；解锁条件＝定【临床应用】栏之层级。"),
          ("docs/ASSERTION_TYPE_SPEC.md",
           "119批立·⭐**断言类型最小规范**（用户令一）。七类 assertion_type ＋五态 observation_state ＋"
           "传播格。⛔其参考实现为 `tools/assertion_engine.py`，**只证规范可解析，不证 LLM 照做**。"),
          ("term_layer/必要条件_D5反例攻击.md",
           "119批·⭐D5 唯一跨场景候选（讲伤寒·2288 太阳病提纲三征）之反例攻击。"
           "⛔结论：**三项合取式已证伪**（栝蒌桂枝汤条：太阳病而脉反沉迟）；"
           "只余「太阳病⇒恶寒」一项，四处互证。**本工程第一条走完晋升四条件者**，"
           "但状态记为 `confirmed·检索范围有限`，非「已证明无反例」。"),
          ("term_layer/苓桂术甘_必要条件反例审计.md",
           "119批·同域反例攻击。⛔**卡在【说话主体未定】**：【临床应用】栏未经体例界定，"
           "不能径称胡老说。⭐并记一处自我克制：刘某案未载气冲而有效，"
           "**但『未载』是 unknown_not_recorded 不是 absent_explicit，故不构成反例**——"
           "若据以反证，即犯本工程打了十五批的『未提及=阴性推定』。"),
          ("term_layer/治疗反馈类型.md",
           "119批立·七类治疗反馈及其权重。⛔撤「治疗反应=病机最硬证据」。"
           "唯【原文预先给出分支预测】者方为诊断性试治。并区分「以方测证」(读原文之法) 与"
           "「治疗有效反推病机」(判病例之法)——V8 原条混二者为一。"),
          ("backup/hxs_engine_v8_full_v2_改前_119批.md",
           "119批·⛔**类型标注与三项旧P0修改前之原件·不得删**。"),
          ("backup/必要条件_适用域分级_116批作废.md",
           "⛔**116批 作废件**：该批分诊用错载入器（`read().replace` 只去换行），"
           "而锚是 `corpus_guard.load_one()`（去尽空白＋去 JUNK）之字位，相差上千字"
           "——**读的是别处的文字**。其 D0–D5 全部数字作废。留档备追溯，**不得引用其数**。"
           "现行件为 `term_layer/必要条件_适用域候选类型.md`。"),
          ("backup/V8v2_盲测段原件_L20558-L20623_117批.md",
           "117批·⛔**归档原件·不得删**（协议16）。P0-7 盲测段自 V8 v2 执行版移出前之原样，"
           "66 行（病例区＋金标准区）。移出经用户令明文授权，git 亦可追溯。"),
          ("backup/hxs_engine_v8_full_v2_改前_117批.md",
           "117批·⛔**P0 修复前之 V8 v2 原件·不得删**。16 处改动之比对基线，"
           "`python3 tools/v8_p0_fix.py --check` 可对其重放。"),
          ("backup/hxs_engine_v8_full_v2_改前_118批.md",
           "118批·⛔**文本订正前之 V8 v2 原件·不得删**（P0-1 论证／P0-9 缺一不成立／"
           "P0-10 对象枚举／P0-16 保留状态 四处订正之基线）。"),
          ("V8/blind/病例区_20组.md",
           "115批·⭐P0-7 盲测病例（20组）·**本档不含答案，可入执行上下文**。"
           "⛔与 `金标准_禁入执行上下文.md` **必须分档**——原套件二者同文件相隔 29 行，"
           "仅以文本「禁读」作隔离；98批 T5 答案逐字在引擎 L9211 即同型事故。"
           "⛔跑 P0-7 前须先把 V8 v2 L20558–20622 之原段移出引擎，否则读引擎即读得答案。"),
          ("V8/blind/金标准_禁入执行上下文.md",
           "115批·⛔⛔**只供 Evaluator**。任何执行会话不得打开。20 条金标准。"),
          ("V8/114批_基线冻结与差分验收.md",
           "114批立·⭐V8 基线冻结之七项交付（结构地图/完成状态/P0冲突清单/两层状态机/三级接口/"
           "人读问题清单/静默错误风险）。⛔**其 P0 数不得由 tools/v8_p0scan.py 直接覆盖**——"
           "该器本批实测**误检 67%**（L429/430 系 V8 明确否定之等式被计为冲突）**且我人读亦漏检一处**"
           "（真冲突 2→3，漏 L18865）。**机械命中数永不得充作冲突数，本册所载皆经逐处人读裁决。**"),
          ("term_layer/附录G_八纲三毒客观判定表.md",
           "56批手写·62行·⛔无产出工具，语料由九书增至十二书后从未随之更新"),
          ("term_layer/位性全谱表.md",
           "107批立·⭐用户令之九栏规格表：3位＋3性组 × ①定义②本位标位③要不要处理④治则治法"
           "⑤禁忌⑥充分条件⑦必要条件⑧充分必要⑨判据五路。⛔现 39/78＝50.0%，"
           "三个全空栏（③要不要处理／⑧充分必要／⑨反证），每批须报填充进度。"),
          ("term_layer/统一对应表.md",
           "106批立·⭐用户令之核心表：症候×八纲×六经×三毒×药物，五类判据合一。"
           "工具 tongyi_yansuan.py 读其编码副本（TONGYI 常量），本文为人读正本。"
           "⛔三毒栏 1/16 有值，为全表最大缺口，每批须报其填充进度。"),
          ("term_layer/显隐映射表_人读判定.md",
           "104批立·⭐人读判定册（显隐映射 148 条）。工具不得写入。"
           "每批须报『已读/命中』比例。"),
          ("term_layer/必要条件表_人读判定.md",
           "103批立·⭐人读判定册，工具不得写入。与 `必要条件表.md`（工具候选池）分离，"
           "因 102批 将判定写在工具产出内，重跑即被覆盖——乙类事故同型。"
           "本册无新鲜度约束（人读之物不随语料自动过期），但每批须报『已读/候选池』比例。")]


def fresh():
    print("== 产出新鲜度（表须不旧于其工具，否则其数不可引用）==\n")
    bad = miss = 0
    for prod, tool in PRODUCT:
        pp, tp = os.path.join(B, prod), os.path.join(B, tool)
        name = os.path.basename(prod)
        if not os.path.exists(tp):
            print("  %-34s ⛔工具缺失 %s" % (name[:32], tool)); bad += 1; continue
        if not os.path.exists(pp):
            print("  %-34s ⛔产出缺失——工具在而表不在，疑跑崩" % name[:32]); miss += 1; continue
        dp, dt = os.path.getmtime(pp), os.path.getmtime(tp)
        if dp < dt:
            print("  %-34s ⛔表旧于工具 %.1f 小时——须重跑，其数暂不可引用"
                  % (name[:32], (dt - dp) / 3600)); bad += 1
        else:
            print("  %-34s ✅" % name[:32])
    print("\n结果：%d/%d 新鲜｜⛔过期 %d｜⛔缺失 %d"
          % (len(PRODUCT) - bad - miss, len(PRODUCT), bad, miss))
    if HANDCODED:
        print("\n⛔⛔ 人录件（**有工具、能重跑，但工具里的数据是人手录的**——")
        print("     故上表之「新鲜」**只证排版是新的，不证证据是新查的**）：")
        for m, tool, why in HANDCODED:
            print("   %-34s ←%s" % (os.path.basename(m)[:32], tool))
            print("       %s" % why)
    if MANUAL:
        print("\n⚠ 手工件（无工具，不可重跑，其数须人读复核）：")
        for m, why in MANUAL:
            print("   %-34s %s" % (os.path.basename(m)[:32], why))
    if bad or miss:
        print("⛔ 有过期或缺失项——**引用其数前须先重跑**。")
    return 1 if (bad or miss) else 0


def main():
    rows = collect()
    if "--fresh" in sys.argv:
        return fresh()
    if "--check" in sys.argv:
        old = parse_existing()
        if not old:
            print("⚠ 无 MANIFEST.md 可比对，先跑 --write")
            return 1
        bad = 0
        for cat, rel, n, ln, sz, sha in rows:
            if rel in old:
                on, ol = old[rel]
                if n < on or ln < ol:
                    print("⛔ %s `%s` 减少：文件 %d→%d，行 %d→%d" % (cat, rel, on, n, ol, ln))
                    bad += 1
        print("核对完毕：%s" % ("⛔ %d 项减少，先查明再动" % bad if bad else "✅ 无减少"))
        return 1 if bad else 0
    txt = render(rows)
    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write(txt)
        print("已写入 %s" % OUT)
    else:
        print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
