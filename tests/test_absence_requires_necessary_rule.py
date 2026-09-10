#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_absence_requires_necessary_rule.py —— absent 须经必要规则（120批·用户令十六）"""
import sys
R=[]
def ck(n,c,w=""):
    R.append((n,bool(c),w));print("%s %-44s %s"%("✅PASS" if c else "⛔FAIL",n,w))
import os,sys
B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(B,'runtime'))
from reference_evaluator import Evaluator,Case
ck('AB1 无规则时 absent_explicit 不排除',Evaluator([]).run(Case({'X':'absent_explicit'}))['exclusion_count']==0)
def exc(vs,kind='cross_scenario'):return [{'rule_id':'E','proposition':'Y⇒X','object':'Y','scope':{'kind':kind},'antecedent':[{'observation':'X','required_state':'absent_explicit'}],'rule_effect':'exclude','validation_status':vs,'source_layer':'L4_hu_theory','speaker_status':'hu_direct','text_status':'accepted','compile_status':'active'}]
ck('AB2 validation 不足时不排除',Evaluator(exc('candidate')).run(Case({'X':'absent_explicit'}))['exclusion_count']==0)
ck('AB3 validation 达标方排除',Evaluator(exc('counterexample_audited')).run(Case({'X':'absent_explicit'}))['exclusion_count']==1)
ck('AB4 scope 不匹配则不排除',Evaluator(exc('counterexample_audited','standalone_pattern')).run(Case({'X':'absent_explicit'},composite=True))['exclusion_count']==0)
for st in ('unknown_not_asked','unknown_not_recorded','uncertain'):
    ck('AB5 %s 不排除'%st,Evaluator(exc('counterexample_audited')).run(Case({'X':st}))['exclusion_count']==0)

ok=sum(1 for _,c,_ in R if c)
print("\n%s：%d/%d 通过"%("absent 须经必要规则",ok,len(R)))
sys.exit(0 if ok==len(R) else 1)
