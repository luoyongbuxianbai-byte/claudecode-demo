import re,os
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}")
BOOKS=[("C卷","C_jingfangliyu.txt"),("讲伤寒","ocr_未识别2.txt"),("讲金匮","ocr_未识别1.txt"),
("解读","ocr_解读张仲景医学.txt"),("传真系","ocr_经方传真系.txt"),("病位类方解","ocr_胡希恕病位类方解.txt"),
("临床家","ocr_中医临床家胡希恕.txt"),("带教","ocr_冯世纶带教实录第一辑.txt"),("汤液经方系","ocr_冯世纶2005汤液经方系_书名待定.txt"),
("伤寒论传真","传真_伤寒论传真.txt"),("金匮要略传真","传真_金匮要略传真.txt"),("中国汤液方证","汤液_中国汤液方证.txt")]
T={}
for bk,fn in BOOKS:
    p=os.path.join("sources",fn)
    T[bk]=JUNK.sub("", re.sub(r"\s+","",open(p,encoding="utf-8",errors="ignore").read()))
def find(q,ctx=0,limit=4):
    tot=0; out=[]
    for bk in T:
        for m in re.finditer(re.escape(q),T[bk]):
            tot+=1
            if len(out)<limit:
                s=max(0,m.start()-ctx); out.append((bk,m.start(),T[bk][s:m.start()+len(q)+ctx]))
    return tot,out
