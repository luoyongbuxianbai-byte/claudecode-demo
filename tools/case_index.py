#!/usr/bin/env python3
"""【案例检索层】㉕批·角色反转：案例为生成器，规则为否决器。

裁决要点（上级㉕批）：引擎把验案拆成★/属性/边/签名，摧毁了完整推理链的格式塔。
本层把验案**以完整原文入库，不拆解**；六槽位签名降为**索引键**，不再充当规则替代。

本文件实现并**当场验收**：
  查询 = 案的**症状段**（判断句之前的部分——检索时我们只有症状，没有答案）
  库   = 其余各案的症状段（**留一法**，查询案本身剔出库外，无泄漏）
  答案 = 该案胡老实际所开之方
  问   = 最近邻案之方，是否就是胡老为本案所开之方？

**这是与规则路径可直接比较的同一金标准、同一批案。**
规则路径（tools/fang_signature.py）在同一 95 例上：CS 3.2%。

【已知失效模式】(视角㉕)
  ① 症状段＝判断句之前的全部文字，含人口学与病史。**人口学（年龄性别）会进入相似度**，
     构成与辨证无关的伪相似。已用 DEMO 正则剔除，但 OCR 变形者剔不干净。
  ② 相似度为字面 2-gram Jaccard ＋ 槽位签名 Jaccard 的加权和，**不做同义词归一**
     （"心下痞"vs"胃脘堵"字面不同）。故本层召回是**下界**；接附录U归一化后应更高。
  ③ 留一法只在**同一本书内**做，未跨书验证；C卷案例风格高度一致，
     **本数字不可外推为泛化准确率**（真泛化须用协议11 留出集，本工具不碰留出集）。
  ④ 合方/加味串按 `合|与` 切开取集合，**加味药物被忽略**（"猪苓汤加减"＝猪苓汤）。
【弃件条件】
  症状段 <30 字、或未解析出用方者，弃并计入 drop。
"""
import re, os, json
from collections import Counter

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(B, "state_layer")
CASE = os.path.join(B, "case_layer")
os.makedirs(CASE, exist_ok=True)
raw = open(os.path.join(B, "sources", "C_jingfangliyu.txt"), encoding="utf-8").read().split("\n")
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com|_")
DEMO = re.compile(r"[一-鿿]{1,3}某[，,、]?|(?:男|女)(?:性)?[，,、]?|\d{1,3}\s*岁|"
                  r"病历号[：:]?\s*\d+|门诊病历号[：:]?\s*\d+|\d{4}年\d{1,2}月\d{1,2}日|初诊日期|初诊")

# ── 复用 state_extract 的判断句与用方解析结果（同一份 _raw.json，保证两路可比）──
rec = {r["line"]: r for r in json.load(open(os.path.join(OUT, "_raw.json")))["recs"]}

idx = [i for i, l in enumerate(raw) if "【验案】" in l]
cases, drop = [], []
for i in idx:
    j = i + 1
    while j < len(raw) and "【" not in raw[j] and j - i < 22:
        j += 1
    full = JUNK.sub("", re.sub(r"\s+", "", "".join(raw[i:j]))).split("【验案】")[-1]
    r = rec.get(i + 1)
    if not r or r["fang"] == "(未解析)":
        drop.append((i + 1, "无判断句或未解析用方")); continue
    sym = full.split(r["text"])[0] if r["text"] in full else full
    sym = DEMO.sub("", sym)
    if len(re.sub(r"[^一-鿿]", "", sym)) < 30:
        drop.append((i + 1, "症状段过短")); continue
    cases.append(dict(line=i + 1, sym=sym, judge=r["text"], fang=r["fang"], full=full))

# ── 六槽位（含㉕批新增【时间节律】槽·锚§208日晡潮热／§240日晡所发热）──
COMP = {"病位": ["半表半里", "心下", "项背", "肌肤", "四肢", "少腹", "胸胁", "表", "里", "内", "外", "上", "下", "胸", "腹"],
        "正气载体": ["营卫", "津液", "胃气", "心气", "血", "气", "阳", "卫", "营"],
        "虚实态": ["俱虚", "不和", "失调", "不足", "虚", "实", "衰", "弱"],
        "寒热": ["恶寒", "发热", "潮热", "往来寒热", "化热", "寒", "热"],
        "病理产物": ["寒饮", "水饮", "停饮", "水气", "湿", "瘀", "痰", "饮", "宿食"],
        "动向": ["上冲", "上犯", "上扰", "上逆", "内停", "内盛", "外溢", "外郁", "流注", "内陷", "不降", "郁", "逆"],
        # ㉕批①：时间节律升为一级槽。锚：§208「日晡所发潮热」属阳明、§240「日晡所发热者属阳明」。
        # 实测 C卷 26 处命中。此前附录Y 只有"病程演变"，无日节律——真缺口。
        "时间节律": ["日晡", "午后", "傍晚", "入夜", "夜甚", "夜间", "平旦", "晨起", "食后", "饭后", "定时", "每日下午"]}
