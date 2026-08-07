#!/usr/bin/env python3
"""协议11 留出保留区·分层抽样器 **v2**。

v1 缺陷（⑰批查获）：按"初诊"前后定长切窗，**30/37 件跨了案边界**——
片段里混着上一案的处方尾、下一段的理论文，医师无法据以作答。**v1 产物作废。**

v2 改为**真边界切案**：
  案起 = 「例N」/「初诊日期」/「(一)(二)…」＋人口学串
  案止 = 「结果…」段末，或下一案起
并要求每案**同时含** ①症状描述 ②处方或结果——否则不成其为可判之案。
再加 OCR 可读性闸门（生僻符号率），**宁弃勿猜**。

用法：python3 tools/holdout_sample.py [--apply]
【已知失效模式】(㉓批·复盘视角㉕ 强制格式)
  ① **切案靠正则识别人口学串与"结果"段**——书的排版一变即全盘失效。
     v1 定长切窗致 30/37 跨案作废；v2 补真边界；v3 漏教材条目闸门致 10/33 粘条目；
     **三次作废的根因都是"这一版没见过的排版形态"**。故任何新书入池，
     **必须人工抽验 3 件出件**，不得直接信任产出数。
  ② 闸门是**逐个补上去的**(过短/无症状/无处方/OCR重噪/粘教材条目/跨案/已曝光/
     与C卷重叠)，**每一个都是被打了之后才加的**。可预期仍有未见过的形态。
  ③ RATE 上调(0.30→0.40)是为凑够协议11 的"不少于30则"，
     **抽样率因下游闸门而变，已非纯随机分层**——泛化数须据此打折读。
【弃件条件】
  任一闸门命中即剔除并计入 rej 计数表，**不做边界通融**(协议4)。
"""
import re, os, sys, random, hashlib, json
from collections import Counter, defaultdict

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(B, "sources")
SEED = 20260805
random.seed(SEED)

RAW = open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read()
ENG = re.sub(r"[^一-鿿0-9]", "", RAW)
CANON = re.sub(r"[^一-鿿]", "", "".join(re.findall(r"^\[原文\][^\n]*", RAW, re.M)) +
               "".join(re.findall(r"^①条文谱[^\n]*", RAW, re.M)))
NAMES = sorted({m.group(1) for m in re.finditer(r"^【([^】·|]*?(?:汤|散|丸|饮|煎))[^】]*】", RAW, re.M)},
               key=len, reverse=True)
C = re.sub(r"[\s　]+", "", open(os.path.join(SRC, "C_jingfangliyu.txt"), encoding="utf-8").read())
CCASE = "".join(re.sub(r"[^一-鿿]", "", x) for x in re.findall(r"【验案】(.{40,500}?)(?:【|$)", C, re.S))

FAM = [("柴胡族", ["柴胡"]),
       ("桂枝族", ["桂枝", "建中", "苓桂"]),
       ("麻黄族", ["麻黄", "葛根", "大青龙", "小青龙", "越婢", "麻杏"]),
       ("承气白虎泻心族", ["承气", "白虎", "泻心", "陷胸", "栀子", "黄连", "黄芩", "茵陈"]),
       ("四逆附子族", ["四逆", "附子", "乌头", "干姜", "理中", "真武"]),
       ("金匮各篇族", ["防己", "薏苡", "栝蒌", "薤白", "当归", "芎归", "胶艾", "温经", "肾气", "五苓", "猪苓"]),
       ("其他", [])]

START = re.compile(r"(?:例\s*\d+|[（(][一二三四五六七八九十]{1,2}[)）])?"
                   r"[一-鿿]{1,3}[某]?[，,、]?\s*(?:男|女)(?:性)?[，,、]?\s*\d{1,2}\s*岁"
                   r"|初诊日期|初诊[：:]")
END = re.compile(r"结果[：:].{0,220}?(?:愈|已|消失|正常|好转|减|止)|按[：:]")


def benign(g):
    if g in CANON: return True
    t = g
    for n in NAMES:
        if n in t: t = t.replace(n, "")
    return len(re.sub(r"[合加去及与并方证汤散丸饮煎的]", "", t)) <= 1


def famof(t):
    for fam, keys in FAM[:-1]:
        for k in keys:
            if k in t: return fam
    return "其他"


