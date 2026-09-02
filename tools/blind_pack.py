#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blind_pack.py —— 盲测出题包生成（97批·用户提出「新会话作执行器」之解法）

原理（用户 97批）：**污染是会话级的，不是账号级的。**
新开一个会话，它读得到 git 仓库，但不继承本会话的对话记忆——本会话已见之 gold 它未见过。

三角色分离：
  · **出题者**（本会话）：知答案，**不判**。选案、遮盲、封存 gold。
  · **判题者**（新会话）：不知答案，只判。
  · **揭盲者**（本会话）：持 gold 判分，**不参与判**。

产出：
  blind_test/            ← 交给新会话，只含遮盲正文与执行指令
  blind_gold/            ← ⛔ 新会话禁读；含 gold 正文与 sha256 承诺
用法：
  python3 tools/blind_pack.py --build   # 出题
  python3 tools/blind_pack.py --verify  # 泄漏自检（遮盲件中不得出现方名/六经名/剂量）
"""
import hashlib
import json
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CD = os.path.join(B, "holdout", "cases")
TD = os.path.join(B, "blind_test")
GD = os.path.join(B, "blind_gold")

# 选案（97批）：4 实测 ＋ 1 对照。对照案本不需查任何附录。
PICK = [("T1", "H039"), ("T2", "H033"), ("T3", "H013"), ("T4", "H041"), ("T5", "H032")]
CONTROL = "T5"

JUNK = re.compile(r"http\S{0,60}|---第\d+页---|[A-Za-z0-9|/.]{6,}")

# 切点：复用 holdout_mask.py v4 之 CUT（经 ⑰⑲批 两次实测迭代，每放宽一处即漏一种形态）
CUT = re.compile(
    r"证属|证为|此为|辨为|诊为|证系|乃[一-鿿]{0,4}之证|属[一-鿿]{2,8}证"
    r"|方用|治以|拟用|治宜|宜与|治[之则]"
    r"|[为是即][^。，,]{0,8}[一-鿿]{2,14}[汤散丸煎]"
    r"|(?:与|予|投|用|处方|服)[^。，,]{0,4}[一-鿿]{2,14}[汤散丸煎]"
    r"|(?:胡老|朐老|冯老|老)[^。]{0,8}(?:处方|与|投|用|认为|当即|诊为)"
    r"|\d{1,4}\s*[克钱两]|[一二三四五六七八九十]\s*[钱两][^。]{0,2}[克钱两]"
    r"|结果|二诊|三诊|复诊|上药服|药后"
    r"|综合分析|中医辨证|辨证为|此属|此乃|据此辨|归纳[为如]"
    r"|宗此法|与《?伤寒论》?第\s*\d+\s*条|所述机制"
    r"|太阳病?中?风?证|阳明|少阳|太阴|少阴|厥阴|合病|并病"
    r"|里实|里虚|表虚|表实|上热下寒|营卫不和|水饮内停|饮停|停饮|津伤|阳虚|阴虚|血虚|气虚")

# 去标识：姓名、日期、病历号、性别年龄之组合 → 一律抹去（防新会话据以反查原案）
IDENT = [
    (re.compile(r"[一-鿿]{1,3}(?:某某|某)[,，]?"), ""),
    (re.compile(r"(?:19|20)\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日"), "〔日期已去〕"),
    (re.compile(r"(?:19|20)\d{2}\s*年\s*\d{1,2}\s*月"), "〔日期已去〕"),
    (re.compile(r"病案[名号][:：]?\s*\d+|病历号\s*\d+"), ""),
    (re.compile(r"初诊日期[:：]?"), ""),
    (re.compile(r"[一-鿿]{2,3}[,，]\s*[男女](?:性|童)?[,，]\s*\d{1,3}\s*岁"), "〔患者〕"),
    # ⚠97批补：首版漏三处——「男性,43岁」不匹配「[男女],岁」；OCR 坏日期(4966年)未去；
    #   医家名可被新会话用于反查原案。
    (re.compile(r"^[一-鿿]{2,4}[,，]\s*(?=[男女])"), ""),
    (re.compile(r"\d{3,4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日"), "〔日期已去〕"),
    (re.compile(r"胡老|朐老|冯老|胡希恕|冯世纶"), "〔某中医〕"),
]

# 泄漏自检词表（⛔ 出现即该例作废）
# ⚠ 97批：首版把「口干思饮」误判为方名（「饮」亦是症状字）。
#    故方名后缀之「饮／煎」须排除症状用法（思饮/欲饮/引饮/渴饮/能饮/不饮/煎…）。
LEAK = re.compile(
    r"[一-鿿]{2,14}(?:汤|散|丸)"                                  # 方名（汤散丸）
    r"|(?<![思欲引渴能不喜多少])[一-鿿]{2,12}(?:饮子|煎剂)"        # 方名（饮子/煎剂）
    r"|太阳|阳明|少阳|太阴|少阴|厥阴"                              # 六经名
    r"|\d{1,4}\s*[克钱两]"                                        # 剂量
    r"|证属|辨为|治以|方用")


def mask(text):
    t = JUNK.sub("", text)
    m = CUT.search(t)
    if m:
        t = t[:m.start()]
    for pat, rep in IDENT:
        t = pat.sub(rep, t)
    return re.sub(r"\s+", "", t).strip()


def build():
    os.makedirs(TD, exist_ok=True)
    os.makedirs(GD, exist_ok=True)
    gold = {}
    for tid, src in PICK:
        raw = open(os.path.join(CD, src + ".txt"), encoding="utf-8", errors="ignore").read()
        blind = mask(raw)
        leaks = LEAK.findall(blind)
        open(os.path.join(TD, tid + ".txt"), "w", encoding="utf-8").write(blind)
        gold[tid] = {
            "src": src,
            "gold_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "blind_len": len(blind),
            "leak_hits": leaks,
            "is_control": tid == CONTROL,
        }
        print("%s ← %s  遮盲后 %d 字  泄漏命中 %d %s"
              % (tid, src, len(blind), len(leaks), leaks[:4] if leaks else ""))
    json.dump(gold, open(os.path.join(GD, "gold_index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n遮盲件 → blind_test/｜gold 索引 → blind_gold/（⛔新会话禁读）")
    bad = [k for k, v in gold.items() if v["leak_hits"]]
    if bad:
        print("⛔ 泄漏未清，须人工处理：%s" % bad)
    return 1 if bad else 0


def verify():
    n = bad = 0
    for f in sorted(os.listdir(TD)):
        if not f.endswith(".txt"):
            continue
        n += 1
        t = open(os.path.join(TD, f), encoding="utf-8").read()
        hits = LEAK.findall(t)
        print("  %-8s %4d字  泄漏 %d %s" % (f, len(t), len(hits), hits[:5] if hits else "✅"))
        bad += 1 if hits else 0
    print("泄漏自检：%d/%d 干净" % (n - bad, n))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(verify() if "--verify" in sys.argv else build())