ORD = sorted([(g, w) for g in COMP for w in COMP[g]], key=lambda x: -len(x[1]))
JING = re.compile(r"太阳|阳明|少阳|太阴|少阴|厥阴")

def sig(s):
    t, out = JING.sub(lambda m: "\x01" * len(m.group()), s), set()
    for g, w in ORD:
        if w in t:
            out.add("%s:%s" % (g, w)); t = t.replace(w, "\x00" * len(w))
    return out

def grams(s):
    s = re.sub(r"[^一-鿿]", "", s)
    return {s[k:k + 2] for k in range(len(s) - 1)}

def jac(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0

for c in cases:
    c["g"], c["s"] = grams(c["sym"]), sig(c["sym"])

def norm(f):
    return set(x for x in re.split(r"合|与", re.sub(r"(加减|加味)$", "", f)) if x)

# ── 留一法检索验收 ──
W_SIG = 0.5      # 槽位签名权重；字面 2-gram 权重 1-W_SIG
res, rows = Counter(), []
for q in cases:
    lib = [c for c in cases if c is not q]
    sc = sorted(lib, key=lambda c: -((1 - W_SIG) * jac(q["g"], c["g"]) + W_SIG * jac(q["s"], c["s"])))
    top = sc[:3]
    gold = norm(q["fang"])
    k = ("CS首选命中" if gold & norm(top[0]["fang"]) else
         "PC前三命中" if any(gold & norm(t["fang"]) for t in top) else "未命中")
    res[k] += 1
    rows.append((q, k, top))

N = len(cases)
L = ["# 案例检索层·留一法验收（㉕批·角色反转后第一个真数）", "",
     "> **同一批案、同一金标准（胡老自己开的方），与规则路径直接可比。**", "",
     "| 路径 | CS 首选命中 | PC 前三内 | 未命中 |", "|---|---|---|---|",
     "| **规则路径**（六槽位签名 ⊆ 方★签名） | **3.2%** | 7.4% | 83.2% |",
     "| **案例检索路径**（本层·留一法） | **%.1f%%** | %.1f%% | %.1f%% |" % (
         100 * res["CS首选命中"] / N,
         100 * (res["CS首选命中"] + res["PC前三命中"]) / N,
         100 * res["未命中"] / N), "",
     "可测案例 %d ／ 弃件 %d（%s）" % (N, len(drop), Counter(d[1] for d in drop).most_common()), "",
     "> ⚠**本数不是泛化准确率**：留一法只在 C卷内做，C卷案例风格高度一致（失效模式③）。",
     "> 真泛化须用协议11 留出集，**本工具不碰留出集**（裁决四：检索库与测试集严格分离）。", "",
     "## 逐例", "", "| 出处 | 胡老实际用方 | 判定 | 最近邻案之方（前三） | 最近邻案之判断句 |", "|---|---|---|---|---|"]
for q, k, top in rows:
    L.append("| L%d | %s | %s | %s | %s |" % (
        q["line"], q["fang"], k, "／".join(t["fang"] for t in top), top[0]["judge"]))
open(os.path.join(CASE, "留一法验收.md"), "w", encoding="utf-8").write("\n".join(L))

# ── 案例库落盘（完整原文·不拆解）──
json.dump(dict(n=N, source="C_jingfangliyu", note="完整原文入库·不拆解（㉕批裁决一①）",
               items=[dict(line=c["line"], sym=c["sym"], judge=c["judge"], fang=c["fang"],
                           sig=sorted(c["s"]), full=c["full"]) for c in cases]),
          open(os.path.join(CASE, "case_index.json"), "w"), ensure_ascii=False, indent=1)

print("入库 %d ／ 弃 %d %s" % (N, len(drop), Counter(d[1] for d in drop).most_common()))
print("留一法：CS %d(%.1f%%) ｜ PC前三 %d(%.1f%%) ｜ 未命中 %d(%.1f%%)" % (
    res["CS首选命中"], 100 * res["CS首选命中"] / N,
    res["CS首选命中"] + res["PC前三命中"], 100 * (res["CS首选命中"] + res["PC前三命中"]) / N,
    res["未命中"], 100 * res["未命中"] / N))
print("对照·规则路径同批：CS 3.2% ｜ PC 7.4% ｜ 未命中 83.2%")