def harvest(fn):
    F = re.sub(r"[\s　]+", "", open(os.path.join(SRC, fn), encoding="utf-8", errors="ignore").read())
    starts = [m.start() for m in START.finditer(F)]
    out, rej = [], Counter()
    for i, s in enumerate(starts):
        lim = starts[i + 1] if i + 1 < len(starts) else len(F)
        seg = F[s:min(lim, s + 900)]
        e = END.search(seg)
        c = seg[:e.end()] if e else seg
        if len(c) < 120: rej["过短"] += 1; continue
        if not re.search(r"苔|脉|痛|热|寒|呕|利|汗|渴", c): rej["无症状描述"] += 1; continue
        if not (re.search(r"结果|愈|克|钱", c)): rej["无处方或结果"] += 1; continue
        if len(re.findall(r"[㐀-䶿]|[`'\"|_={}\[\]]", c)) > 8: rej["OCR重噪"] += 1; continue
        # ⑱批闸门：教材条目结构标记＝本片段已越过案文进入方证讲解段
        # (⑰批漏设此闸，致10/33出件粘着"15.茯苓四逆汤证【证象】…"一类条目，
        #  其"烦躁/小便不利"是条目证象而非病人症状，直接坏掉金标准)
        if re.search(r"\d{1,2}\s*[.、]\s*[一-鿿]{2,14}[汤散丸煎]证|【证象|【证质|【类证|【禁忌|证象〗|证质〗", c):
            rej["粘教材条目"] += 1; continue
        if len(re.findall(r"[（(][一二三四五六七八九十]{1,2}[)）]|例\s*\d+|初诊日期|初诊[：:]", c)) >= 2:
            rej["跨案"] += 1; continue
        cn = re.sub(r"[^一-鿿]", "", c)
        if any(cn[i:i + 9] in ENG and not benign(cn[i:i + 9]) for i in range(len(cn) - 8)):
            rej["引擎已曝光"] += 1; continue
        if any(cn[i:i + 11] in CCASE for i in range(len(cn) - 10)):
            rej["与C卷重叠"] += 1; continue
        out.append(dict(src=fn, off=s, text=c, fam=famof(c)))
    return out, rej


BOOKS = ["ocr_冯世纶2005汤液经方系_书名待定.txt", "ocr_中医临床家胡希恕.txt",
         "ocr_冯世纶带教实录第一辑.txt", "ocr_解读张仲景医学.txt"]
pool = []
for b in BOOKS:
    got, rej = harvest(b)
    print("%-38s 可用 %3d  ｜剔除 %s" % (b[:36], len(got), dict(rej)))
    pool += got
print("\n**可用干净案池 %d**" % len(pool))
byfam = defaultdict(list)
for c in pool: byfam[c["fam"]].append(c)
print("分族：" + " ".join("%s%d" % (f, len(byfam[f])) for f, _ in FAM))

RATE = 0.40   # ⑱批上调：v3 闸门加严后，30% 抽样经出件闸门只剩26则(<30下限)；
              # 协议11 要求'≥30%且不少于30则'，故上调抽样率以保出件数达标。
picked = []
for f, _ in FAM:
    g = byfam[f]
    if g: picked += random.sample(g, max(1, round(len(g) * RATE)))
if len(picked) < 30:
    rest = [c for c in pool if c not in picked]
    picked += random.sample(rest, min(30 - len(picked), len(rest)))
print("\n**抽中 %d 则**（占池 %.1f%%）%s" %
      (len(picked), 100 * len(picked) / max(1, len(pool)), dict(Counter(c["fam"] for c in picked))))

if "--apply" in sys.argv:
    cd = os.path.join(B, "holdout", "cases"); os.makedirs(cd, exist_ok=True)
    for old in os.listdir(cd): os.remove(os.path.join(cd, old))
    md = os.path.join(B, "holdout", "_mapping"); os.makedirs(md, exist_ok=True)
    mapping = []
    for i, c in enumerate(sorted(picked, key=lambda x: (x["fam"], x["src"], x["off"])), 1):
        hid = "H%03d" % i
        open(os.path.join(cd, hid + ".txt"), "w", encoding="utf-8").write(c["text"])
        mapping.append(dict(id=hid, src=c["src"], off=c["off"], fam=c["fam"],
                            sha=hashlib.sha256(c["text"].encode()).hexdigest()[:16]))
    json.dump(dict(seed=SEED, rate=RATE, n=len(picked), version="v2-真边界切案", items=mapping),
              open(os.path.join(md, "mapping.json"), "w"), ensure_ascii=False, indent=1)
    print("\n[已写入] holdout/cases/ %d 件（v1 产物已清除）" % len(picked))
else:
    print("\n[dry-run]")
