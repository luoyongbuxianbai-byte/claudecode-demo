#!/usr/bin/env python3
"""留出集·遮盲件生成（路径1·医师亲跑）。

遮法＝**截断法**（⑰批改定）。
词典遮盲已实测失败：OCR 把药名写成「茉胡／茨苓／庭陈／泽沼／生娆」、把方名写成
「小柴朐汤／麻杏惧甘汤／桂校二越婢一汤」，**任何词典都漏，而残留即等于泄漏答案**。
故改为**在第一个「本次辨证结论或本次处方」标记处截断**，只留其前的病史／症状／舌脉。
不依赖任何词典，是本材料条件下唯一可靠的遮法。

保留：既往治疗及其反应（「曾服…不效」——那是医源史判据，A9 最高优先，非答案）。
产出：holdout/blind/批N.md（医师用，案号重编）｜_mapping/blind_map.json（揭盲用）
"""
import re, os, json
from collections import defaultdict

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CD = os.path.join(B, "holdout", "cases")
BD = os.path.join(B, "holdout", "blind")
MD = os.path.join(B, "holdout", "_mapping")
os.makedirs(BD, exist_ok=True)
mapping = json.load(open(os.path.join(MD, "mapping.json")))
fam = {it["id"]: it["fam"] for it in mapping["items"]}

JUNK = re.compile(r"http\S{0,60}|---第\d+页---|[A-Za-z0-9|/.]{6,}")
# 切点须尽可能早、尽可能全——⑰批实测：每放宽一处，就漏一种形态。
CUT = re.compile(
    r"证属|此为|辨为|诊为|证系|乃[一-鿿]{0,4}之证|属[一-鿿]{2,8}证"
    r"|方用|治以|拟用|治宜|宜与|治[之则]"
    r"|[为是即][^。，,]{0,8}[一-鿿]{2,14}[汤散丸煎]"          # 「为麻杏甘汤」「是小柴胡汤」
    r"|(?:与|予|投|用|处方|服)[^。，,]{0,4}[一-鿿]{2,14}[汤散丸煎]"
    r"|(?:胡老|朐老|冯老|老)[^。]{0,8}(?:处方|与|投|用|认为|当即|诊为)"
    r"|\d{1,4}\s*[克钱两]|[一二三四五六七八九十]\s*[钱两][^。]{0,2}[克钱两]"  # 剂量串起点
    r"|结果|二诊|三诊|复诊|上药服|药后"
    # ── v4 补（⑲批·医师查获：v3 只截处方与疗效，漏截辨证结论）──
    # ① 结论引导语
    r"|综合分析|中医辨证|辨证为|此属|此乃|据此辨|归纳[为如]"
    # ② 方向提示语（原作者已给出路径）
    r"|宗此法|与《?伤寒论》?第\s*\d+\s*条|所述机制"
    # ③ **六经名与病机结论词＝辨证语言，非症状语言**：一出现即结论段开始。
    #    这些书是「分析式」排版——症状后有一段逐条归纳（"脉弦滑，苔黄腻…阳明里实"），
    #    该归纳段已把症状映射到六经，等同答案，须整段截去。
    r"|太阳病?中?风?证|阳明|少阳|太阴|少阴|厥阴|合病|并病"
    r"|里实|里虚|表虚|表实|上热下寒|营卫不和|水饮内停|饮停|停饮|津伤|阳虚|阴虚|血虚|气虚")
GIVE = re.compile(r"(?:与|予|投|方用|治以|处方)[^。，,；;]{0,6}[一-鿿]{2,14}(?:汤|散|丸|饮|煎)[^。，,；;]{0,10}")


def mask(t):
    t = JUNK.sub("", t)
    c = [m.start() for m in CUT.finditer(t)]
    if c:
        t = t[:min(c)]
    t = re.sub(r"[，,。；;]{2,}", "。", t).strip("，,。；; ")
    return t + "\n\n〔本案之辨证结论、处方与疗效：已截去〕"


def gold(t):
    g = GIVE.findall(t)
    return "／".join(dict.fromkeys(x[:26] for x in g)) or "(未解析·揭盲时人工读原案)"


# ── 出件闸门（⑰批立）──
# 自动遮盲在本材料(重OCR)上连挫四法(量词/药名词典/标记截断/加严截断)，
# 每次都漏出新形态。故**不再调正则，改为闸门弃件**：遮后仍带泄漏或过短者一律弃。
# 依据：协议4「宁弃勿猜」。弃件登记于 blind_map.json 的 dropped 字段。
LEAK = re.compile(r"\d{1,4}\s*[克钱两]|证属|此为|此属|此乃|综合分析|中医辨证|辨证为"
                  r"|结果[：:]|[一-鿿]{2,12}[汤散丸煎](?!证)"
                  r"|太阳中风|阳明|少阳|太阴|少阴|厥阴|合病|并病"
                  r"|里实|里虚|表虚|表实|上热下寒|营卫不和|停饮|饮停|宗此法|所述机制")

def qualified(masked):
    if LEAK.search(masked):
        return False, "遮后仍带泄漏"
    if len(re.sub(r"[^一-鿿]", "", masked)) < 50:
        return False, "遮后过短(<50字)"
    return True, ""

byfam = defaultdict(list)
dropped = []
for f in sorted(os.listdir(CD)):
    ok, why = qualified(mask(open(os.path.join(CD, f), encoding="utf-8").read()))
    if not ok:
        dropped.append(dict(id=f[:-4], reason=why)); continue
    byfam[fam[f[:-4]]].append(f)
print("出件闸门：合格 %d ／ 弃 %d %s" % (sum(len(v) for v in byfam.values()), len(dropped),
                                    [d["id"] + ":" + d["reason"] for d in dropped]))
order = []
while any(byfam.values()):
    for k in list(byfam):
        if byfam[k]:
            order.append(byfam[k].pop(0))

NB = 5
bybatch = defaultdict(list)
for i, f in enumerate(order):
    bybatch[i % NB + 1].append(f)

bmap = []
for b, fs in sorted(bybatch.items()):
    L = ["# 留出盲测·第 %d 批（共 %d 批·v3 出件）" % (b + 5, NB), "",
         "> **给医师**：按引擎流通件逐案走查，原样回传 Schema（含拒绝／异常输出）。",
         "> **必须给出候选排序**（首选／次选／再次 ＋各自置信度 ＋决定性观察 ＋若观察为X则改选Y）。",
         "> **不确定就降置信度，不要不给排序**——「止方」已不是终态（R6·㉑批）。",
         "> 见红旗征象时：转诊建议与候选排序**并列输出**，不得以安全为由不做辨证（R6b）。",
         "> 案文出自 OCR，错别字与残缺处请按可读部分判断，读不出的部分**不要脑补**。", ""]
    for k, f in enumerate(fs, 1):
        raw = open(os.path.join(CD, f), encoding="utf-8").read()
        cid = "B%d-%d" % (b + 5, k)
        L += ["---", "", "## 案 %s" % cid, "", mask(raw), ""]
        bmap.append(dict(blind=cid, src_id=f[:-4], fam=fam[f[:-4]], gold=gold(raw)))
    open(os.path.join(BD, "批%d.md" % (b + 5)), "w", encoding="utf-8").write("\n".join(L))
    print("批%d：%d 案" % (b + 5, len(fs)))

json.dump(dict(n=len(bmap), dropped=dropped, items=bmap),
          open(os.path.join(MD, "blind_map.json"), "w"), ensure_ascii=False, indent=1)
print("\n遮盲件 %d 案／%d 批" % (len(bmap), NB))
