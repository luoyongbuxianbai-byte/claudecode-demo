#!/usr/bin/env python3
"""【胡希恕原词—方证结构库】全量取证器（L0原文 → L1原词 → L2原文明确关系）。

纪律（上级冻结指令 1-9）：
  只收原词原句｜保留出处与上下文｜不判类别｜不建轴｜同义词不合并｜
  关系只在原文明确表达时建｜方剂只在实案/条文支持时建｜无证据留空｜
  禁止据统计未共现创造「禁止关系」｜禁止据形式组合补格。

【已知失效模式】(视角㉕)
  ① 定义句靠句式捕获（"X，指…"/"X，即…"/"X…之谓也"/"X就是…"）。
     胡老不用这些句式而在长段落中隐含定义者，**一律漏检**，不做推测补全。
  ② 关系句只收**同句内**的「原词 … 治法/方」共现，跨句因果**不收**——
     跨句需要理解，那是 L3 的事，本工具只做 L2。
  ③ 出处标到源文件行号；C卷已知有 PDF 页脚噪声，已剔，其余书未剔。
  ④ 一词多义**不合并**：同一原词的每次出现各占一行，上下文各自保留。
     故本库**行数 > 词数**是设计，不是重复。
  ⑤ 证据等级：A=条文或胡老注解原文；B=胡老医案实际使用；C=序言/他人转述。
     **本工具只能机械区分 A/B（按所在段落是否含【验案】），C 需人工标**。
【弃件条件】
  定义主词长度 >8 字、或含标点者弃（多为断句错误）；定义体 <4 字弃。
【口径】(视角㊱) 一条＝一个「原词＋一次出现」；`python3 tools/term_db.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "term_layer")
os.makedirs(OUT, exist_ok=True)
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com")

BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读", "ocr_解读张仲景医学.txt"), ("传真系", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("汤液经方系", "ocr_冯世纶2005汤液经方系_书名待定.txt"),
         ("伤寒论传真", "传真_伤寒论传真.txt"), ("金匮传真", "传真_金匮要略传真.txt"),
         ("中国汤液方证", "汤液_中国汤液方证.txt")]

# ── L1 定义句 ──
# ⚠㉗批自查：首版把「者，」也当定义引导词，结果把**条文条件句**
# （"小便不利者，五苓散主之"）全部误收为定义——小便不利×26 全是假定义。
# 「者，」是条文的**条件标记**，不是定义标记。已移除；这类句由 REL_FANG 收进 L2。
DEF = re.compile(r"([一-鿿]{2,8})[，,]?\s*(?:指的?是|指|即是|即指|即|谓的?是|就是|系指|之谓也)"
                 r"\s*([^。；;]{4,60})")
DEF2 = re.compile(r"([一-鿿]{2,8})[，,]\s*([^。；;]{4,50}?)之谓(?:也)?")
# ── L2 关系句（同句内·原词 → 治法/方/禁忌）──
FANG = r"[一-鿿]{2,16}(?:汤|散|丸|饮|煎)"
REL_FANG = re.compile(r"([^。；;，,]{2,40}?)(?:者)?[，,]?\s*(?:宜|与|主之|用|投|治以|治宜|故治)\s*(" + FANG + r")")
REL_BAN = re.compile(r"([^。；;，,]{2,40}?)(?:者)?[，,]?\s*(不可(?:攻|下|与之?|发汗|吐|余药|更|服)[^。；;]{0,20})")
NOWORD = re.compile(r"[，,。；;：:0-9A-Za-z]")
# ── 弃件闸门（协议4 宁弃勿猜）──
# 讲座类书是**口语转录**，"这个…就是…""那么…即…"是话语填充，不是定义。
# 首版实测：5974 条中最高频主词为「这个×56／所以然×31／那么×23／就是×13」——
# 全是口语指代与连词。不调正则去猜，直接**弃件并登记**（同 holdout_mask 出件闸门）。
STOP = set("""这个 那个 这是 那是 就是 那么 所以 所以然 我们 你们 他这 咱们 如果 但是 因为 因此
其实 当然 一般 一定 就要 就得 也就 都是 不是 可是 而是 现在 后来 上面 下面 这样 那样 这种 那种
这类 那类 这条 那条 本条 上条 下条 前面 后面 头前 刚才 方才 反正 总之 总而 大概 大约 差不多
古人 今人 前人 后人 一句 一段 这段 那段 书上 原文 注家 王叔 成无 章太 陆渊""".split())
def drop(w, d):
    if w in STOP: return "口语指代词"
    if re.match(r"^(这|那|就|也|都|还|又|再|很|太|最|更|其)", w): return "口语起首"
    if re.match(r"^(这|那|就是|也就|所以|因为|但是)", d): return "定义体为口语"
    return None

terms, rels, bans = [], [], []
dropped = Counter()
for bk, fn in BOOKS:
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): continue
    lines = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    incase = False
    for i, raw in enumerate(lines):
        l = JUNK.sub("", re.sub(r"\s+", "", raw))
        if not l: continue
        if "【验案】" in l: incase = True
        elif re.search(r"【(方解|注解|辨证要点|原文|条文|用法)", l): incase = False
        lvl = "B" if incase else "A"
        for m in list(DEF.finditer(l)) + list(DEF2.finditer(l)):
            w, d = m.group(1), m.group(2)
            if NOWORD.search(w) or len(d) < 4: continue
            why = drop(w, d)
            if why: dropped[why] += 1; continue
            terms.append(dict(term=w, defn=d, book=bk, line=i + 1, lvl=lvl,
                              ctx=l[max(0, m.start() - 40):m.end() + 40]))
        for m in REL_FANG.finditer(l):
            rels.append(dict(cond=m.group(1)[-30:], fang=m.group(2), book=bk, line=i + 1, lvl=lvl,
                             ctx=l[max(0, m.start() - 30):m.end() + 20]))
        for m in REL_BAN.finditer(l):
            bans.append(dict(cond=m.group(1)[-30:], ban=m.group(2), book=bk, line=i + 1, lvl=lvl,
                             ctx=l[max(0, m.start() - 30):m.end() + 20]))

# ── 写出 ──
def w(f, s): open(os.path.join(OUT, f), "w", encoding="utf-8").write(s)

tc = Counter(t["term"] for t in terms)
L = ["# L1 原词定义库（胡老显式定义句·全量·一词多义不合并）", "",
     "> 取证器 `tools/term_db.py`（文件头含【已知失效模式】与口径）。",
     "> **同一原词的每次出现各占一行，上下文各自保留**——行数 > 词数是设计，不是重复。",
     "> 证据等级：A＝条文/注解原文；B＝医案段内；**C（序言/他人转述）须人工标，本工具不产**。", "",
     "**总计 %d 条定义句，涉 %d 个不同原词。**" % (len(terms), len(tc)),
     "", "**弃件 %d 条**（讲座类书系口语转录，「这个…就是…」是话语填充非定义；"
     "按协议4宁弃勿猜，不调正则去猜，直接弃并登记）：%s" % (sum(dropped.values()), dict(dropped)), "",
     "| # | 原词 | 胡老定义 | 出处 | 等级 | 上下文 |", "|---|---|---|---|---|---|"]
for k, t in enumerate(sorted(terms, key=lambda x: (-tc[x["term"]], x["term"], x["line"])), 1):
    L.append("| %d | **%s** | %s | %s L%d | %s | %s |" % (
        k, t["term"], t["defn"][:60], t["book"], t["line"], t["lvl"], t["ctx"][:70].replace("|", "／")))
w("L1_原词定义库.md", "\n".join(L))

L = ["# L2 原文明确关系库·证→方（同句内共现·跨句不收）", "",
     "> **只收原文同句内明确表达的「条件 → 方」**。跨句因果需要理解，属 L3，本工具不做。",
     "> **未经 L3 验证者不得进入引擎规则**（冻结指令 3）。", "",
     "**总计 %d 条。**" % len(rels), "",
     "| # | 条件（原文片段） | 方 | 出处 | 等级 |", "|---|---|---|---|---|"]
for k, r in enumerate(rels, 1):
    L.append("| %d | %s | **%s** | %s L%d | %s |" % (k, r["cond"].replace("|", "／"), r["fang"], r["book"], r["line"], r["lvl"]))
w("L2_关系库_证到方.md", "\n".join(L))

L = ["# L2 原文明确关系库·禁忌（显式「不可」句）", "",
     "> **只收原文显式的「不可X」**。",
     "> ⚠**禁止据统计未共现创造禁止关系**（冻结指令 8）——本表每一条都有原文。", "",
     "**总计 %d 条。**" % len(bans), "",
     "| # | 条件（原文片段） | 禁 | 出处 | 等级 |", "|---|---|---|---|---|"]
for k, r in enumerate(bans, 1):
    L.append("| %d | %s | **%s** | %s L%d | %s |" % (k, r["cond"].replace("|", "／"), r["ban"], r["book"], r["line"], r["lvl"]))
w("L2_关系库_禁忌.md", "\n".join(L))

json.dump(dict(terms=terms, rels=rels, bans=bans), open(os.path.join(OUT, "_term_raw.json"), "w"),
          ensure_ascii=False, indent=1)

print("L1 定义句 %d 条／不同原词 %d 个  ｜弃件 %d %s"
      % (len(terms), len(tc), sum(dropped.values()), dict(dropped)))
print("L2 证→方 %d 条 ｜ L2 禁忌 %d 条" % (len(rels), len(bans)))
print("按书：", dict(Counter(t["book"] for t in terms)))
print("等级：", dict(Counter(t["lvl"] for t in terms)))
print("\n出现最多的原词（一词多义候选，须逐条保留上下文）：")
for t, c in tc.most_common(15):
    print("   %-8s ×%d" % (t, c))
