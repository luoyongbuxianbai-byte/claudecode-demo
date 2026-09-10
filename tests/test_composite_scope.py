#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_composite_scope.py —— composite scope（120批·用户令十六）"""
import sys
R=[]
def ck(n,c,w=""):
    R.append((n,bool(c),w));print("%s %-44s %s"%("✅PASS" if c else "⛔FAIL",n,w))
import os,sys
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(B,'runtime'))
from reference_evaluator import Evaluator,Case
def r(kind):return [{'rule_id':'C','proposition':'p','object':'O','scope':{'kind':kind},'antecedent':[{'observation':'X','required_state':'present'}],'rule_effect':'confirm','validation_status':'scope_verified','source_layer':'L4_hu_theory','speaker_status':'hu_direct','text_status':'accepted','compile_status':'active'}]
ck('C1 standalone 不作用于 composite',Evaluator(r('standalone_pattern')).run(Case({'X':'present'},composite=True))['final_confirmed_count']==0)
ck('C2 standalone 作用于非 composite',Evaluator(r('standalone_pattern')).run(Case({'X':'present'}))['final_confirmed_count']==1)
ck('C3 composite_component 可作用于 composite',Evaluator(r('composite_component')).run(Case({'X':'present'},composite=True))['final_confirmed_count']==1)

ok=sum(1 for _,c,_ in R if c)
print("\n%s：%d/%d 通过"%("composite scope",ok,len(R)))
sys.exit(0 if ok==len(R) else 1)
