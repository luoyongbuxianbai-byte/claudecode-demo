#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_validation_runtime_orthogonal.py —— validation/runtime 正交（120批·用户令十六）"""
import sys
R=[]
def ck(n,c,w=""):
    R.append((n,bool(c),w));print("%s %-44s %s"%("✅PASS" if c else "⛔FAIL",n,w))
import os,sys
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(B,'runtime'))
sys.path.insert(0,os.path.join(B,'compiler'))
from reference_evaluator import Evaluator,Case
from lint_rules import load_all
def r(vs,cs):return [{'rule_id':'V','proposition':'p','object':'O','scope':{'kind':'cross_scenario'},'antecedent':[{'observation':'X','required_state':'present'}],'rule_effect':'confirm','validation_status':vs,'source_layer':'L4_hu_theory','speaker_status':'hu_direct','text_status':'accepted','compile_status':cs}]
ck('V1 source_verified 不自动 confirmed',Evaluator(r('source_verified','support_only')).run(Case({'X':'present'}))['final_confirmed_count']==0)
ck('V2 candidate 不自动 confirmed',Evaluator(r('candidate','support_only')).run(Case({'X':'present'}))['final_confirmed_count']==0)
ck('V3 scope_verified+active 方 confirmed',Evaluator(r('scope_verified','active')).run(Case({'X':'present'}))['final_confirmed_count']==1)
ck('V4 IR 无 runtime_status 字段',all('runtime_status' not in x for x in load_all()))
ck('V5 患者无该观察项则不 confirmed',Evaluator(r('scope_verified','active')).run(Case({}))['final_confirmed_count']==0)

ok=sum(1 for _,c,_ in R if c)
print("\n%s：%d/%d 通过"%("validation/runtime 正交",ok,len(R)))
sys.exit(0 if ok==len(R) else 1)
