#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fang_compose.py —— 由 C卷【方剂组成】抽方剂组成表（106批·统一演算器之方库）
⛔只做集合，不含量〔附录I 同限〕：桂枝加桂汤与桂枝汤在集合上相同，其别在量。
  故本表不可用于「量」之判断——量之判据见 tongyi_yansuan.py ⑤剂量路。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus_guard import load_one
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "state_layer", "方剂组成.json")
YAO = (r"(桂枝|芍药|甘草|生姜|大枣|麻黄|杏仁|石膏|柴胡|黄芩|半夏|人参|干姜|附子|白术|苍术|"
       r"茯苓|泽泻|猪苓|大黄|芒硝|厚朴|枳实|栀子|黄连|黄柏|当归|川芎|地黄|阿胶|细辛|五味子|"
       r"吴茱萸|龙骨|牡蛎|葛根|瓜蒌|栝蒌|贝母|桔梗|防己|黄芪|薏苡仁|桃仁|丹皮|知母|竹叶|"
       r"旋覆花|代赭石|滑石|车前子|乌梅|川椒|蜀漆|皂荚|葶苈子|射干|紫菀|款冬花|白头翁|"
       r"秦皮|赤石脂|禹余粮|升麻|鳖甲|水蛭|虻虫|大戟|甘遂|芫花|巴豆|瓜蒂|赤小豆)")
def main():
    c = load_one("C卷")
    rows = re.findall(r"([一-鿿]{2,14}(?:汤|散|丸|饮))方?\s*【方剂组成】([^【]{4,240})", c)
    F = {}
    for name, comp in rows:
        ys = sorted(set(x.replace("栝蒌", "瓜蒌") for x in re.findall(YAO, comp)))
        if ys:
            F.setdefault(name, ys)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(F, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("【方剂组成】块 %d ｜可解析 %d 方 → %s" % (len(rows), len(F), OUT))
    assert len(F) > 150, "⛔抽取量骤减，疑正则失效"
    assert "桂枝" in F.get("桂枝汤", []), "⛔自检失败：桂枝汤无桂枝"
    print("[自检] 桂枝汤含桂枝 ✅｜方数 >150 ✅")
    return 0
if __name__ == "__main__":
    sys.exit(main())
