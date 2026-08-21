#!/usr/bin/env python3
"""【外部仓库·纯净性扫描 ＋ 双向缺口对比】（㊾批·指令三）。

上级㊾批：克隆 `jangviktor-web/huxishu` 与 `tcmzhou/TCM`，**用途仅三**：
  ①缺口双向对比 ②组织形态参考 ③对照基准。
  **全部标 [他人C级]，规则一律不入引擎；须先做纯净性扫描。**

本工具做三件事，**全部只出报表，一个字不写进引擎**：
  ① **纯净性扫描**：按 R1 闭卷禁区词表（温病/卫气营血/三焦辨证/脏腑辨证结论/五运六气/
     倪海厦五行等）逐库统计命中，**判定该库可否作对照基准**；
  ② **双向缺口对比**：他有我无 ／ 我有他无——**两个方向都必须报**
     （只报"他有我无"会变成单向抄袭清单，只报"我有他无"会变成自我安慰）；
  ③ **语料重合与 OCR 质量对比**：其讲稿与我方 `ocr_未识别2.txt`(讲伤寒) 是否同一底本，
     **我方已知 OCR 损坏处在对方是否完好**——这一项关系到「四次缺口中三次是工具」那条账。

⚠**本工具不判断对方内容对不对**（那需要读原文，且属 R1 禁区外的他人体系时更无从判起）。
  它只回答**结构性问题**：有没有、覆盖多少、干不干净、能不能当尺子。

【已知失效模式】(视角㉕)
  ① **纯净性靠关键词**。对方若用别的措辞讲同一个外部体系，**漏检**；
     反之胡老本人也偶用"肝郁"一类字样（case_purity KEEP 之例），**会误报**。
     → 故一律输出「命中**候选**」＋所在文件，**判定须人读**，不自动定性。
  ② **条文号覆盖**靠「第N条」正则。对方用「398 条」编号体系而我方按条文内容挂载，
     **两边可比性有限**——故只报**量级**，不作精确差集断言。
  ③ **OCR 质量对比取我方已知损坏样本**（小柴朐/茨苓/麻杏惧甘…），
     **该样本是人工列的，必然不全**（R41⑪：词表未命中一律不得读作"不存在"）。
  ④ **无法判定对方讲稿之来源真伪**——它可能是真转录，也可能是模型重写。
     本工具**只测文本相似度，不作真伪断言**；**真伪须人读并另行取证**。
【弃件条件】仓库中非文本文件（图片/二进制）一律跳过。
【口径】(视角㊱) 一处＝一个文件内一次命中；`python3 tools/ext_repo_scan.py <外部仓库目录…>`
"""
import re, os, sys, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── R1 闭卷禁区（沿用 case_purity.EXT，并补五运六气/倪氏五行）────────────
EXT = {
 "卫气营血": r"卫分|气分|营分|血分|卫气营血",
 "三焦辨证": r"上焦(?:湿|证|病)|中焦(?:湿|证|病)|下焦(?:湿|证|病)|三焦辨证",
 "温病学说": r"温病|湿温|春温|暑温|伏邪|伏暑|透热转气|凉营|清营|银翘|桑菊",
 "脏腑辨证结论": r"肝郁|肝火|肝阳上亢|肝肾阴虚|脾虚|脾胃虚弱|脾失健运|肾阳虚|肾阴虚|"
                r"心血不足|心脾两虚|肺气虚|肝血虚|气滞血瘀",
 "五运六气": r"运气|五运|司天|在泉|六气",
 "五行生克": r"五行|生克|相生相克|木克土|培土生金",
}
TXT = (".md", ".txt", ".json", ".yaml", ".yml", ".html", ".go", ".py")


def files(root):
    for dp, dn, fn in os.walk(root):
        if ".git" in dp: continue
        for f in fn:
            if f.lower().endswith(TXT):
                yield os.path.join(dp, f)


def load(p):
    try: return open(p, encoding="utf-8", errors="ignore").read()
    except Exception: return ""


# ── 我方口径 ──────────────────────────────────────────────────────
ENG = open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read()
MY_FANG_RAW = set(re.findall(r"【([一-鿿]{2,14}(?:汤|散|丸|饮|煎))", ENG))
MY_TIAO = set(re.findall(r"§(\d{1,3})", ENG))
FANG_RX = re.compile(r"([一-鿿]{2,16}(?:汤|散|丸))")
# ⚠**首跑事故·本工具自查**：直接用 FANG_RX 抽对方方名，得「他有我无 1529 个」，
#   而其中「用桂枝汤／就是桂枝汤／这个附子汤／梦远行而精神离散」全是**前缀粘连**——
#   与㊹批「方证断点 136 例全部机械可修」**同型第五次**。
#   → **凡"缺口"数出具前须先剥前缀**（㊹批闸门：缺口须先排除是不是自己的抽取器不够）。
LEAD = re.compile(r"^(?:宜|用|与|予|服|投|拟|方用|治以|治宜|就是|这个|那个|所以|当以|"
                  r"再与|改与|故与|即与|乃与|先与|后与|仍宜|据证与|一个|个|的|了|是)+")
