#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_fail_closed.py —— legacy fail closed（120批·用户令十六）"""
import sys
R=[]
def ck(n,c,w=""):
    R.append((n,bool(c),w));print("%s %-44s %s"%("✅PASS" if c else "⛔FAIL",n,w))
import json,os,sys
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(B,'compiler'))
from lint_rules import load_all
from importlib import import_module
sys.path.insert(0,os.path.join(B,'runtime'))
C=json.load(open(os.path.join(B,'runtime','compiled_rules.json'),encoding='utf-8'))
RULES={r['rule_id']:r for r in load_all()}
ids={r['rule_id'] for r in C}
ck('F1 fail_closed 不进 runtime',all(RULES[i]['compile_status'] not in ('fail_closed','inactive','manual_review') for i in ids))
ck('F2 speaker uncertain 之硬门 fail_closed',all(r['compile_status'] in ('fail_closed','inactive') for r in RULES.values() if r.get('speaker_status')=='uncertain' and r['rule_effect'] in ('confirm','exclude','contraindicate')))
ck('F3 falsified 不进 runtime',all(RULES[i]['validation_status'] not in ('falsified_overbroad','rejected') for i in ids))
ck('F4 legacy Markdown 不进 runtime',all('rule_id' in r for r in C),'evaluator 只吃 compiled_rules.json')
ck('F5 NEC-TAIYANG-WUHAN 已 inactive',RULES['NEC-TAIYANG-WUHAN']['compile_status']=='inactive')

ok=sum(1 for _,c,_ in R if c)
print("\n%s：%d/%d 通过"%("legacy fail closed",ok,len(R)))
sys.exit(0 if ok==len(R) else 1)
