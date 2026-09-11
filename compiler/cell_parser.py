#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cell_parser.py —— 原子 cell 解析器（123批·上级令二·2.2）

⛔⛔ **本器存在之唯一理由，是 122批 查出的【行粒度污染】：**

   V8 L4056 一行内并列四格：
       `脉滑→…⛔不得独立定热…｜数=热｜洪大=阳明气分｜结代=心血虚炙甘草｜沉迟→…`
   而 `tools/yuyi_huigui.py` 之 `REVOKED` 正则含 `⛔` 且**按整行判定**。
   ⇒ 该行因【脉滑】那格有 ⛔ 而**整行被视为已撤销**，
     `数=热` 便**永远不会被任何 mustnot 测试抓到**。
   ⇒ 这是本工程假绿之第四例，**且是唯一一例其成因不是我写错正则，
     而是【行粒度本身不够】**——正则再准也救不了。

⛔ **本器只做解析，不做医学判断。**
   它答的是：「这一行里有几格？哪一格带撤销记号？」
   **它不答「数是不是主热」——那是 `term_layer/脉象裸映射审计_123批.md` 之事。**

── 格之定义 ────────────────────────────────────────────────
  以 `|` 或 `｜` 切分一行；每一段为一个 cell。
  cell 之撤销状态**只由该段自身之文本决定**，
  ⛔ **不受同行兄弟格影响**——这正是本器与旧行级判定之全部分别。
"""
import re

# 撤销/限制记号（与 tools/yuyi_huigui.py 之 REVOKED 同源，但作用于【格】不作用于【行】）
REVOKED_MARK = re.compile(
    r"11[789]批(撤|收窄|改|降|加注)|12[0-9]批(撤|收窄|改|降|加注)"
    r"|作废原文|已撤|撤销|勘误|不得|禁止|⛔")

# 类型标记 {{at:...}}
AT_MARK = re.compile(r"\{\{at:([a-z_]+)\|")

# {{at:...}} 标记内部亦用 `|` 分隔（`{{at:trigger_candidate|obj=…|src=…|scope=…}}`）。
# ⛔ 若不先遮蔽，切格时会把 `obj=里热` `src=C卷·71679` `scope=D0}}` 当成裸映射。
#   ——初版即如此，实测误检 45 格中 30 格为此类。**先遮后切。**
AT_BLOCK = re.compile(r"\{\{at:[^}]*\}\}")

# 裸映射：`X=Y` 或 `X＝Y`，且该格内**无**任何撤销记号、无 {{at:}} 类型标记
BARE_MAP = re.compile(r"^\s*([^=＝\s]{1,12})\s*[=＝]\s*([^=＝]{1,30})\s*$")

# ⛔ 排除式：引号内之句多为【明文否定之例】（如 L2103「不能反推：『脉数＝热证充分条件』」），
#   星号/括号/句号多为定义句或说明句，皆非执行用之映射格。
#   ——114批 教训：L429/430 因前有「所以不能建立：」而被误计为冲突，误检率 67%。
NOT_A_MAPPING = re.compile(r"[“”\"'（）()。：:★]|\*\*")

# 候选箭头：`X→【候选…】`
ARROW = re.compile(r"[→⇒]")


class Cell(object):
    __slots__ = ("line_no", "idx", "text", "revoked", "at_types", "bare", "lhs", "rhs")

    def __init__(self, line_no, idx, text):
        self.line_no = line_no
        self.idx = idx
        self.text = text
        self.revoked = bool(REVOKED_MARK.search(text))
        self.at_types = AT_MARK.findall(text)
        m = BARE_MAP.match(text)
        self.bare = (bool(m) and not self.revoked and not self.at_types
                     and not NOT_A_MAPPING.search(text))
        self.lhs = m.group(1) if m else None
        self.rhs = m.group(2) if m else None

    @property
    def cell_id(self):
        return "L%d#%d" % (self.line_no, self.idx)

    def __repr__(self):
        return "<Cell %s revoked=%s bare=%s %r>" % (
            self.cell_id, self.revoked, self.bare, self.text[:24])


def split_cells(line, line_no=0):
    """把一行切成原子 cell。⛔ 每格之 revoked 只看自己。

    ⛔ 先把 `{{at:...}}` 整块遮成占位符再切，切完还原——
       否则标记内部之 `|` 会把一个标记撕成三四个假格。
    """
    blocks = []

    def _stash(m):
        blocks.append(m.group(0))
        return "\x00%d\x00" % (len(blocks) - 1)

    masked = AT_BLOCK.sub(_stash, line)
    parts = re.split(r"[|｜]", masked)
    out = []
    for i, p in enumerate(parts):
        for j, b in enumerate(blocks):
            p = p.replace("\x00%d\x00" % j, b)
        if p.strip():
            out.append(Cell(line_no, i, p))
    return out


def scan_file(path, line_filter=None):
    """扫全文；line_filter(line)->bool 可限定只扫某些行。"""
    out = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line_filter and not line_filter(line):
                continue
            out.extend(split_cells(line.rstrip("\n"), n))
    return out


def bare_mappings(path, line_filter=None):
    """返回所有【裸映射格】——无撤销记号、无类型标记之 `X=Y`。"""
    return [c for c in scan_file(path, line_filter) if c.bare]


# ── 旧行级判定之复现（只为在测试中对照，⛔ 不得用于生产） ──────────
def legacy_line_revoked(line):
    """122批 以前 tools/yuyi_huigui.py 之判法：整行有 ⛔ 即整行已撤。"""
    return bool(REVOKED_MARK.search(line))


if __name__ == "__main__":
    import os, sys
    B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    V8 = os.path.join(B, "V8", "hxs_engine_v8_full_v2.md")
    pulse = lambda L: ("脉" in L and ("=" in L or "＝" in L))
    bs = bare_mappings(V8, pulse)
    print("═══ 裸映射格（脉相关行）═══")
    for c in bs:
        print("  %-10s %s = %s" % (c.cell_id, c.lhs, c.rhs))
    print("\n共 %d 格。" % len(bs))
    print("\n⛔ 对照：若按【旧行级】判定，下列格会被其兄弟格之 ⛔ 掩蔽而查不到：")
    lines = open(V8, encoding="utf-8").read().split("\n")
    masked = [c for c in bs if legacy_line_revoked(lines[c.line_no - 1])]
    for c in masked:
        print("  %-10s %s = %s   ← 同行有 ⛔，旧判法整行放过" % (c.cell_id, c.lhs, c.rhs))
    print("\n被行级判定掩蔽者 %d/%d 格。" % (len(masked), len(bs)))
    sys.exit(0)