# ⚠**第四次自查·异体字**：对方作「枳朮汤／桂枝加黄耆汤」，我方作「枳术汤／桂枝加黄芪汤」
#   ——**朮/术、耆/芪、藭/芎 是异体字**，不归一即两边互报为缺口，**两个方向同时虚高**。
VAR = str.maketrans("朮耆藭薑蔞蒌栝萋", "术芪芎姜蒌蒌栝蒌")
def vnorm(x): return x.translate(VAR)
def norm_fang(f):
    f = LEAD.sub("", f)
    return vnorm(f) if len(f) >= 3 else ""
TIAO_RX = re.compile(r"(?:伤寒论)?第\s*(\d{1,3})\s*条")

# 我方已知 OCR 损坏样本（R41⑪：此表必然不全，未命中不得读作"对方也没有"）
OCR_BAD = ["小柴朐", "茨苓", "麻杏惧甘", "小标胡", "大柏胡", "麻杳石甘", "莞苓饮",
           "桂校二越婢一", "庭陈", "泽沼", "生娆", "茉胡"]
OCR_GOOD = ["小柴胡", "茯苓", "麻杏甘", "小柴胡", "大柴胡", "麻杏石甘", "茯苓饮",
            "桂枝二越婢一", "茵陈", "泽泻", "生姜", "柴胡"]

MY_FANG = {vnorm(x) for x in MY_FANG_RAW}

roots = sys.argv[1:]
if not roots:
    sys.exit("用法：python3 tools/ext_repo_scan.py <外部仓库目录…>")

L = ["# 外部仓库·纯净性扫描与双向缺口对比（㊾批·指令三）", "",
     "> ⛔**全部标 [他人C级]，永不升 A。规则一律不入引擎（R1 闭卷）。**",
     "> 本表**只出结构性判断**（有没有／多少／干不干净／能不能当尺子），**不判内容对错**。", ""]

