#!/usr/bin/env python3
"""【表位无单方】＋【先后主次＝治法冲突】双命题检验（71批·上级指令二三）。

## 命题一（上级立·机制假说）
  **汗法消耗津液，津液出自里 → 任何表位方必须同时安排里位津液供给。**
  锚：桂枝汤「**既是发汗解热汤剂，又是安中养液方药**」｜麻黄汤须体液充盈｜五家禁汗。
  **验证法（上级指定）**：数三味以上表方，看是否每张都含里药。**若无一例外，则由统计现象升为结构必然。**

⛔⛔【本工具最大的陷阱·必须先拆·否则本测不可证伪】
  **甘草、生姜、大枣几乎无方不有。** 若「里药」定得宽，则「每张表方都含里药」
  **在任何方剂库上都恒真**，与表位无关——**那不是发现，是同义反复。**
  → **故本工具先算基线率**：**全部方**中含里药者占比。
    · 若基线 ≈ 100% → ⛔**本命题不可证伪，测不出东西，须换测法。**
    · 若基线明显低于表方之比例 → 才有判别力。
  **这一步不做，后面的数一律作废。**〔㊹·且与 67/70 批「基线必报」同源〕

## 命题二（上级[推演]·交执行线验）
  **主次不由病位轻重定，由「哪个位的治法会伤到另一个位」定。**
  三实例：§91 下利清谷先救里｜§106 表未解先解表｜§219 三阳合病独取阳明。
  **验证法**：全库抽「先…后…」「急当救…」条文，**逐条检验能否用「治法冲突」解释；
    不能解释者列表，即为该假说之反例。**

【已知失效模式】(视角㉕)
  ① **「表方」之认定**：本工具只收**方解/要点中明含表位判定语**者，不由药性推定〔R58〕。
  ② 药名归一之单位粘连与炮制前缀〔70批实发·沿用同一 norm〕。
  ③ 条文抽取之「先后」句式必不全；**报「已抽到的」，不称「全部」**〔R41 戊〕。
【口径】(视角㊱) `python3 tools/biaowei_wudanfang.py` 复跑。
"""
import re, os, json
from collections import Counter
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}")
BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读", "ocr_解读张仲景医学.txt"), ("传真系", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("汤液经方系", "ocr_冯世纶2005汤液经方系_书名待定.txt"),
         ("伤寒论传真", "传真_伤寒论传真.txt"), ("金匮传真", "传真_金匮要略传真.txt"),
         ("中国汤液方证", "汤液_中国汤液方证.txt")]
T = {bk: JUNK.sub("", re.sub(r"\s+","",open(os.path.join(B,"sources",fn),encoding="utf-8",errors="ignore").read()))
     for bk,fn in BOOKS if os.path.exists(os.path.join(B,"sources",fn))}
C = T["C卷"]
def norm(h):
    h = re.sub(r"^(?:克|g|两|钱|斤|枚|升|合|分|铢)+", "", h)
    h = re.sub(r"[各等]?分$|\d.*$|[一二三四五六七八九十]+[枚茎杯两斤]?$", "", h)
    h = re.sub(r"^(?:炙|炮|熟|清|炒|真|煨)(?=[一-鿿]{2,})", "", h)
    return h
HERB = re.compile(r"([一-鿿]{2,6})(?=\d|各)")
# ── 方剂库 ────────────────────────────────────────────────
fangs = {}
for m in re.finditer(r"([一-鿿]{2,12}(?:汤|散|丸))(?:方)?【方剂组成】(.{6,400}?)【", C):
    hs = set(norm(h) for h in HERB.findall(m.group(2)))
    hs = {h for h in hs if len(h) >= 2}
    if len(hs) >= 3: fangs.setdefault(m.group(1), hs)
# ── 表方之认定：方解/要点中明含表位判定语（不由药性推定）──
BIAO = re.compile(r"发汗|解表|解外|表实|表虚|在表|表不解|表未解|汗解")
biao = set()
for f in fangs:
    m = re.search(re.escape(f) + r"(?:方)?【方剂组成】.{0,700}?(?=【仲景|【验案|$)", C)
    if m and BIAO.search(m.group(0)): biao.add(f)
