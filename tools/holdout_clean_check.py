#!/usr/bin/env python3
"""留出集干净度复核（协议1 三重grep ＋ 九字串比对）。

判据：一本书能否充留出集，取决于其**案例**是否已被引擎消化。
逐案抽取后对引擎全文做：
  ①病历号 ②就诊日期 ③特征短语（九字连续中文串）
三者任一命中 → 该案已曝光，不得入留出区。

用法：python3 tools/holdout_clean_check.py [书名...]
【已知失效模式】(㉓批·复盘视角㉕ 强制格式)
  ① **九字串比对在重OCR语料上假阴性极高**——同一案在两书中OCR差一个字即不命中。
     "干净"是本工具的**弱结论**，不是强保证。
  ② `benign()` 剔除条文原文与方名串，**剔除过头则真泄漏被当良性放过**；
     方名表来自引擎【…】头，引擎里没有的方名一律不剔(方向安全)但也一律不认。
  ③ 只查**案例**曝光，不查**理论段**曝光。一本书理论部分与引擎重合 84%
     (ocr1 实测)时，本工具仍会报其案例"干净"——⑮批归因错一半即此。
     **书能否充留出集，本工具只回答其中一半。**
【弃件条件】
  三项任一命中即判已曝光并弃件，**不做人工豁免**(协议4宁弃勿猜)。
"""
import re, sys, os

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ENG = re.sub(r"[^一-鿿0-9]", "",
             open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read())
ENG_RAW = open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read()

# ── 良性集：命中这些不算污染（㉑工具独立性·须查内容归属）──
# ① 引擎所载仲景条文原文：案例引用条文≠案例被记住
_CT = "".join(re.findall(r"^\[原文\][^\n]*", ENG_RAW, re.M))
_CT += "".join(re.findall(r"^[①]条文谱[^\n]*", ENG_RAW, re.M))
CANON = re.sub(r"[^一-鿿]", "", _CT)
# ② 方名（含合方串）：由引擎条目名构成，最长优先
_NM = sorted({m.group(1) for m in re.finditer(r"^【([^】·|]*?(?:汤|散|丸|饮|煎))[^】]*】", ENG_RAW, re.M)},
             key=len, reverse=True)

def benign(g):
    """九字串 g 是否属良性（条文原文／方名或合方串）"""
    if g in CANON:
        return True
    t = g
    for n in _NM:
        if n in t:
            t = t.replace(n, "")
    # 去掉方名后只剩连接字（合/加/去/及/与/汤散丸饮等）即视为方名串
    return len(re.sub(r"[合加去及与并方证汤散丸饮煎的]", "", t)) <= 1

# 方名白名单：九字串命中若整体为方名，属良性
FN = ["桂枝甘草龙骨牡蛎汤", "葛根加苓术附汤", "附子粳米汤", "小半夏加茯苓汤", "大柴胡汤",
      "桂枝茯苓丸", "小柴胡加生石膏", "半夏厚朴汤", "当归四逆加吴茱萸生姜汤", "越婢加术汤",
      "茯苓四逆汤", "木防己汤", "白头翁加甘草阿胶汤", "干姜黄连黄芩人参汤",
      "木防己去石膏加茯苓芒硝汤", "柴胡桂枝干姜汤", "当归芍药散", "苓桂术甘汤"]


def cases(path):
    """按'初诊'切案：取初诊前80字(人口学)＋后420字(症治)"""
    T = open(path, encoding="utf-8", errors="ignore").read()
    F = re.sub(r"[\s　]+", "", T)
    out = []
    for m in re.finditer(r"初诊", F):
        s = max(0, m.start() - 80)
        out.append(F[s:m.start() + 420])
    return out


def check(path):
    name = os.path.basename(path)
    cs = cases(path)
    ids = dates = phrases = 0
    dirty = 0
    for c in cs:
        hit = False
        for m in re.finditer(r"病历号\s*[:：]?\s*(\d{4,})", c):
            if m.group(1) in ENG_RAW:
                ids += 1; hit = True
        for m in re.finditer(r"((?:19|20)\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})", c):
            if re.search(r"%s\D{0,3}%s\D{0,3}%s" % m.groups(), ENG_RAW):
                dates += 1; hit = True
        cn = re.sub(r"[^一-鿿]", "", c)
        grams = {cn[i:i + 9] for i in range(len(cn) - 8)}
        real = [g for g in grams if g in ENG
                and not any(g in f or f in g for f in FN)
                and not benign(g)]
        if real:
            phrases += 1; hit = True
        if hit:
            dirty += 1
    n = len(cs)
    print("\n【%s】" % name)
    print("  切得案例 %d" % n)
    if not n:
        print("  → 无案，不可作留出源"); return name, 0, 0
    print("  病历号命中 %d ｜ 就诊日期命中 %d ｜ 九字特征串命中 %d" % (ids, dates, phrases))
    print("  **已曝光案 %d ／ 干净案 %d = 干净率 %.1f%%**" % (dirty, n - dirty, 100 * (n - dirty) / n))
    return name, n, n - dirty


if __name__ == "__main__":
    files = sys.argv[1:] or [os.path.join(B, "sources", f)
                             for f in sorted(os.listdir(os.path.join(B, "sources")))
                             if f.endswith(".txt") and f != "MD5SUMS.txt"]
    res = [check(f) for f in files]
    print("\n" + "=" * 60)
    print("%-38s %6s %6s" % ("源书", "案数", "干净"))
    for n, a, c in res:
        print("%-38s %6d %6d" % (n[:36], a, c))
