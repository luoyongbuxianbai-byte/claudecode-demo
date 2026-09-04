#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paichu_yansuan.py —— 【排除演算器】(105批·上级以统帅位裁决之唯一任务)

## 立此器之由（上级 105批 裁决，逐字）
「一百零四批我们只采材料，未造机器。**执行核是路由表——告诉执行器『去哪查』，不告诉它『怎么算』。**
 而胡老排除法本身可机械执行……**足以跑一次完整排除演算，而一次都没跑过。**
 定方率百批不动，不是材料不够，**是没有机器在用材料。**」

## ⛔ 本器之三条铁律（皆有原文根据，非工程约定）

### 铁律一：只排除，不指派〔R96·闸门11〕
〔A·C卷·51288 等四书〕「必自下利」宜读作「**必须自下利者，才可用葛根汤主之**，
  而不是说太阳与阳明合病者**必定**自下利」。
⇒ **每条规则只能把候选项从活集中划掉，永远不能把某项标为「命中」。**

### 铁律二：三值，且「未采 ≠ 阴性」〔(51) 缺省不得推定〕
症状有三态：**显性阳性（病案写了有）｜显性阴性（病案写了无）｜未采（病案没提）**。
⇒ **「无X则非Y」只在 X 为「显性阴性」时触发。X 未采时，规则静默，不得触发。**
⛔ **这一条决定了本器的实际威力，也是本次测量的真正对象。**

### 铁律三：报余项，不报答案
输出是**排除后的活候选集**，不是诊断。三类结果各有意义：
  **余项＝1** → 排除法成立，现有条数于该案已够
  **余项＞1** → **缺口可量化**，且知道缺在哪一格
  **余项＝0** → **条件互斥，材料内部有矛盾，须报具体哪两条**

## ⛔ 条数之订正（105批·双向纪律，须先报再算）
上级令「用现有 **89** 条必要条件」。**核实：89 是人读总数，其中可用于病位排除者远少于此。**
  甲族病位 14｜乙族传变 8｜丙族方证 4｜丁族药味 23（绝对6/程度3/非X不可14）｜
  第〇节读法元规则 1｜第二节自我限制 3｜半表半里独立性论证 2 …… 合计 89 是**全部人读条数**。
**可直接参与「六经排除」演算者，只有甲族 14 ＋ 乙族 8 ＝ 22 条。**
**丁族 23 条作用于「方内某药之去留」，丙族 4 条作用于「某方是否成立」，皆非病位层，不入本演算。**
⇒ ⛔**本器实测之基数是 22，不是 89。不得以 89 之名报本测之结果。**

用法：python3 tools/paichu_yansuan.py            # 跑 T1–T5 并报三类结果
     python3 tools/paichu_yansuan.py --rules    # 只列规则表与覆盖度
