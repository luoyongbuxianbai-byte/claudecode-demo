#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_rule_schema.py —— schema 合规（120批·用户令十六）"""
import sys
R=[]
def ck(n,c,w=""):
    R.append((n,bool(c),w));print("%s %-44s %s"%("✅PASS" if c else "⛔FAIL",n,w))
import json,os,sys
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(B,'compiler'))
from lint_rules import load_all,lint,ENUMS,REQUIRED
RULES=load_all();errs,warns=lint(RULES)
ck('S1 lint 无错',not errs,'%d 错'%len(errs))
ck('S2 每条必填齐',all(all(k in r for k in REQUIRED) for r in RULES))
ck('S3 enum 全合法',all(all(r.get(k) in v for k,v in ENUMS.items() if k in r) for r in RULES))
ck('S4 rule_id 唯一',len({r['rule_id'] for r in RULES})==len(RULES))
ck('S5 IR 不含 runtime_status',all('runtime_status' not in r for r in RULES))

ok=sum(1 for _,c,_ in R if c)
print("\n%s：%d/%d 通过"%("schema 合规",ok,len(R)))
sys.exit(0 if ok==len(R) else 1)
