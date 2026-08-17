#!/usr/bin/env python3
"""案例库体系纯净复筛（R18③·㉘批立·㉙批首次执行）。

R18③：外部体系不得进入判断链；**案例检索层同样生效**——近邻案只取胡老/仲景体系内案例。

【已知失效模式】(视角㉕)
  ① 关键词命中**不等于**违规：胡老本人偶用"肝郁"一类字样作描述（R18②注：
     照录为原词，不得据以生成规则）。故本工具**只标记，不自动删**，
     判定须逐案看上下文——本文件的 DROP 名单是**人工核过的结果**，不是正则产物。
  ② 只扫 full 文本；若案文 OCR 把"卫分"写成变形字，漏检。
  ③ 不扫方名——"银翘散"这类非经方须靠方名白名单另查，本工具未做。
【弃件条件】见 DROP（逐案人工核实后登记，附理由）。
【口径】(视角㊱) 一案＝case_library.json 的一个 item；`python3 tools/case_purity.py --apply` 执行剔除。
"""
import json, re, os, sys
from collections import Counter
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(B, "case_layer", "case_library.json")
EXT = {"卫气营血": r"卫分|气分|营分|血分|卫气营血",
       "三焦辨证": r"上焦(?:湿|证|病)|中焦(?:湿|证|病)|下焦(?:湿|证|病)|三焦辨证",
       "温病学说": r"温病|湿温|春温|暑温|伏邪|伏暑|透热转气|凉营|清营",
       "脏腑辨证结论": r"肝郁|肝火|肝阳上亢|肝肾阴虚|脾虚|脾胃虚弱|脾失健运|肾阳虚|肾阴虚|心血不足|心脾两虚|肺气虚|肝血虚",
       "五运六气": r"运气|五运|司天|在泉"}
# ── 逐案人工核实后的判定（不是正则产物）──
DROP = {
 158361: "转引《袁文补医根》他人医案，判断句作「此是脾虚泄泻，法宜补中益土」"
         "——**脏腑辨证语言且非胡老案**，违 R18③＋R1闭卷",
 163670: "「诊断为伏暑型卫分重证」＋方用**银翘散**——**温病学说＋非经方**，违 R1闭卷",
}
KEEP = {31541: "胡老本人原话「实为肝郁偏实热之证」→大柴胡汤合桂枝茯苓丸茵陈蒿汤。"
               "**「肝郁」是胡老原词，非外部体系**。按 R18② 照录为原词，"
               "**不得据以生成规则**；案例保留，加标注。"}

d = json.load(open(P))
flag, hits = [], Counter()
for c in d["items"]:
    ws = [k for k, rx in EXT.items() if re.search(rx, c["full"])]
    if ws: hits.update(ws); flag.append((c, ws))
print("案例库 %d 案 ｜ 复筛命中 %d 案 %s" % (len(d["items"]), len(flag), dict(hits)))
for c, ws in flag:
    off = c["off"]
    verdict = "**剔除**：" + DROP[off] if off in DROP else ("保留：" + KEEP.get(off, "未裁"))
    print("  %s#%-7d %-24s [%s] %s" % (c["src"][:14], off, c["fang"], "/".join(ws), verdict))

if "--apply" in sys.argv:
    kept = [c for c in d["items"] if c["off"] not in DROP]
    for c in kept:
        if c["off"] in KEEP: c["r18_note"] = KEEP[c["off"]]
    d["items"] = kept; d["n"] = len(kept)
    d["r18_screen"] = dict(dropped=[dict(off=k, reason=v) for k, v in DROP.items()],
                           kept_with_note=[dict(off=k, note=v) for k, v in KEEP.items()])
    json.dump(d, open(P, "w"), ensure_ascii=False, indent=1)
    print("\n[已执行] 剔除 %d 案，库存 %d 案" % (len(DROP), len(kept)))
