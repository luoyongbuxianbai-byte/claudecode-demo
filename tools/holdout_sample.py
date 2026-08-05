#!/usr/bin/env python3
"""协议11 留出保留区·分层抽样器。

规则（协议11）：
- 只从**干净案**中抽（引擎三重grep零命中 ∧ 与C卷验案无文本重叠）；
- 按**七族分层**随机抽 ≥30%（不少于30则）；
- 抽中者写入 holdout/cases/，**引擎侧零消费**；
- 映射（案号→源书+偏移）单独存 holdout/_mapping/，与引擎分离。

用法：python3 tools/holdout_sample.py [--apply]
"""
import re, os, sys, random, hashlib, json

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(B, "sources")
SEED = 20260805
random.seed(SEED)

ENG = re.sub(r"[^一-鿿0-9]", "", open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read())
ENG_RAW = open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read()
_CT = "".join(re.findall(r"^\[原文\][^\n]*", ENG_RAW, re.M)) + \
      "".join(re.findall(r"^①条文谱[^\n]*", ENG_RAW, re.M))
CANON = re.sub(r"[^一-鿿]", "", _CT)
NAMES = sorted({m.group(1) for m in re.finditer(r"^【([^】·|]*?(?:汤|散|丸|饮|煎))[^】]*】", ENG_RAW, re.M)},
               key=len, reverse=True)
C = re.sub(r"[\s　]+", "", open(os.path.join(SRC, "C_jingfangliyu.txt"), encoding="utf-8").read())
CCASE = "".join(re.sub(r"[^一-鿿]", "", x) for x in re.findall(r"【验案】(.{40,500}?)(?:【|$)", C, re.S))

# 七族：族名 → 判族关键方名片段（最长优先匹配处方文本）
FAM = [("柴胡族", ["柴胡"]),
       ("桂枝族", ["桂枝", "建中", "苓桂"]),
       ("麻黄族", ["麻黄", "葛根", "大青龙", "小青龙", "越婢", "麻杏"]),
       ("承气白虎泻心族", ["承气", "白虎", "泻心", "陷胸", "栀子", "黄连", "黄芩", "茵陈"]),
       ("四逆附子族", ["四逆", "附子", "乌头", "干姜", "理中", "真武"]),
       ("金匮各篇族", ["防己", "薏苡", "栝蒌", "薤白", "当归", "芎归", "胶艾", "温经", "肾气", "五苓", "猪苓"]),
       ("其他", [])]


def benign(g):
    if g in CANON: return True
    t = g
    for n in NAMES:
        if n in t: t = t.replace(n, "")
    return len(re.sub(r"[合加去及与并方证汤散丸饮煎的]", "", t)) <= 1


def famof(txt):
    for fam, keys in FAM[:-1]:
        for k in keys:
            if k in txt: return fam
    return "其他"


def harvest(fn):
    F = re.sub(r"[\s　]+", "", open(os.path.join(SRC, fn), encoding="utf-8", errors="ignore").read())
    out = []
    for m in re.finditer(r"初诊", F):
        s, e = max(0, m.start() - 80), m.start() + 420
        c = F[s:e]
        cn = re.sub(r"[^一-鿿]", "", c)
        grams = {cn[i:i + 9] for i in range(len(cn) - 8)}
        if any(g in ENG and not benign(g) for g in grams): continue          # 引擎已曝光
        if any(cn[i:i + 11] in CCASE for i in range(len(cn) - 10)): continue  # 与C卷重叠
        if re.search(r"病历号\s*[:：]?\s*(\d{4,})", c) and \
           re.search(r"病历号\s*[:：]?\s*(\d{4,})", c).group(1) in ENG_RAW: continue
        out.append(dict(src=fn, off=s, text=c, fam=famof(c)))
    return out


BOOKS = ["ocr_冯世纶2005汤液经方系_书名待定.txt", "ocr_中医临床家胡希恕.txt",
         "ocr_冯世纶带教实录第一辑.txt", "ocr_解读张仲景医学.txt"]
pool = []
for b in BOOKS:
    got = harvest(b)
    print("%-38s 干净案 %d" % (b[:36], len(got)))
    pool += got
print("\n干净案池合计 %d" % len(pool))

from collections import Counter, defaultdict
byfam = defaultdict(list)
for c in pool: byfam[c["fam"]].append(c)
print("\n分族：")
for f, _ in FAM: print("  %-16s %d" % (f, len(byfam[f])))

RATE = 0.30
picked = []
for f, _ in FAM:
    g = byfam[f]
    if not g: continue
    k = max(1, round(len(g) * RATE))
    picked += random.sample(g, k)
if len(picked) < 30:
    rest = [c for c in pool if c not in picked]
    picked += random.sample(rest, min(30 - len(picked), len(rest)))
print("\n**抽中 %d 则 (占干净池 %.1f%%)**" % (len(picked), 100 * len(picked) / len(pool)))
print(dict(Counter(c["fam"] for c in picked)))

if "--apply" in sys.argv:
    cd = os.path.join(B, "holdout", "cases"); os.makedirs(cd, exist_ok=True)
    md = os.path.join(B, "holdout", "_mapping"); os.makedirs(md, exist_ok=True)
    mapping = []
    for i, c in enumerate(sorted(picked, key=lambda x: (x["fam"], x["src"], x["off"])), 1):
        hid = "H%03d" % i
        open(os.path.join(cd, hid + ".txt"), "w", encoding="utf-8").write(c["text"])
        mapping.append(dict(id=hid, src=c["src"], off=c["off"], fam=c["fam"],
                            sha=hashlib.sha256(c["text"].encode()).hexdigest()[:16]))
    json.dump(dict(seed=SEED, rate=RATE, n=len(picked), items=mapping),
              open(os.path.join(md, "mapping.json"), "w"), ensure_ascii=False, indent=1)
    print("\n[已写入] holdout/cases/ %d 件；映射 holdout/_mapping/mapping.json" % len(picked))
else:
    print("\n[dry-run]")