for root in roots:
    name = os.path.basename(root.rstrip("/"))
    fl = list(files(root))
    total = 0
    hits = defaultdict(Counter)
    fangs, tiaos = Counter(), set()
    corpus = []
    for p in fl:
        t = load(p)
        total += len(re.sub(r"\s+", "", t))
        rel = os.path.relpath(p, root)
        for k, rx in EXT.items():
            n = len(re.findall(rx, t))
            if n: hits[k][rel] = n
        fangs.update(x for x in map(norm_fang, FANG_RX.findall(t)) if x)
        tiaos |= set(TIAO_RX.findall(t))
        if len(t) > 50000: corpus.append((rel, t))

    L += ["", "═" * 60, "## 仓库 `%s`" % name, "",
          "**规模**：%d 个文本文件／**%d 字**。" % (len(fl), total), ""]

    # ── ① 纯净性 ──
    L += ["### ① 纯净性扫描（R1 闭卷禁区）", "", "| 禁区体系 | 命中数 | 主要文件 |", "|---|---|---|"]
    dirty = 0
    for k in EXT:
        n = sum(hits[k].values()); dirty += n
        top = "／".join("%s(%d)" % (f, c) for f, c in hits[k].most_common(2)) or "—"
        L.append("| %s | **%d** | %s |" % (k, n, top))
    L += ["", "**禁区词合计 %d 处**（每万字 %.1f 处）。" % (dirty, 10000 * dirty / max(total, 1)), ""]

    # ── ② 双向缺口 ──────────────────────────────────────────────
    # ⚠**第三次自查·剥前缀仍不够**：对方是**口语转录**，粘连前缀是任意口语
    #   （「那么小青龙汤」「她这个例假啊吃抵当汤」「附就叫六味地黄丸」），
    #   **负向剥离原理上补不全**（cvol_rebuild 之教训：**界定对象须用正向判据**）。
    # → 改**正向识别**：凡候选中**含有我方任一在库方名作子串**者，即判为「我方已有」，
    #   **不计入缺口**。残余才是候选，且一律标 `[候选·须人读]`，**不作缺口断言**。
    allraw = vnorm("".join(load(p) for p in fl))
    theirs = {f for f, c in fangs.items() if c >= 2}
    only_them = sorted({f for f in theirs if not any(m in f for m in MY_FANG)},
                       key=lambda x: -fangs[x])
    # 我有他无：在对方**全文**中做子串检索（比集合差集准确得多）
    only_me = sorted(m for m in MY_FANG if m not in allraw)
    L += ["### ② 双向缺口对比（**两个方向都报**）", "",
          "| 方向 | 数量 | 例（前20） |", "|---|---|---|",
          "| **他有我无**·方名`[候选·须人读]` | %d | %s |"
          % (len(only_them), "／".join(only_them[:20]) or "—"),
          "| **我有他无**·方名（对方全文无此串） | %d | %s |"
          % (len(only_me), "／".join(only_me[:20]) or "—"),
          "| 条文号覆盖 | 他 %d 条／我 %d 条 | （编号体系不同，**只作量级参照**） |"
          % (len(tiaos), len(MY_TIAO)), "",
          "⚠**「他有我无」一栏在口语转录上原理不可靠**：粘连前缀是任意口语，",
          "  **正则补不全**（本工具三次自查所得）。**该栏只作线索，不得作缺口清单。**", ""]

    # ── ③ 语料重合与 OCR 质量 ──
    L += ["### ③ 语料重合与 OCR 质量对比", ""]
    if corpus:
        my = open(os.path.join(B, "sources", "ocr_未识别2.txt"), encoding="utf-8", errors="ignore").read()
        my = re.sub(r"\s+", "", my)
        probe = [my[i:i + 14] for i in range(2000, min(len(my), 200000), 4000)]
        big = "".join(re.sub(r"\s+", "", t) for _, t in corpus)
        same = sum(1 for s in probe if s in big)
        # ⚠**精确串探针有一个致命混淆**（本工具第二次自查）：
        #   **我方语料自身满是 OCR 错字**，故 14 字精确串**即使同底本也必然对不上**。
        #   → 精确串低命中**不能证明不同底本**。补 **2-gram Jaccard**（对稀疏错字鲁棒）。
        def g2(x): return {x[i:i+2] for i in range(len(x)-1)}
        ga, gb = g2(my[:200000]), g2(big[:200000])
        jac = len(ga & gb) / len(ga | gb)
        cov = len(ga & gb) / len(ga)          # 我方 2-gram 被对方覆盖之比例
        L += ["- **底本重合·精确串**：我方《讲伤寒》取 %d 个 14 字串，对方命中 **%d 个（%.0f%%）**。"
              % (len(probe), same, 100 * same / max(len(probe), 1)),
              "  ⚠**此数被我方自身 OCR 错字污染，低命中不能证明不同底本**（本工具自查所得）。",
              "- **底本重合·2-gram**（对稀疏错字鲁棒）：Jaccard **%.2f**／"
              "我方 2-gram 被对方覆盖 **%.0f%%**。" % (jac, 100 * cov),
              "  - 覆盖高而精确串低 ⇒ **同一题材同一语言，但非逐字同底本**（改写或另一转录）。",
              "  - **无论哪种，均不足以断言真伪**（失效模式④）——**须人读比对**。", ""]
        L += ["| 我方已知 OCR 损坏 | 对方是否有正确写法 |", "|---|---|"]
        for bad, good in zip(OCR_BAD, OCR_GOOD):
            L.append("| %s（我方误字） | %s |" % (bad, "**有 `%s`**" % good if good in big else "无"))
        L += ["", "⚠**此表按 R41⑪ 读**：「无」只表示**本词表未在对方命中**，"
              "**不得读作「对方没有」**。", ""]
    else:
        L += ["- 本库**无大文本文件**（>50KB），**不存在可作校本的语料**。", ""]

    # ── 裁定 ──
    L += ["### ⛔ 本库之裁定（三用途逐项判）", ""]
    L += ["| 用途 | 可否 | 理由 |", "|---|---|---|"]
    # ⚠**机械裁定之假阳**（本工具首跑自查）：仅按「字数＋方名数」判，
    #   会把**网盘资源索引**判成知识库——其方名全部来自**书名/视频名清单**。
    #   → 补**资源索引检测器**：网盘/提取码/加微信/媒体文件清单之特征密度。
    IDX = len(re.findall(r"访问密码|提取码|加微信|扫码|网盘|\.mp4|\.mp3|\.pdf\s|\.epub|"
                         r"\d+[MG]\b|下载", "".join(load(p) for p in fl)))
    is_index = IDX > 500 and len(tiaos) < 20
    usable = total > 100000 and len(theirs) > 20 and not is_index
    L += ["**[资源索引检测]** 网盘/提取码/媒体清单特征 **%d 处**；条文号 %d 个 → "
          "判为 **%s**。" % (IDX, len(tiaos),
          "⛔**资源索引，非知识库**（其「方名」来自书名清单，不是知识）" if is_index else "知识文本"), ""]
    L += ["| ①缺口双向对比 | %s | %s |" % ("**可**" if usable else "⛔**不可**",
          "有 %d 方名、%d 条文号可比" % (len(theirs), len(tiaos)) if usable
          else "**无知识内容**，方名 %d／条文号 %d，不成其为知识库" % (len(theirs), len(tiaos))),
          "| ②组织形态参考 | %s | %s |" % ("**可**" if len(fl) > 5 and usable else "⛔**不可**",
          "有 SKILL/modules/references 分层可参考" if usable else "**无结构**，为资源清单"),
          "| ③对照基准 | %s | %s |" % ("**待判**" if usable else "⛔**不可**",
          "须先解决「其讲稿来源真伪」（失效模式④）" if usable else "**无内容可对照**"), ""]

open(os.path.join(B, "term_layer", "外部仓库_纯净性与双向缺口.md"), "w").write("\n".join(L))
print("\n".join(L))
print("\n→ term_layer/外部仓库_纯净性与双向缺口.md")
