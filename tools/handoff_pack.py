#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交接包生成器（126D）——给【不能读仓库】的协作线用。

用户痛点：上级线（claude.ai 对话）读不到仓库，每批都要人工复制粘贴；
而人工复制会**丢限定词**，这正是「C卷同族」硬化成断言、「63组」变成幽灵的机制。

⇒ 本工具从仓库**确定性地**生成一份可直接粘贴的现状摘要，并附每份资产的
   raw URL（本仓库为 public，`private=false` 实测），使对方能自取原文而非听转述。

用法：
    python3 tools/handoff_pack.py            # 写 docs/交接包_给上级线.md
    python3 tools/handoff_pack.py --stdout   # 只打印
"""
import json
import os
import re
import subprocess
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "docs", "交接包_给上级线.md")
REPO = "luoyongbuxianbai-byte/claudecode-demo"

# 对方最可能需要自取的资产。⛔ 只列**现行**件，作废件不列。
KEY_ASSETS = [
    ("schema/retrieval_gates_v0.json", "四闸权威定义（GATE_1–4）"),
    ("rules/text_critical_v0.json", "text-critical 登记（胡老判错简／补字之条）"),
    ("rules/pulse_cells_v0.json", "脉象映射格（格级状态）"),
    ("rules/state_variables_v0.json", "状态变量（ordinal／graded_unscaled）"),
    ("docs/说话主体与版本_十二书体例_125批.md", "十二书 speaker map（卷首实查）"),
    ("docs/C卷_provenance调查_126批.md", "C卷 身份调查（结论：uncertain）"),
    ("docs/取证协议_source_layer_v0.md", "source_layer 命名与检索阶段"),
    ("docs/故障源计数口径_v0.md", "故障源计数口径"),
    ("evidence/审计全集普查与分母修复_126B.md", "全集普查＋四闸分母（现行统计之唯一出处）"),
    ("evidence/下游引用链审计_126B.md", "下游引用链"),
    ("evidence/翻转组_结构补齐_123批.md", "11 组翻转对 × 15 栏"),
    ("evidence/组合判定元规则_125批.md", "M1–M14 元规则"),
    ("MANIFEST.md", "资产清单（每批核一次）"),
]

SPEAKER = [
    ("讲伤寒／讲金匮", "hu_lecture", "可 hu_direct（仍须保留【讲课记录之整理媒介】属性）"),
    ("传真系／解读／病位类方解／汤液经方系／伤寒论传真／金匮要略传真／中国汤液方证／临床家",
     "editor_compiled", "只可 hu_via_editor，表述作「某整理本作……」"),
    ("带教", "editor_compiled_feng", "同上"),
    ("C卷", "uncertain（P0）", "只可 source_unattributed；⛔ 本工程引用最多的一本"),
]

HARD = [
    "speaker_status = uncertain       → ⛔ 禁 hu_direct attribution",
    "speaker_status = editor_compiled → ⛔ 禁自动升级为 hu_direct",
    "publication_date ≠ text_composition_date（⛔ 不得据出版先后论「晚年改说」）",
    "same_style_family ≠ same_book ≠ same_author",
    "⛔ 不允许仅根据文件名推作者",
    "⛔ 未采 ≠ 阴性（协议51）；unknown 不进分子，not_applicable／无锚 不进分母",
    "⛔ 闸门9⑦：不得以检索宣称「全库无此规则」",
    "⛔ 胡老判为错简／错乱／传抄误并拒绝解释之文本，不得作正证或反例，只可作 text-critical evidence",
    "⛔ 测试全绿不作为完成证明（测试只能证明已编码之错误模型未违反自己）",
]


def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, cwd=B,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "?"


def census_numbers():
    """从普查册**读回**数字，不重算——避免交接包与证据册各说各话。"""
    p = os.path.join(B, "evidence", "审计全集普查与分母修复_126B.md")
    if not os.path.exists(p):
        return None
    rows, final = [], []
    for ln in open(p, encoding="utf-8"):
        s = ln.strip()
        if s.startswith("| 闸") and "issue_found" in s:
            continue
        if s.startswith("| 闸") and s.count("|") >= 6:
            rows.append(s)
        if s.startswith("| `survives`") or s.startswith("| `downgraded`") \
           or s.startswith("| `partially_retracted`") or s.startswith("| `retracted`") \
           or s.startswith("| `unknown_pending_audit`"):
            final.append(s)
    return rows, final


def jcount(rel, key=None):
    p = os.path.join(B, rel)
    if not os.path.exists(p):
        return "?"
    d = json.load(open(p, encoding="utf-8"))
    if key and isinstance(d, dict):
        return len(d.get(key, []))
    if isinstance(d, dict):
        for k in ("passages", "cells", "variables", "rules"):
            if k in d:
                return len(d[k])
        return len(d)
    return len(d)



def draft_status():
    """⭐ 126AJ 立：**工作稿之章节／小节由扫描产出**，⛔ 不手写。

    上级 126AJ 实查：`ST-6` 手写「七节」「第 1／6 章仍未成段」，
    而 126AI 已增 §1.7 ⇒ **与 ST-12 及工作稿本身矛盾**。
    ⇒ 根因是**同一事实写在两处**。本函数把它收到**一处生成**。
    """
    f = os.path.join(B, "reports", "学术报告_工作稿.md")
    if not os.path.isfile(f):
        return None
    t = open(f, encoding="utf-8").read()
    chaps = sorted({int(m.group(1)) for m in re.finditer(r'^# 第 (\d+) 章', t, re.M)})
    secs = sorted({m.group(1) for m in re.finditer(r'^## (\d+\.\d+)', t, re.M)},
                  key=lambda x: [int(y) for y in x.split(".")])
    all6 = [1, 2, 3, 4, 5, 6]
    return {"chapters": chaps, "missing": [c for c in all6 if c not in chaps],
            "sections": secs}


SELF_PATH = "docs/交接包_给上级线.md"


def _worktree_changes():
    """⭐⭐ 126AJ 改（上级指出之**静默失败**）：按 `-z` 记录解析，⛔ 不再用字符串包含过滤。

    ⛔⛔ **原实现之缺陷**（上级原话）：
      「当前用**中文路径字符串**过滤 `git status --porcelain`，但 **Git 可能将中文路径转义**，
       导致**排除自身失败**。应使用 `--porcelain -z` 按记录解析并**精确匹配路径**。」

    ⭐ 实证：`git status --porcelain`（无 `-z`）对非 ASCII 路径会输出
      `"docs/\\344\\272\\244\\346\\216\\245..."` 形态（带引号与八进制转义），
      于是 `"docs/交接包_给上级线.md" in ln` **恒为假** ⇒ 本包**永远排不掉自己**
      ⇒ 横幅**恒亮**，而**无任何报错** —— 这正是**静默失败**。
    ⇒ `-z` 输出**原始字节、NUL 分隔、不转义不加引号**，故可**精确等值比较**。

    ⛔⛔ **126AK 再修（上级故障注入所证）**：
      上级实测「**Git 返回 128、输出为空**」时，本函数**同样返回 `('', 0)`** ——
      ⭐ **与「工作区干净」完全不可分辨** ⇒ **失败被静默改写成成功**。
      ⇒ ⭐ **现行：检查 `returncode`，非 0 即【抛出并使生成器非零退出】**，
        ⛔ **禁止在 git 失败时产出任何「干净」判断**。
      ⚠ 并及：`returncode == 0` 而 stdout 为空，**才**是真正的「干净」。

    ⛔ 返回 `(其余改动之列表文本, 条数)`；⛔ **不判断 HEAD 是哪一批**（见 main 之注）。
    """
    pr = subprocess.run(["git", "status", "--porcelain", "-z"],
                        cwd=B, capture_output=True)
    if pr.returncode != 0:
        # ⛔⛔ 不得降级为「干净」，不得 return ('', 0)，不得吞掉。
        raise SystemExit(
            "⛔⛔ `git status --porcelain -z` 失败（退出码 %d）——**已停，⛔ 不生成交接包**。\n"
            "   ⛔ **失败⛔ 不得表现为「工作区干净」**（126AK 上级故障注入所证）。\n"
            "   stderr: %s"
            % (pr.returncode, pr.stderr.decode("utf-8", "replace").strip()[:400]))
    raw = pr.stdout.decode("utf-8", "surrogateescape")
    recs, i = [], 0
    parts = raw.split("\0")
    while i < len(parts):
        rec = parts[i]
        if not rec:
            i += 1
            continue
        xy, path = rec[:2], rec[3:]
        # ⚠ 重命名／复制之记录后**紧跟一个额外 NUL 段**（原路径）⇒ 须一并吃掉，
        #   否则原路径会被当成下一条记录之状态位，解析整体错位。
        if xy[0] in "RC" or xy[1] in "RC":
            i += 1
        recs.append((xy, path))
        i += 1
    other = [(xy, p) for xy, p in recs if p != SELF_PATH]   # ⭐ 精确等值，⛔ 非包含
    return "\n".join("%s %s" % (xy, p) for xy, p in other), len(other)


def selftest():
    """⭐⭐ 126AK 立（上级令二末句之纪律）：
    **「声称能检查什么」须由【实际注入代表性故障】来证**，⛔ 不得只凭「代码写了」。

    ⛔⛔ **本自测只覆盖 `_worktree_changes()` 之【输入侧】**——
      ⭐ 它**能**验：git 非零退出是否被静默改写成「干净」｜本包自身是否被正确排除｜
        `R`/`C` 记录之额外原路径段是否被吃掉。
      ⛔ 它**不能**验：横幅措辞是否恰当｜正文数字是否正确｜账本内容是否为真
        ｜git 本身是否报了正确的状态。⇒ **未覆盖之失效如实保留。**
    """
    real = subprocess.run

    def mk(rc, out=b"", err=b""):
        class R:
            returncode, stdout, stderr = rc, out, err
        return R()

    cases = [
        # (名, 假 git 结果, 期望)　期望为 "raise" 或 (文本, 条数)
        ("git 退出 128、stdout 空", mk(128, b"", b"fatal: not a git repository"), "raise"),
        ("git 退出 1、stdout 空", mk(1, b"", b"error"), "raise"),
        ("git 退出 0、stdout 空（真·干净）", mk(0, b"", b""), ("", 0)),
        ("只有本包自身", mk(0, (" M %s\0" % SELF_PATH).encode()), ("", 0)),
        ("本包 ＋ 另一件", mk(0, (" M %s\0 M tools/x.py\0" % SELF_PATH).encode()), (" M tools/x.py", 1)),
        ("重命名记录（R 带额外原路径段）",
         mk(0, "R  docs/新.md\0docs/旧.md\0 M tools/y.py\0".encode()),
         ("R  docs/新.md\n M tools/y.py", 2)),
    ]
    bad = 0
    print("═══ `_worktree_changes()` 故障注入自测 ═══")
    for name, r, want in cases:
        subprocess.run = (lambda R: (lambda *a, **k: R if (
            a and isinstance(a[0], list) and a[0][:2] == ["git", "status"]) else real(*a, **k)))(r)
        try:
            got = _worktree_changes()
            ok = (want != "raise" and got == want)
            print("  %s %-30s ⇒ %r" % ("✅" if ok else "⛔", name, got))
        except SystemExit:
            ok = (want == "raise")
            print("  %s %-30s ⇒ 抛出 SystemExit（⛔ 未产出「干净」）" % ("✅" if ok else "⛔", name))
        finally:
            subprocess.run = real
        if not ok:
            bad += 1
    print("\n%s" % ("✅ 全部符合预期。" if not bad else "⛔⛔ %d 项不符 ⇒ 修复未生效。" % bad))
    print("⛔⛔ **本自测只覆盖输入侧**（见 docstring）——⛔ 横幅措辞、正文数字、账本内容**皆不在覆盖内**。")
    return 1 if bad else 0


def main():
    head = sh("git rev-parse --short HEAD")
    branch = sh("git rev-parse --abbrev-ref HEAD")
    # ⛔⛔ 126AI 曾在此「排除本包自身之路径」—— ⭐ **126AJ 实测：那个排除从未生效**
    #     （中文路径被 porcelain 转义，`in` 恒假）⇒ 见 `_worktree_changes` 之说明。
    dirty, dirty_n = _worktree_changes()
    raw = "https://raw.githubusercontent.com/%s/%s" % (REPO, branch)

    L = []
    w = L.append
    w("# 交接包 · 给上级线（自动生成，勿手改）\n")
    # ⛔⛔ 126AI 修（上级实查所指）：本包此前**在 commit 之前生成**，
    #     于是「HEAD」记的是【上一批】，而包里的内容是【本批】——
    #     前后不一致，且**看不出来**。⇒ 不是显示问题，是**生成时机**问题。
    #     现在：脏工作区时在**最前面**打横幅，并把 HEAD 一行改写成明确的「不含本包内容」。
    # ⛔⛔ 126AJ 改（上级指出）：「**工作区有改动**」⛔ **不等于**「**HEAD 是上一批**」——
    #     前者是本工具能观测的事实，后者是**推论**，且在「先提交内容再重跑」的流程下**为假**。
    #     ⇒ 本工具只报**两件可观测的事**，⛔ 不再宣称 HEAD 属于哪一批：
    #       ① 本包所描述之内容，落在 `HEAD`（= 已提交的那一份）；
    #       ② 生成时工作区另有 N 项未提交改动（逐项列出）——**它们不在 ① 内**。
    # ⛔ 并依上级：**不必要求交接包记载自己的最终哈希** ⇒ 126AI 之「两次提交」判据**撤销**。
    # ⛔⛔ 126AK 改（上级指出）：本工具之正文（账本、索引、工作稿、standing_tasks）
    #     **全部读自【工作区文件】**，⛔ 不是从 HEAD 检出的 —— 故工作区一有改动，
    #     「本包所述 ＝ HEAD 快照」**即为假**。⇒ 只在确证干净时才可这么说。
    if dirty:
        w("> ⛔⛔ **本包之正文读自【工作区文件】，⛔ 非 `HEAD` 之检出** ——")
        w("> 而**生成时工作区有 %d 项未提交改动**，⇒ ⛔ **本包所述⛔ 不是 `HEAD` 之快照**，" % dirty_n)
        w("> 而是**「`HEAD` ＋ 下列未提交改动」之混合**。⛔ 引用本包任何数字前须先看这一条。")
    else:
        w("> ⭐ **生成时工作区干净**（⛔ 本包自身之改动不计）⇒ **本包正文所述 ＝ 下表之 `HEAD`**。")
    if dirty:
        w("> ⚠⚠ **未提交改动逐项**（⛔ 已在 `HEAD` 之外，⭐ 但已被本包正文读入）：\n")
        w("> ```")
        for ln in dirty.splitlines():
            w("> " + ln)
        w("> ```")
        w("> ⇒ ⭐ **须 `git commit` 后重跑本工具**，使「正文所读」与「`HEAD`」合一。")
        w("> ⛔⛔ **本工具⛔ 不判断 `HEAD` 属于哪一批** —— 「工作区有改动」⛔ 不蕴含「HEAD 是上一批」"
          "（⭐ **上级 126AJ 指出**：126AI 之横幅把这两件事混为一谈）。\n")
    else:
        w("> ✅ **生成时工作区无其他未提交改动。**\n")
    w("> ⛔ 本册由 `python3 tools/handoff_pack.py` 从仓库**确定性生成**。")
    w("> 手工转述会丢限定词——「C卷同族」硬化成断言、「63组」变成幽灵，都是这么来的。")
    w("> **凡本册与任何报告叙述冲突，以本册与其所指向之原文为准。**\n")

    # ⛔ 上级 126S 令：把「最终交付完整学术报告」写入交接说明。
    #    ⭐ 放在最前，因为它决定其余各节的性质——其余各节全是**过程**。
    w("## ⭐⭐⭐ 最终交付\n")
    w("**本工程之最终交付是完整的《胡希恕辨证论治体系重构》学术报告。**\n")
    w("⛔ 通读、取证、Code 审计、批次报告，**都是过程，不能取代这个目标**。（上级 126S 令）\n")
    w("| 项 | 位置 |")
    w("|---|---|")
    w("| **报告主线索引**（按研究问题组织，非按批次拼接） | `reports/学术报告_主线索引.md` |")
    w("| 其源（勿手改；由 `tools/report_index.py` 生成并自检） | `rules/report_index_v0.json` |")
    w("| 研究纲领（含附编一、附编二） | `evidence/研究纲领_v0_126H.md` |")
    ri = os.path.join(B, "rules", "report_index_v0.json")
    if os.path.exists(ri):
        d = json.load(open(ri, encoding="utf-8"))
        w("")
        w("**章目与条目状态**（版本 `%s`）：\n" % d["version"])
        w("| 章 | 研究问题 | 条目 | 现行 | 部分 | 未决 |")
        w("|---|---|---:|---:|---:|---:|")
        for ch in d["chapters"]:
            es = ch["entries"]
            c = lambda st: sum(1 for e in es if e["status"] == st)
            w("| **%d %s** | %s | %d | %d | %d | %d |"
              % (ch["no"], ch["title"], ch["question"], len(es),
                 c("current"), c("partial"), c("open")))
        w("")
        w("⛔ **已撤回之判断保留于索引 `R-02`，不得继续作为现行结论被引用。**")
        w("⛔ `report_position` 只是**拟入位置**，⛔ 正文结论**未冻结**。\n")

    # ⛔ 上级 126W 令一：交接包须含「持续任务及状态」。
    #    ⭐ 放在最终交付之后、取原文之前——因为它决定**每批该做什么**。
    st = os.path.join(B, "rules", "standing_tasks_v0.json")
    if os.path.exists(st):
        sd = json.load(open(st, encoding="utf-8"))
        # ⛔⛔ 上级 126X 令一·1：**断点须从阅读账本生成**，⛔ 不得在台账里另抄一份
        #    ——「交接包不能同时提供两个现行状态」。126W 之 ST-1 即因手抄而落后一批。
        led = os.path.join(B, "evidence", "顺序首读账本.json")
        # ⛔⛔ 上级 126Y 令四：**缺失账本应明确报错**，⛔ 不得静默跳过而留下一份
        #    看起来完整、实则没有持续状态的交接包。
        if not os.path.exists(led):
            raise SystemExit("⛔ 阅读账本缺失（%s）——交接包之持续状态无从生成，已停。" % led)
        if True:
            # ⛔ 变量名不得用 `L`——本文件之输出缓冲即 `L`。
            #    126X 初稿曾写 `L = json.load(...)`，把输出缓冲替换成了账本 dict，
            #    结果 `"\n".join(L)` 迭代出 dict 的键，生成了一份**只有 7 行、
            #    内容是 JSON 键名**的交接包——⭐ 而脚本仍打印「已写」。
            #    ⇒ 这是一次**静默产出错误**：无异常、无红项、文件存在。
            LED = json.load(open(led, encoding="utf-8"))
            # ⛔⛔ 126BP 订正（上级实查所指）：此前硬编码书名「讲伤寒」，
            #    该书 100% 读完后 next_offset=395556／next_unit_title=None 仍被当作
            #    当前断点续读——生成了「从395556、None续读」这种失真的交接包，
            #    实际断点早已转移到下一本（讲金匮）。⇒ **续读断点须取 QUEUE 中
            #    第一本未读完的书**，⛔ 不得固定指向某一本书名。
            import corpus_guard as _CG
            import reading_ledger as _RL  # QUEUE 定义执行顺序，⛔ 非 BASELINE 之字典序
            _active_name = None
            for _n in _RL.QUEUE:
                _o = LED["books"].get(_n, {}).get("next_offset", 0)
                if _o < _CG.BASELINE[_n]:
                    _active_name = _n
                    break
            if _active_name is None:
                _active_name = list(LED["books"].keys())[-1] if LED["books"] else "讲伤寒"
            bk = LED["books"].get(_active_name, {"next_offset": 0, "next_unit_title": None,
                                                   "src": {"cleaned_len": _CG.BASELINE.get(_active_name, 0)}})
            tot = bk["src"]["cleaned_len"]
            off = bk["next_offset"]
            # ⚠ 账本之 books 只含已开读之书；十二书总字数取自 corpus_guard 之冻结基线
            allbooks = sum(_CG.BASELINE.values())
            allread = sum(b.get("next_offset", 0) for b in LED["books"].values())
            # ⛔⛔ 上级 126Y 令四：**逐书状态同样由账本生成**。
            #    原文硬编码「其余十一书 0%」——现虽合账本，⛔ 第二本开读后就会**静默失真**。
            per = []
            for name, base in _CG.BASELINE.items():
                o = LED["books"].get(name, {}).get("next_offset", 0)
                if o:
                    per.append("%s `[0,%d)` ＝ **%.3f%%**" % (name, o, 100.0 * o / base))
            unread = [n for n in _CG.BASELINE if not LED["books"].get(n, {}).get("next_offset", 0)]
            tail = ("；**未开读 %d 本**（%s）" % (len(unread), "、".join(unread))
                    if unread else "；**十二书皆已开读**")
            live = ("%s；十二书合计 %.4f%%%s。B 档定向 %d 次。⭐ **本行由账本生成**"
                    % ("｜".join(per), 100.0 * allread / allbooks, tail,
                       LED.get("topical_reads", 0)))
            nxt = "从 **%d、%s** 续读。⭐ **本行由账本生成**" % (off, bk.get("next_unit_title", "?"))
            for t in sd["tasks"]:
                if t["id"] == "ST-1":
                    t["current_result"] = live
                    t["next_action"] = nxt
        w("## ⭐⭐ 持续任务及状态（版本 `%s`）\n" % sd["version"])
        w("⛔⛔ **最新批次指令不是全部任务清单。**")
        w("**最新指令只改变其中的优先级或内容；没有明确撤销的任务继续有效。**")
        w("⛔ **本批未安排不等于取消，研究取舍也不叫阻塞。**\n")
        w("| # | 任务 | 当前结果 | 下一动作 | 真实阻塞 | 优先级 |")
        w("|---|---|---|---|---|---|")
        for t in sd["tasks"]:
            w("| `%s` | **%s** | %s | %s | %s | %s |"
              % (t["id"], t["name"], t["current_result"], t["next_action"],
                 t["real_blocker"], t["priority"]))
        w("")
        w("⇒ 对应文件见 `rules/standing_tasks_v0.json`。\n")

    w("## 〇、怎么直接取原文（不必再复制粘贴）\n")
    w("本仓库为 **public**（实测 `private=false`）。以下两条路任一可通：\n")
    w("1. **网页抓取**：下列 raw 链接是**纯文本**，任何能联网抓取的对话都可直接取。")
    w("   ⚠ 「代码沙箱无网络」与「对话能否抓网页」是两件事——前者关闭不表示后者关闭，**请先试一次**。")
    w("2. **Claude Code on the web**（claude.ai/code）开一个本仓库的会话，可直接读文件，")
    w("   无需任何粘贴。\n")
    w("```")
    w("仓库    https://github.com/%s" % REPO)
    w("分支    %s" % branch)
    w("raw 前缀 %s/<路径>" % raw)
    w("```\n")

    w("## 一、开工报账\n")
    w("| 项 | 值 |")
    w("|---|---|")
    # ⛔⛔ 126AK 删（上级指出）：此处仍留着「**上一批之 HEAD**」这一**已撤销之推断**
    #     —— 126AJ 只改了上方横幅而**漏改了本行** ⇒ 同一份包内两种口径并存。
    #     ⭐ 现行：本行**只报 HEAD 本身**，是否与正文一致由上方横幅说。
    w("| HEAD | `%s` |" % head)
    w("| 分支 | `%s` |" % branch)
    ds = draft_status()
    if ds:
        w("")
        w("## ⭐ 学术报告工作稿之**标题扫描**（⛔ 只报检出，⛔ 非验收）\n")
        # ⛔⛔ 126AK 改（上级指出）：扫到标题**只能报「检出章节标题」** ——
        #     ⭐ **正文存在／论证完成／学术验收是三种不同状态**，⛔ 本扫描只及第一种。
        w("| 项 | 值 |")
        w("|---|---|")
        w("| **检出章节标题** | %s |" % "、".join("第%d章" % c for c in ds["chapters"]))
        w("| **未检出章节标题** | %s |" % ("、".join("第%d章" % c for c in ds["missing"]) or "无"))
        w("| 小节数 | **%d** |" % len(ds["sections"]))
        w("| 小节 | %s |" % "｜".join("§" + x for x in ds["sections"]))
        w("")
        w("⛔ **此表由 `handoff_pack.draft_status()` 扫描 `reports/学术报告_工作稿.md` 之标题行生成**——")
        w("⛔ 凡 `standing_tasks` 内再手写章节数者，**以本表为准**（126AJ 上级令二）。")
        w("")
        w("⛔⛔ **本表能说与不能说**（126AK 上级令二）：")
        w("| 状态 | 本表 |")
        w("|---|---|")
        w("| **标题行存在** | ✅ **本表所报者即此** |")
        w("| **正文存在／有实质内容** | ⛔ **本表不报** |")
        w("| **论证完成** | ⛔ **本表不报** |")
        w("| **学术验收通过** | ⛔ **本表不报** |")
        w("⇒ ⛔ **「检出章节标题」⛔ 不得改写为「已成段」「已完成」「已交付」。**\n")
    w("| 工作区 | %s |" % ("⚠ **有 %d 项未提交改动**（⛔ 已排除本包自身；⭐ 已被本包正文读入）" % dirty_n
                          if dirty else "干净（⛔ 本包自身之改动不计）"))
    w("| 冻结件 | `V8/`／`rules/core_v0.json`／`runtime/`——126批起冻结，diff 须为 0 |")
    w("")

    w("## 二、现行裁决状态（读自普查册，非重算）\n")
    cn = census_numbers()
    if cn:
        rows, final = cn
        w("| 闸 | issue_found | eligible 分母 | 比率 | 无锚 | n/a | unknown |")
        w("|---|---|---|---|---|---|---|")
        for r in rows:
            w(r)
        w("")
        w("| 对象级裁决 | 数 |")
        w("|---|---|")
        for f in final:
            w("|".join(f.split("|")[:3]) + "|")
    else:
        w("⛔ 普查册缺失——先跑 `python3 tools/audit_population_census.py`。")
    w("")
    w("⛔ **分母纪律**：每闸各自算；`not_applicable`／无锚**不进分母**；`unknown`**不进分子**。")
    w("⛔ **对象级只可**：`survives`／`downgraded`／`partially_retracted`／`retracted`／`unknown_pending_audit`；同一对象不得重复计数。\n")

    w("## 三、十二书说话主体（卷首实查，非推定）\n")
    w("| 书 | speaker_status | 可用归因 |")
    w("|---|---|---|")
    for b, s, u in SPEAKER:
        w("| %s | `%s` | %s |" % (b, s, u))
    w("")

    w("## 四、硬约束（违反即不得入库）\n")
    w("```")
    for h in HARD:
        w(h)
    w("```\n")

    w("## 五、现行资产计数\n")
    w("| 件 | 条目 |")
    w("|---|---|")
    w("| `rules/text_critical_v0.json` | %s |" % jcount("rules/text_critical_v0.json"))
    w("| `rules/pulse_cells_v0.json` | %s |" % jcount("rules/pulse_cells_v0.json"))
    w("| `rules/state_variables_v0.json` | %s |" % jcount("rules/state_variables_v0.json"))
    w("| `tests/` | %s |" % len([f for f in os.listdir(os.path.join(B, "tests"))
                                 if f.startswith("test_") and f.endswith(".py")]))
    w("")

    w("## 六、可自取之关键资产\n")
    w("| 资产 | 是什么 | raw |")
    w("|---|---|---|")
    for rel, what in KEY_ASSETS:
        ok = "" if os.path.exists(os.path.join(B, rel)) else " ⛔缺"
        w("| `%s`%s | %s | %s/%s |" % (rel, ok, what, raw, rel))
    w("")

    w("## 七、⛔ 已知为【幽灵】者——请勿据以布置任务\n")
    w("| 名 | 实情 |")
    w("|---|---|")
    w("| 「63 组机器候选」 | ⛔ **不存在**。曾被五份报告引用，仓库内枚举不出 ⇒ 记 `PHANTOM-63FLIP` |")
    w("| 「28 条 `validation=candidate`」 | ⛔ 现行 `rules/*.json` 中 `candidate` 为 **0** 条；出自 119–120批叙述，从未落为带 ID 之资产 |")
    w("")
    w("⛔ **常设**：凡报告中称引之对象集合，须能在 repository 中被枚举出来；")
    w("枚举不出者记 `population_gap`，**不得作为待办计数**——不制造不存在的债务。\n")

    # ⛔⛔ 126X 产出健全性闸：本册正常在 100 行以上。
    #    ⚠ 126X 曾因变量名冲突产出一份 7 行之废件而脚本仍打印「已写」
    #    ⇒ **静默产出错误**。此闸只挡最粗的一类，⛔ 不保证内容正确。
    if not isinstance(L, list):
        raise SystemExit("⛔ 输出缓冲被覆盖（类型 %s）——检查是否有变量名冲突" % type(L).__name__)
    # ⛔⛔ 上级 126Y 令四：**行数检查只能辅助**；核心须查
    #    「必要任务、断点及来源是否存在且一致」。
    body = "\n".join(L)
    must = {
        "持续任务台账": "持续任务及状态",
        "最终交付": "最终交付",
        "断点": "由账本生成",
        "冻结件": "冻结件",
    }
    missing = [k for k, v in must.items() if v not in body]
    if missing:
        raise SystemExit("⛔ 交接包缺必要节：%s——已停" % "、".join(missing))
    # 断点一致性：正文所报之偏移须与账本一致
    # ⚠ 126BP：取 QUEUE 中第一本未读完的书作校验对象，⛔ 不再硬编码「讲伤寒」
    #    （该书读完后 next_offset 固定在书末，不再是「当前断点」）。
    import corpus_guard as _CG2
    import reading_ledger as _RL2
    _led = json.load(open(os.path.join(B, "evidence", "顺序首读账本.json"), encoding="utf-8"))
    _active = None
    for _n in _RL2.QUEUE:
        _o = _led["books"].get(_n, {}).get("next_offset", 0)
        if _o < _CG2.BASELINE[_n]:
            _active = _n
            break
    _off = _led["books"][_active]["next_offset"] if _active else _led["books"]["讲伤寒"]["next_offset"]
    if ("[0,%d)" % _off) not in body:
        raise SystemExit("⛔ 交接包所报断点与账本不一致（账本 next_offset=%d，当前本 %s）——已停" % (_off, _active))
    # 来源存在性：台账所指之文件须真的在仓库里
    _st = json.load(open(os.path.join(B, "rules", "standing_tasks_v0.json"), encoding="utf-8"))
    import glob as _g
    _bad = []
    for t in _st["tasks"]:
        for f in t.get("files", []):
            if not _g.glob(os.path.join(B, f)):
                _bad.append("%s → %s" % (t["id"], f))
    if _bad:
        raise SystemExit("⛔ 台账所指之来源不存在：%s——已停" % "；".join(_bad))
    if len(L) < 60:
        raise SystemExit("⛔ 交接包只有 %d 行，远少于常态（≥60）——⚠ 此为**辅助**检查" % len(L))
    txt = "\n".join(L) + "\n"
    if "--stdout" in sys.argv:
        print(txt)
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(txt)
    print("已写 %s（%d 行）" % (OUT, txt.count("\n")))
    print("⇒ 把它整份粘给上级线，或直接给对方这一条：")
    print("   %s/docs/交接包_给上级线.md" % raw)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
