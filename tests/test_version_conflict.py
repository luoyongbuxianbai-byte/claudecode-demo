#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_version_conflict.py —— L5 不覆盖 L4（120批·用户令十六）"""
import sys
R=[]
def ck(n,c,w=""):
    R.append((n,bool(c),w));print("%s %-44s %s"%("✅PASS" if c else "⛔FAIL",n,w))
import os,sys
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(B,'compiler'))
from lint_rules import load_all,lint
RULES={r['rule_id']:r for r in load_all()}
j=RULES['JUEYIN-SHANGREXIAHAN']
ck('X1 L5 与 L4 冲突 → disputed',j['text_status']=='disputed')
ck('X2 冲突者不得 active',j['compile_status']!='active')
ck('X3 两造皆保留',any('C卷·12662' in c['ref'] for c in j['counterexamples']) and '解读·261497' in j['source_refs'])
bad=[{'rule_id':'BAD','proposition':'p','object':'O','scope':{'kind':'cross_scenario'},'antecedent':[{'observation':'X','required_state':'present'}],'rule_effect':'confirm','validation_status':'scope_verified','source_layer':'L5_editorial','speaker_status':'editorial','text_status':'accepted','compile_status':'active'}]
e,_=lint(bad)
ck('X4 lint 拦截 L5 硬门 active',any('锁5' in m for _,m in e),'%d 错'%len(e))
t=RULES['NEC-TAIYANG-WUHAN']
ck('X5 §172 两读皆挂且 disputed',t['text_status']=='disputed' and len(t['counterexamples'])==2)

ok=sum(1 for _,c,_ in R if c)
print("\n%s：%d/%d 通过"%("L5 不覆盖 L4",ok,len(R)))
sys.exit(0 if ok==len(R) else 1)
