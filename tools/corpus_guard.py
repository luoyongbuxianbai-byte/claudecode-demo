#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
corpus_guard.py —— 语料载入唯一合规入口（87批·用户令·常设纪律）

事故谱系：
  · 65批 发现《中医临床家胡希恕》147,300 字被清洗正则静默销毁至 181 字，
    且持续十批未被发现（协议16 事故）。
  · 82批 scratchpad 全清、83批 容器换新克隆工作区全丢，两次皆事后补救。

本模块提供三重防护，缺一不可：
  ① 清洗降幅守卫：去空白→JUNK 清洗后，降幅 > MAX_DROP（20%）即 SystemExit。
     ——上级 87批 令，将旧阈值 50% 收紧至 20%。
  ② 基线核对：与冻结基线比对，偏离 > BASE_TOL（2%）即 SystemExit。
     ——降幅守卫只看单次载入前后比，基线守卫看的是「与已知良好值」比，
       可捕获「清洗式改坏后各工具同步变小」这一降幅守卫看不见的模式。
  ③ 有界 JUNK：`\\S{0,60}` / `\\S{0,40}` 为 65批 修复值，⛔ 严禁改回无界 `\\S*`。

用法：
    from corpus_guard import load_books, load_one, JUNK
    T = load_books()                 # 十二书全量，dict: 书名 -> 去空白清洗后正文
    C = load_one("C卷")

开工预检（闸门9 第六款，每批用到语料前必跑）：
    python3 tools/corpus_guard.py --audit
"""
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(B, "sources")

MAX_DROP = 0.20   # 清洗降幅上限（87批：50% → 20%）
BASE_TOL = 0.02   # 与冻结基线之容差

# ⛔ 65批修复值：`\S{0,60}` / `\S{0,40}` 为有界量词。
#    改回无界 `\S*` 会在去空白后吞掉整本书（临床家事故原型）。
JUNK = re.compile(
    r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
    r"www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}"
)

BOOKS = [
    ("C卷",           "C_jingfangliyu.txt"),
    ("讲伤寒",         "ocr_未识别2.txt"),
    ("讲金匮",         "ocr_未识别1.txt"),
    ("解读",           "ocr_解读张仲景医学.txt"),
    ("传真系",         "ocr_经方传真系.txt"),
    ("病位类方解",     "ocr_胡希恕病位类方解.txt"),
    ("临床家",         "ocr_中医临床家胡希恕.txt"),
    ("带教",           "ocr_冯世纶带教实录第一辑.txt"),
    ("汤液经方系",     "ocr_冯世纶2005汤液经方系_书名待定.txt"),
    ("伤寒论传真",     "传真_伤寒论传真.txt"),
    ("金匮要略传真",   "传真_金匮要略传真.txt"),
    ("中国汤液方证",   "汤液_中国汤液方证.txt"),
]

# 冻结基线：去空白 + JUNK 清洗后之字数。87批冻结。
# 修改本表须在报告中说明理由——它是「静默销毁」的最后一道锚。
# 实测冻结（87批），非估值。当日全书最大清洗降幅 9.82%（临床家），故 20% 阈值有余量。
# ⚠ 历批报告所记「字数」有两种口径：部分为去空白值（清洗前），部分为清洗后值。
#    本表统一为**清洗后**口径，与 _clean() 产出同源。
BASELINE = {
    "C卷": 159923, "讲伤寒": 395556, "讲金匮": 282577, "解读": 276905,
    "传真系": 215599, "病位类方解": 188544, "临床家": 132831, "带教": 101431,
    "汤液经方系": 195656, "伤寒论传真": 169436, "金匮要略传真": 117573,
    "中国汤液方证": 187749,
}


def _clean(raw, tag):
    n0 = len(re.sub(r"\s+", "", raw))
    t = JUNK.sub("", re.sub(r"\s+", "", raw))
    if n0 and (1 - len(t) / n0) > MAX_DROP:
        raise SystemExit(
            "⛔协议16 中止：%s 清洗降幅 %.1f%%（%d→%d），超上限 %.0f%%。"
            "疑清洗正则吃掉正文——检查是否有无界 \\S* 量词。"
            % (tag, 100 * (1 - len(t) / n0), n0, len(t), 100 * MAX_DROP)
        )
    base = BASELINE.get(tag)
    if base and abs(len(t) - base) / base > BASE_TOL:
        raise SystemExit(
            "⛔协议16 中止：%s 清洗后 %d 字，偏离冻结基线 %d 字达 %.1f%%（容差 %.0f%%）。"
            "语料或清洗式已变——先查明再跑，勿覆盖基线。"
            % (tag, len(t), base, 100 * abs(len(t) - base) / base, 100 * BASE_TOL)
        )
    return t


def load_one(book):
    fn = dict(BOOKS).get(book)
    if fn is None:
        raise SystemExit("⛔未知书名：%s（可选：%s）" % (book, "/".join(b for b, _ in BOOKS)))
    p = os.path.join(SRC, fn)
    if not os.path.exists(p):
        raise SystemExit("⛔语料缺失：%s（%s）——语料完备性核查未过，勿跑" % (book, p))
    return _clean(open(p, encoding="utf-8", errors="ignore").read(), book)


def load_books():
    """十二书全量。任一本缺失或异常即中止——不静默跳过（76批语料缺三本之教训）。"""
    missing = [b for b, fn in BOOKS if not os.path.exists(os.path.join(SRC, fn))]
    if missing:
        raise SystemExit("⛔语料完备性核查未过，缺 %d 本：%s" % (len(missing), "、".join(missing)))
    return {b: load_one(b) for b, _ in BOOKS}


def audit():
    print("== 语料完备性与协议16 预检（十二书）==")
    print("阈值：清洗降幅 ≤ %.0f%% ｜ 基线容差 ± %.0f%%\n" % (100 * MAX_DROP, 100 * BASE_TOL))
    print("%-14s %10s %10s %8s %8s  %s" % ("书", "去空白", "清洗后", "降幅", "偏基线", "判"))
    bad = 0
    for bk, fn in BOOKS:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            print("%-14s %10s %10s %8s %8s  ⛔缺失" % (bk, "-", "-", "-", "-"))
            bad += 1
            continue
        raw = open(p, encoding="utf-8", errors="ignore").read()
        n0 = len(re.sub(r"\s+", "", raw))
        t = JUNK.sub("", re.sub(r"\s+", "", raw))
        drop = (1 - len(t) / n0) if n0 else 0
        base = BASELINE.get(bk)
        dev = abs(len(t) - base) / base if base else 0
        ok = drop <= MAX_DROP and dev <= BASE_TOL
        bad += 0 if ok else 1
        print("%-14s %10d %10d %7.2f%% %7.2f%%  %s"
              % (bk, n0, len(t), 100 * drop, 100 * dev, "✅" if ok else "⛔"))
    print("\n结果：%d/%d 通过。" % (len(BOOKS) - bad, len(BOOKS)))
    if bad:
        print("⛔ 有未通过项——禁止在此状态下跑任何取证工具。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(audit() if "--audit" in sys.argv else audit())