"""
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 候选空间：胡老自己的构造 ── 病位三分 × 病性二分 ＝ 六格 ＝ 六经 ──
LIU = ["太阳", "阳明", "少阳", "太阴", "少阴", "厥阴"]
WEI = {"太阳": "表", "少阴": "表", "阳明": "里", "太阴": "里",
       "少阳": "半表半里", "厥阴": "半表半里"}
XING = {"太阳": "阳", "阳明": "阳", "少阳": "阳",
        "太阴": "阴", "少阴": "阴", "厥阴": "阴"}

# ── 症状三值抽取词表 ────────────────────────────────────
# 显性阴性优先于显性阳性匹配（「不恶寒」须先于「恶寒」判）
NEG = {  # 病案明写「无」者
    "恶寒": [r"不恶寒", r"无恶寒", r"不恶风寒"],
    "汗":   [r"无汗", r"不汗出", r"未汗出"],
    "渴":   [r"不渴", r"口不渴", r"不思饮"],
    "呕":   [r"不呕", r"无呕", r"不恶心"],
    "热":   [r"无热", r"不发热", r"身不热", r"热退", r"不热"],
    "大热": [r"无大热", r"身无大热"],
    "下利": [r"不下利", r"无下利", r"大便正常", r"清便欲自可", r"大便自调"],
    "气上冲": [r"无气上冲", r"无气冲"],
    "喘":   [r"不喘", r"无喘"],
    "厥":   [r"无厥", r"不厥", r"四肢温"],
    "小便不利": [r"小便清", r"小便自利", r"小便清长"],
}
POS = {  # 病案明写「有」者
    "恶寒": [r"恶寒", r"恶蹈", r"畏寒", r"恶风"],
    "汗":   [r"汗出", r"自汗", r"盗汗", r"有汗"],
    "渴":   [r"口渴", r"渴", r"思饮", r"口干思饮"],
    "呕":   [r"呕", r"恶心", r"欲吐"],
    "热":   [r"发热", r"发烧", r"身热", r"体温3[789]", r"潮热", r"热"],
    "大热": [r"大热", r"壮热", r"高热"],
    "下利": [r"下利", r"腹泻", r"便溏", r"日\d+行"],
    "气上冲": [r"气上冲", r"气冲", r"奔豚"],
    "喘":   [r"喘", r"咳喘", r"呼吸困难"],
    "厥":   [r"厥", r"四肢逆冷", r"手足逆冷", r"肢冷"],
    "往来寒热": [r"往来寒热", r"寒热往来", r"时有.{0,2}寒热", r"时寒时热"],
    "烦":   [r"心烦", r"烦躁", r"烦"],
    "小便不利": [r"小便.{0,2}少", r"小便不利", r"尿少", r"无尿"],
    "身疼": [r"身疼", r"身痛", r"身础", r"骨节疼", r"腰痛", r"身咤痛"],
    "胸胁苦满": [r"胸胁苦满", r"胁下.{0,2}满", r"右股痛", r"胁痛"],
}

# ── 规则表：每条 = (编号, 触发, 排除, 逐字原文, 锚, 族) ──────
# 触发形式：("neg", 症) 病案明写无此症｜("pos", 症) 病案明写有此症｜("and", [...]) 合取
R = [
    ("甲1", ("neg", "恶寒"), ["太阳"],
     "不恶寒者为温病……所以太阳病啊必须要恶寒", "讲伤寒·196590", "甲"),
    ("甲2", ("and", [("pos", "热"), ("neg", "恶寒")]), ["太阳", "少阴"],
     "邪进于表了就要怕冷……邪进于里则恶热，不恶寒", "讲伤寒·116589", "甲"),
    ("甲3", ("neg", "大热"), ["阳明·内结"],
     "热实于里身当大热，今无大热则未至阳明内结的热实程度", "C卷·46515", "甲"),
    ("甲4", ("neg", "小便不利"), ["阳明", "太阴"],
     "其小便清者，知不在里，仍在表也", "C卷·15592｜解读·82122", "甲"),
    ("甲5", ("and", [("neg", "喘"), ("neg", "身疼")]), ["太阴"],
     "平时无喘、吐痰、头痛、身疼等症，知不在太阴", "临床家·15979", "甲"),
    ("甲6", ("neg", "热"), ["少阳"],
     "虽处于半表半里，但无阳证，则不往来寒热", "伤寒论传真·88135", "甲"),
    ("甲7", ("and", [("pos", "厥"), ("pos", "汗")]), ["少阴"],
     "血不充于四末则厥，故少阴病厥者必无汗", "讲伤寒·292003", "甲"),
    ("甲8", ("neg", "气上冲"), ["太阳"],
     "若无气上冲感觉者，说明邪已陷于里，此时就不能再给服桂枝汤了",
     "解读·79840｜传真系·12633", "甲"),
    ("甲9", ("and", [("neg", "热"), ("pos", "恶寒")]), ["太阳", "阳明", "少阳"],
     "发汗后……若无热而恶寒者，是已陷于阴虚证", "C卷·71721", "甲"),
    ("乙1", ("neg", "呕"), ["少阳"],
     "其人不呕，则未传入少阳", "伤寒论传真·51859｜病位类方解·79751", "乙"),
    ("乙2", ("neg", "下利"), ["阳明"],
     "清便欲自可，则未传入阳明", "伤寒论传真·51872", "乙"),
    ("乙3", ("neg", "渴"), ["阳明"],
     "不渴，则未传阳明", "伤寒论传真·103597", "乙"),
    ("乙4", ("and", [("neg", "恶寒"), ("pos", "渴")]), ["太阳"],
     "其人已不复恶寒而渴者，此表证已罢而转属阳明", "C卷·42155", "乙"),
]

# ⛔ 未编码者（如实记，防后批以为已全）：
UNCODED = [
    ("甲·太阳伤寒必喘", "讲金匮·84482", "须先判是否伤寒（表实），单症无法定，故不可机械编码"),
    ("甲·无热则不烦", "伤寒论传真·88135", "结论为「不烦」而非某病位，属症-症关系，不排除候选"),
    ("甲·无汗则不恶风", "伤寒论传真·39911", "同上，症-症关系"),
    ("甲·太阳伤寒必恶寒（较中风显著）", "讲伤寒·5483", "程度式（「明显显著」），无客观阈值，不可编码"),
    ("乙·无太阳证则表已罢", "解读·179148", "「太阳证」为证候群非单症，须先有定太阳之法，循环依赖"),
    ("乙·无柴胡证则未传少阳", "解读·179158", "同上，「柴胡证」为证候群"),
    ("乙·表证已罢（脉迟身凉）", "伤寒论传真·93169", "须脉诊数据，本测五案脉象记载不全"),
    ("乙·柴胡证已罢（误治后谵语）", "C卷·111735", "须误治史，本测五案无"),
]


def tri(txt, sym):
    """三值判定：-1 显性阴性｜+1 显性阳性｜0 未采。⛔阴性优先。"""
    for p in NEG.get(sym, []):
        if re.search(p, txt):
            return -1
    for p in POS.get(sym, []):
        if re.search(p, txt):
            return 1
    return 0


def fire(txt, trig):
    """规则是否触发。⛔未采时一律不触发〔(51)〕。"""
    k = trig[0]
    if k == "neg":
        return tri(txt, trig[1]) == -1
    if k == "pos":
        return tri(txt, trig[1]) == 1
    if k == "and":
        return all(fire(txt, t) for t in trig[1])
    return False


def run(name, txt):
    alive = set(LIU)
    fired, killed = [], {}
    for rid, trig, out, quote, anchor, fam in R:
        if not fire(txt, trig):
            continue
        real = [o for o in out if o in alive]
        sub = [o for o in out if "·" in o]       # 亚项（如「阳明·内结」）不减候选
        fired.append((rid, out, quote, anchor))
        for o in real:
            alive.discard(o)
            killed.setdefault(o, []).append(rid)
        if sub:
            fired[-1] = (rid, out, quote + "〔⚠亚项排除，不减六经候选〕", anchor)
    return alive, fired, killed



def wenzhen(txt, alive):
    """⭐⭐⭐ 问诊生成器（105批·排除演算之逆用）

    排除演算在 T1–T5 上零触发，根因是「显性阴性」几乎不存在于医案（实测 1/75 ＝ 1.3%）。
    ⇒ 医案只记阳性；胡老的排除法在诊室能用，因为他能当面问，而问诊之「问了而无」写不进医案。
    ⇒ **故本器之正确用法不是「看案定方」，是「看案出问题清单」**：
       余项 > 1 时，反查规则表——**哪几项若问出「无」，就能划掉哪几个候选。**
       这既是排除法的自然用法，也是引擎唯一能在医案语料上真正做到的事。
    """
    want = {}
    for rid, trig, out, quote, anchor, fam in R:
        hit = [o for o in out if o in alive]
        if not hit:
            continue
        need = []
        def collect(t):
            if t[0] in ("neg", "pos"):
                need.append((t[1], t[0]))
            elif t[0] == "and":
                for x in t[1]:
                    collect(x)
        collect(trig)
        # 只列「现为未采」者——已知者无须再问
        ask = [(s, k) for s, k in need if tri(txt, s) == 0]
        if not ask:
            continue
        for s, k in ask:
            want.setdefault(s, {"rules": set(), "kills": set(), "need": k})
            want[s]["rules"].add(rid)
            want[s]["kills"].update(hit)
    rows = sorted(want.items(), key=lambda x: -len(x[1]["kills"]))
    return rows


def symtab(txt):
    all_sym = sorted(set(list(NEG) + list(POS)))
    return [(s, tri(txt, s)) for s in all_sym]


def main():
    if "--rules" in sys.argv:
        print("== 规则表（可参与六经排除者）==")
        for rid, trig, out, q, a, f in R:
            print("  %-4s %-46s → 排除 %s" % (rid, q[:44], "／".join(out)))
        print("\n合计 **%d** 条已编码。" % len(R))
        print("\n== ⛔ 未能编码者（%d 条）==" % len(UNCODED))
        for n, a, why in UNCODED:
            print("  %-30s 〔%s〕%s" % (n, a, why))
        cov = {}
        for rid, trig, out, q, a, f in R:
            for o in out:
                cov[o.split("·")[0]] = cov.get(o.split("·")[0], 0) + 1
        print("\n== 六经覆盖度（每格有几条必要条件可排除它）==")
        for j in LIU:
            n = cov.get(j, 0)
            print("  %-4s %s %d 条" % (j, "⛔零条！" if n == 0 else "✅", n))
        return 0

    files = sorted(f for f in os.listdir(os.path.join(B, "blind_test"))
                   if re.match(r"T\d+\.txt$", f))
    print("== 排除演算 · %d 案 ==\n" % len(files))
    tally = {"唯一": [], "多于一": [], "为零": []}
    for f in files:
        txt = open(os.path.join(B, "blind_test", f), encoding="utf-8").read()
        alive, fired, killed = run(f[:-4], txt)
        st = symtab(txt)
        npos = sum(1 for _, v in st if v == 1)
        nneg = sum(1 for _, v in st if v == -1)
        nunk = sum(1 for _, v in st if v == 0)
        print("── %s ──" % f[:-4])
        print("  症状三值：显性阳性 %d｜**显性阴性 %d**｜未采 %d（共 %d 项）"
              % (npos, nneg, nunk, len(st)))
        print("  显性阴性项：%s" % ("、".join(s for s, v in st if v == -1) or "⛔无——则无一条规则可触发"))
        print("  触发规则 %d 条：%s" % (len(fired), "、".join(r[0] for r in fired) or "无"))
        for rid, out, q, a in fired:
            print("     %s 〔%s〕「%s」→ 排除 %s" % (rid, a, q[:34], "／".join(out)))
        order = [j for j in LIU if j in alive]
        print("  **余项 %d：%s**" % (len(order), "、".join(order) or "（空）"))
        k = "唯一" if len(order) == 1 else ("为零" if not order else "多于一")
        tally[k].append((f[:-4], order, len(fired)))
        if len(order) > 1:
            wz = wenzhen(txt, alive)
            print("  ⭐**须问诊 %d 项**（问出「%s」即可划掉对应候选）：" % (len(wz), "无"))
            for s_, d in wz[:8]:
                print("     问「%s」%s → 若答『%s』可排除：%s〔规则 %s〕"
                      % (s_, "有无" if d["need"] == "neg" else "有无",
                         "无" if d["need"] == "neg" else "有",
                         "、".join(sorted(d["kills"])), "/".join(sorted(d["rules"]))))
        print()
    print("== 三类结果 ==")
    for k in ["唯一", "多于一", "为零"]:
        print("  %-4s %d 案 %s" % (k, len(tally[k]),
              "｜".join("%s(余%d)" % (n, len(o)) for n, o, _ in tally[k])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
