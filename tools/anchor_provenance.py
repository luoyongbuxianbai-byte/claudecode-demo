#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""anchor_provenance.py —— 清洗字位 → 原始 OCR 行段（126T·上级令六第一、二步）。

上级 126T 令六（分层实施，⛔ 不一次做完）：
  ① 先**保留**清洗文本版本与现有字位锚；
  ② 对**本批关键引用**建立**清洗字位 → 原始 OCR 行段**之对应；   ← ⭐ 本工具做的是这一步
  ③ 能取得版面时再补页码与图像核验，**不能从 OCR 行号猜出版页码**；
  ④ 存在**多处同文或无法唯一对应**者，**显式保留歧义**。

原理：`corpus_guard._clean` ＝ ①去一切空白 ②去 JUNK。两步皆为**删除**，
      故可重放该变换并为**每个存活字符**记下它在原始文件中的下标 ⇒ 得到一张
      `cleaned_index -> raw_index` 的映射。⛔ 本工具不改语料、不改锚。

⛔⛔ 本工具**不做**、也不能做的事：
  ⛔ 不给纸本页码——`---第N页---`、`龙门课栈N/732` 只是 **OCR 残迹所载之串**，
     ⛔ 未与版面核验；⛔ 严禁由 OCR 行号推算页码（上级令六第三步）。
  ⛔ 不判定该段落是否支持任何命题。

用法：
    python3 tools/anchor_provenance.py 讲伤寒 62900 63050
    python3 tools/anchor_provenance.py --batch evidence/锚溯源_126T.json
"""
import json
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, "tools"))
import corpus_guard as CG  # noqa: E402

PAGE_MARK = re.compile(r"---第\d+页---|[一-龥]{0,12}课栈\d+/\d+|·\d+·")

_CACHE = {}


def build_map(book):
    """返回 (cleaned_text, idx_map)；idx_map[i] ＝ 第 i 个清洗字符在原始文件中的下标。"""
    if book in _CACHE:
        return _CACHE[book]
    fn = dict(CG.BOOKS).get(book)
    if fn is None:
        raise SystemExit("⛔未知书名：%s" % book)
    raw = open(os.path.join(CG.SRC, fn), encoding="utf-8", errors="ignore").read()

    # 第一步：去空白，记下标
    s1, m1 = [], []
    for i, ch in enumerate(raw):
        if not ch.isspace():
            s1.append(ch)
            m1.append(i)
    s1 = "".join(s1)

    # 第二步：去 JUNK，沿用下标
    keep = [True] * len(s1)
    for m in CG.JUNK.finditer(s1):
        for k in range(m.start(), m.end()):
            keep[k] = False
    s2, m2 = [], []
    for k, ch in enumerate(s1):
        if keep[k]:
            s2.append(ch)
            m2.append(m1[k])
    s2 = "".join(s2)

    # 与唯一合规入口之结果比对——⛔ 不一致则停，绝不静默使用自建映射
    ref = CG.load_one(book)
    if s2 != ref:
        raise SystemExit("⛔ 重放之清洗结果与 corpus_guard.load_one 不一致（%d vs %d 字），"
                         "映射不可信，已停。" % (len(s2), len(ref)))
    # 行起始表
    line_starts = [0]
    for i, ch in enumerate(raw):
        if ch == "\n":
            line_starts.append(i + 1)
    _CACHE[book] = (raw, s2, m2, line_starts)
    return _CACHE[book]


def line_of(line_starts, raw_idx):
    lo, hi = 0, len(line_starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if line_starts[mid] <= raw_idx:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1  # 1-based


def resolve(book, start, end=None, quote_len=60):
    """给一个清洗字位区间，报其原始行段与歧义状况。"""
    raw, cleaned, m, line_starts = build_map(book)
    end = end if end is not None else start + quote_len
    end = min(end, len(cleaned))
    # ⛔⛔ 上级 126U 令六：端点口径须**统一并显式标注**，且须检查 start < end。
    #    126T 初版之病：`cleaned_end` 是**右开**，而 `raw_end` 取最后一字符之位置（**闭端**）
    #    ⇒ 同一条记录里两个端点口径不同，读者无从知道该不该 +1。
    #    ⇒ 126U 统一为 **[start, end) 左闭右开**：raw_end_exclusive ＝ 末字符下标 ＋ 1。
    #    ⚠ 原始文本中**被删去的空白／JUNK 不连续**，故 raw 区间是「覆盖该片段之最小闭包」，
    #      ⛔ 不表示该区间内每个字符都属于该片段。
    if not (0 <= start < len(cleaned)):
        raise SystemExit("⛔ 偏移越界：%s·%d（清洗长度 %d）" % (book, start, len(cleaned)))
    if not start < end:
        raise SystemExit("⛔ 端点非法：start(%d) 须 < end(%d)——%s" % (start, end, book))
    r0, r_last = m[start], m[end - 1]
    r1 = r_last + 1                      # ⭐ 右开
    l0, l1 = line_of(line_starts, r0), line_of(line_starts, r_last)
    snippet = cleaned[start:end]

    # ④ 歧义：该片段在清洗文本中出现几次
    occ = cleaned.count(snippet)

    # ③ 近旁之页码残迹 —— ⛔ 只报「原始文本里确实有这个串」，⛔ 不作页码断言
    win = raw[max(0, r0 - 1500):min(len(raw), r1 + 1500)]
    marks = sorted(set(PAGE_MARK.findall(win)))

    import hashlib
    fp = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:12]
    return dict(book=book,
                source_file=dict(CG.BOOKS)[book],
                cleaned_len=len(cleaned),
                cleaned_sha12=fp,          # ⭐ 清洗版本指纹：换了语料/清洗式即变，旧映射立即可辨
                interval_convention="[start, end) 左闭右开（cleaned 与 raw 两侧口径一致，126U 统一）",
                cleaned_start=start, cleaned_end=end,
                raw_start=r0, raw_end_exclusive=r1, raw_last_char=r_last,
                raw_span_caveat="⚠ raw 区间是覆盖该片段之**最小闭包**；⛔ 其中含已被删去之空白／JUNK，⛔ 不表示区间内每字符皆属该片段",
                raw_line_start=l0, raw_line_end=l1,
                snippet=snippet, occurrences_in_cleaned=occ,
                ambiguous=(occ != 1),
                page_marks_nearby_in_raw=marks,
                page_marks_caveat="⛔ 仅为 OCR 残迹所载之串，⛔ 未与版面核验，⛔ 不得据以断定纸本页码")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--batch" in sys.argv:
        spec = json.load(open(os.path.join(B, args[0]), encoding="utf-8"))
        out = []
        for it in spec["anchors"]:
            r = resolve(it["book"], it["cleaned_start"], it.get("cleaned_end"))
            r["label"] = it.get("label", "")
            out.append(r)
        spec["resolved"] = out
        spec["tool"] = "tools/anchor_provenance.py"
        json.dump(spec, open(os.path.join(B, args[0]), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        amb = sum(1 for r in out if r["ambiguous"])
        print("已解析 %d 条｜⚠ 歧义（清洗文中非唯一）%d 条 ⇒ 写回 %s" % (len(out), amb, args[0]))
        print("⛔ 本工具只到【原始 OCR 行段】，⛔ 未到纸本页码（上级令六第三步未做）。")
        return
    if len(args) < 2:
        raise SystemExit(__doc__)
    r = resolve(args[0], int(args[1]), int(args[2]) if len(args) > 2 else None)
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
