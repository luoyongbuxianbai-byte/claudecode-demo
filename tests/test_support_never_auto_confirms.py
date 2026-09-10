#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_support_never_auto_confirms.py —— support 永不自动确认（120批·用户令十六）"""
import sys
R=[]
def ck(n,c,w=""):
    R.append((n,bool(c),w));print("%s %-44s %s"%("✅PASS" if c else "⛔FAIL",n,w))
import os,sys
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(B,'runtime'))
from reference_evaluator import Evaluator,Case
def sup(n):return [{'rule_id':'S%d'%i,'proposition':'p','object':'O','scope':{'kind':'cross_scenario'},'antecedent':[{'observation':'X%d'%i,'required_state':'present'}],'rule_effect':'support','validation_status':'counterexample_audited','source_layer':'L4_hu_theory','speaker_status':'hu_direct','text_status':'accepted','compile_status':'support_only'} for i in range(n)]
for n in (2,5,100):
    r=Evaluator(sup(n)).run(Case({'X%d'%i:'present' for i in range(n)}))
    ck('SU support×%d → 不 confirmed'%n,r['final_confirmed_count']==0,'support_count=%d'%r['support_count'])
raw=open(os.path.join(B,'runtime','reference_evaluator.py'),encoding='utf-8').read()
code='\n'.join(l.split('#')[0] for l in raw.split('\n'))
ck('SU4 代码内无聚合升级式','support_count >=' not in code and 'len(out["supports"]) >=' not in code)

ok=sum(1 for _,c,_ in R if c)
print("\n%s：%d/%d 通过"%("support 永不自动确认",ok,len(R)))
sys.exit(0 if ok==len(R) else 1)