# ── 里药表（津液供给/健胃一类）──
LIYAO = {"生姜","大枣","甘草","人参","白术","苍术","干姜","半夏","粳米","饴糖","党参","茯苓"}
def has_li(hs): return bool(hs & LIYAO)
NA = len(fangs); NB = len(biao)
base = sum(1 for h in fangs.values() if has_li(h)) / NA
bi = sum(1 for f in biao if has_li(fangs[f])) / NB if NB else 0
print("═══ 命题一【表位无单方】═══")
print("C卷三味以上方 **%d**｜其中方解含表位判定语者 **%d**" % (NA, NB))
print("\n⛔[**先拆陷阱：基线率**]")
print("  **全部方**含里药者：%.1f%%" % (100*base))
print("  **表方**含里药者：  %.1f%%" % (100*bi))
if base > 0.95:
    print("  ⛔⭐**基线 >95%% → 本命题在本方剂库上恒真，不可证伪。**")
    print("  ⛔**「每张表方都含里药」不是发现，是同义反复——甘草姜枣几乎无方不有。**")
    print("  → ⭐**须换测法**：见下「加严测法」。")
else:
    print("  → 基线 %.1f%% 明显低于表方 %.1f%%，**有判别力**" % (100*base, 100*bi))
# ── ⭐加严测法：只看「核心里药」（津液供给之实药，排除甘草这类几乎通用者）──
CORE = {"人参","党参","粳米","饴糖","大枣","生姜"}
b2 = sum(1 for h in fangs.values() if h & CORE) / NA
bi2 = sum(1 for f in biao if fangs[f] & CORE) / NB if NB else 0
print("\n⭐[**加严测法·只计核心津液药**（人参/党参/粳米/饴糖/大枣/生姜，剔除甘草茯苓术）]")
print("  全部方 %.1f%%  ｜  **表方 %.1f%%**  → 差 %+.1f 个百分点" % (100*b2, 100*bi2, 100*(bi2-b2)))
exc = [f for f in biao if not (fangs[f] & CORE)]
print("  ⭐**表方中不含核心津液药者 %d 张**（＝反例候选）：%s" % (len(exc), "／".join(sorted(exc)[:14])))
print("  → **%s**" % ("⭐**表方显著高于基线，命题一得支持**" if bi2 - b2 > 0.15 else
      "⚠**表方与基线接近，命题一未获支持（差 %+.1f pp）**" % (100*(bi2-b2))))

# ══ 命题二【先后主次＝治法冲突】═══════════════════════════
print("\n═══ 命题二【先后主次＝治法冲突】═══")
PAT = re.compile(r"(先[救解治攻][^，。；]{0,12}(?:而)?后[救解治攻][^，。；]{0,12}|急当救[里表][^，。；]{0,10}|"
                 r"当先解(?:其)?[表外][^，。；]{0,10}|先解(?:其)?[表外][^，。；]{0,10})")
hits, seen = [], set()
for bk in T:
    for m in PAT.finditer(T[bk]):
        k = m.group(0)[:14]
        if k in seen: continue
        seen.add(k)
        hits.append((bk, m.group(0), T[bk][max(0,m.start()-110):m.start()+90]))
print("抽到「先…后…／急当救…」句 **%d 条**（去重后）⛔**是已抽到的，不称全部**〔R41戊〕" % len(hits))
CONFLICT = re.compile(r"亡阳|亡血|虚|陷|逆|变|不可发汗|不可下|伤|竭|脱|误")
ok_n = sum(1 for _, _, c in hits if CONFLICT.search(c))
print("  ⭐**其上下文含「治法冲突」类词（亡阳/陷/逆/不可发汗/伤/竭…）者：%d／%d ＝ %.0f%%**"
      % (ok_n, len(hits), 100*ok_n/max(1,len(hits))))
print("  ⛔**共现≠解释**〔R24〕：此数只说明冲突语常伴，**不证明每条都由冲突解释**。逐条须人读。")
print("\n[逐条·供人读]")
for bk, s0, c in hits[:14]:
    print("  〔%s〕**%s**\n     …%s…" % (bk, s0, c[-95:]))
assert norm("克炙甘草") == "甘草", "⛔自检失败：归一无效"
assert not BIAO.search("子虚乌有绝无一词"), "⛔自检失败：虚构句命中表位语"
print("\n[自检] 归一有效｜虚构句不命中表位语")
json.dump(dict(NA=NA, NB=NB, base=base, biao=bi, core_base=b2, core_biao=bi2,
               exc=sorted(exc), xianhou=len(hits)),
          open(os.path.join(B, "term_layer", "_biaowei.json"), "w"), ensure_ascii=False, indent=1)
