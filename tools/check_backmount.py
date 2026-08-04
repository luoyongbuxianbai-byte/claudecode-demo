#!/usr/bin/env python3
"""附录X 出口回挂锚的校验与自动重同步。

背景：方证条目里的"鉴别·出口回挂"行带 `附录X L####` 行号提示。引擎文件任何一次
插入都会使其后所有行下移，行号随即失准——⑦批内就连续发生两次(先是 L5 复核文字
+16 行，再是本说明 +8 行)。权威锚是 ◆段名◆，行号只是跳转提示。

用法：
    python3 tools/check_backmount.py            # 只校验
    python3 tools/check_backmount.py --fix      # 按 ◆段名◆ 重算行号并写回

校验三项：
  1. 每个行号提示确实落在一个 ◆ 段首行上，且该段名与所载段名一致
  2. 回挂行所列的每个"对举方"确实出现在被引 ◆ 段内
  3. 条目自身也出现在被引 ◆ 段内（否则说明这条出口挂错了方）
"""
import re, sys, os

ENGINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "hxs_engine_v79_full.md")
MOUNT = "鉴别·出口回挂"
REF = re.compile(r"附录X L(\d+) ◆([^◆]+)◆→([^；]+)")
HDR = re.compile(r"^【([^】·|]*?(?:汤|散|丸|饮|煎))[^】]*】")


def sections(E):
    """◆段名 -> (行号1起, 段全文)。同名段取首次出现。"""
    out = {}
    for i, l in enumerate(E):
        if not l.startswith("◆"):
            continue
        seg = l
        k = i + 1
        while k < len(E) and (E[k].startswith("  ") or E[k].startswith("|")) and E[k].strip():
            seg += E[k]
            k += 1
        name = re.sub(r"[（(].*?[)）]", "", re.sub(r"\*+", "", l).strip("◆").split("◆")[0])
        name = re.split(r"[：，,]", name)[0].strip()[:26]
        out.setdefault(name, (i + 1, seg))
    return out


def main(fix=False):
    E = open(ENGINE, encoding="utf-8").read().split("\n")
    secs = sections(E)
    bad_anchor = bad_member = bad_self = 0
    refs = 0
    changed = 0
    for i, l in enumerate(E):
        if MOUNT not in l:
            continue
        ent = None
        for j in range(i, -1, -1):
            m = HDR.match(E[j])
            if m:
                ent = m.group(1)
                break
        new = l
        for m in REF.finditer(l):
            refs += 1
            ln, name, others = int(m.group(1)), m.group(2), m.group(3)
            if name not in secs:
                bad_anchor += 1
                print("  段名查无此段: %s (条目%s)" % (name, ent))
                continue
            real, seg = secs[name]
            if real != ln:
                bad_anchor += 1
                if fix:
                    new = new.replace("附录X L%d ◆%s◆" % (ln, name),
                                      "附录X L%d ◆%s◆" % (real, name))
                    changed += 1
                else:
                    print("  行号失准: 条目%s ◆%s◆ 载L%d 实L%d" % (ent, name, ln, real))
            for nm in others.split("/"):
                if nm == "(同段内)":
                    continue
                if nm not in seg:
                    bad_member += 1
                    print("  对举方不在段内: 条目%s → %s ◆%s◆" % (ent, nm, name))
            if ent and ent not in seg:
                bad_self += 1
                print("  挂错方: 条目【%s】不在 ◆%s◆ 内" % (ent, name))
        if fix and new != l:
            E[i] = new
    if fix and changed:
        open(ENGINE, "w", encoding="utf-8").write("\n".join(E))
    print("回挂引用 %d ｜ 锚失准 %d%s ｜ 对举方缺失 %d ｜ 挂错方 %d"
          % (refs, bad_anchor, "(已修)" if fix and changed else "", bad_member, bad_self))
    return 0 if (bad_member == 0 and bad_self == 0 and (fix or bad_anchor == 0)) else 1


if __name__ == "__main__":
    sys.exit(main("--fix" in sys.argv))
