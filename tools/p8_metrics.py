"""协议8 指标脚本（互指完备率／出口覆盖率）。

【已知失效模式】(㉓批·复盘视角㉕ 强制格式)
  ① **子串匹配会与引擎内新增的标记文本撞车**——⑨批实测：分子用 `[★换源·X-0]`
     子串计数，与新加的主症★标记相撞，报出 98.8% 虚高(真值 98.5%)。
     故现版带**最长优先消费自验断言**；断言若被移除，指标立即不可信。
  ② 指标测的是**存量**(挂了多少边)，**不测通路**(从入口能否走到)。
     在库率 100% 时入口反查率仍可能很低——W-1.14 即此。
     **本工具不能用于回答"知识是否可达"**(须待 reachability 指标)。
  ③ 方名归属靠 C卷章节标题正则；OCR 变形名(小柴朐/茨苓)靠 fix 表硬修，
     **fix 表之外的变形一律漏**。
【弃件条件】
  章节标题解析不出方名者标 "?" 并计入未归属，**不按相邻条目猜测**(协议4)。
"""
import re
B="/home/user/claudecode-demo/"
E=open(B+"hxs_engine_v79_full.md",encoding="utf-8").read().split("\n")
C=open(B+"sources/C_jingfangliyu.txt",encoding="utf-8").read().split("\n")
sec=re.compile(r"^\s*[一二三四五六七八九十百]+\s*、\s*(\S.*?)\s*$")
fix={"麻黄杏仁薏苡苡甘草汤":"麻黄杏仁薏苡甘草汤","大黄蜃虫丸":"大黄蟅虫丸",
     "理中汤或丸":"理中汤","枳实薙白桂枝汤":"枳实薤白桂枝汤","八味丸（又名肾气丸）":"肾气丸"}
names=set()
for l in C:
    m=sec.match(l.strip())
    if m:
        n=re.sub(r"\s+","",m.group(1))
        if n.endswith("方") and len(n)<=20:
            n=n[:-1]
            if n not in ("何谓经","如何掌握经"): names.add(fix.get(n,n))
hdr=re.compile(r"^【([^】·|]*?(?:汤|散|丸|饮|煎))[^】]*】")
ents=[]
for i,l in enumerate(E):
    m=hdr.match(l)
    if m and "附录" not in l:
        ents.append((i,m.group(1))); names.add(m.group(1))
NAMES=sorted(names,key=len,reverse=True)

def extract(t,self_nm):
    """最长优先消费，避免 '当归四逆汤' 被误记为 '四逆汤' 边"""
    found=[]; s=t
    for n in NAMES:
        while n in s:
            s=s.replace(n," "*len(n),1)
            if n!=self_nm: found.append(n)
    return set(found)

# ---- 扫描器自验(指标脚本本身须验证·W-1.12教训) ----
a=extract("鉴别：vs当归四逆汤(血虚)；vs四逆汤(真寒)","通脉四逆汤")
assert a=={"当归四逆汤","四逆汤"}, a
b=extract("鉴别：vs当归四逆汤(血虚)","通脉四逆汤")
assert b=={"当归四逆汤"}, b
c=extract("鉴别：vs小柴胡汤","小柴胡汤")
assert c==set(), c
print("[自验] 最长优先消费/自指剔除 通过")

blocks=[]
for k,(i,nm) in enumerate(ents):
    end=ents[k+1][0] if k+1<len(ents) else len(E)
    blocks.append((nm,i+1,"\n".join(E[i:end])))
# 口径订正(⑨批):"反义：…→X汤"同样是出口——执行器锚错时据以转出。
# 但"反义：…→禁"不含方名，不构成出口，故反义行须实含他方名才计。
EXIT=re.compile(r"鉴别|vs|↔|不可混|相鉴|别于|误配|勿混|区别于|^反义[：:]")
we=0; E1=set(); noexit=[]
for nm,ln,body in blocks:
    seg="\n".join(l for l in body.split("\n") if EXIT.search(l))
    outs=extract(seg,nm) if seg else set()
    if not outs:
        noexit.append((nm,ln)); continue
    we+=1
    for o in outs: E1.add((nm,o))
print("\n【池A·方证条目级】")
print("  条目 %d ／ 有出口 %d = 出口覆盖率 %.1f%%"%(len(blocks),we,100*we/len(blocks)))
b1={tuple(sorted(e)) for e in E1 if (e[1],e[0]) in E1}
print("  有向边 %d ／ 双向 %d对 = 互指完备率 %.1f%%"%(len(E1),len(b1),100*2*len(b1)/len(E1)))

# ---- 池B:附录X 谱系/边表区 ----
st=[i for i,l in enumerate(E) if l.startswith("附录X·经方理论增量边表")]
st=st[0] if st else 0
XT=E[st:]
E2=set()
for line in XT:
    if not re.search(r"◆|\||↔|→|vs",line): continue
    fs=sorted(extract(line,None),key=len,reverse=True)
    for x in fs:
        for y in fs:
            if x!=y: E2.add(tuple(sorted((x,y))))
A1={tuple(sorted(e)) for e in E1}
print("\n【池B·附录X谱系/边表区】")
print("  共现对 %d"%len(E2))
print("  其中未出现在任何方证条目出口中的 = %d (%.1f%%)"%(len(E2-A1),100*len(E2-A1)/len(E2)))
print("\n【合池】全库无向对 %d ／ 其中条目级可见 %d = 条目可见率 %.1f%%"%(
    len(E2|A1),len(A1),100*len(A1)/len(E2|A1)))
open("/tmp/claude-0/-home-user-claudecode-demo/af7eb2ce-34ff-5188-99a8-44b28c14b7a2/scratchpad/noexit.txt","w",encoding="utf-8").write(
    "\n".join("%s L%d"%(n,l) for n,l in noexit))
print("\n无出口条目已写入 noexit.txt，共",len(noexit))
