# -*- coding: utf-8 -*-
"""chapter_selfcheck.py 用的计量函数（独立版，只依赖 Python 3 标准库）。
从项目内部的 compare_mine_vs_orig.py 抽出 load_mine / analyze 及其词表，口径不变；
去掉了读取参考书原文的部分（仓库里不带原文），基准数字见 baseline_866.json。
"""
import re, json, statistics as st, collections, sys

WATER=re.compile(r'(\(本章完\)|（本章完）|更新不易|记得分享|记住我们网|最\+近\+章节|求月票|求双倍月票|阅读！)')
SEP=re.compile(r'^[\-—\*·…\.=＊~～\s]+$')

def load_mine(path,start):
    out=[]
    for i,line in enumerate(open(path,encoding='utf-8'),1):
        if i<start: continue
        s=line.strip().lstrip('\u3000').strip()
        if s: out.append((i,s))
    return out

def L(s): return len(re.sub(r'\s','',s))
QOPEN='“「"'; 
def is_dialog(s): return bool(re.search(r'[“「]',s))
def is_sys(s): return s.startswith('【')
def is_sep(s): return bool(SEP.match(s))
def quoted_chars(s): return sum(len(x) for x in re.findall(r'[“「]([^”」]*)[”」]',s))

BODY=['攥','发白','指节','发颤','颤抖','发抖','手抖','在抖','发紧','发麻','发虚','发酸','发软','发烫','胸口','指尖','掌心','手心','喉结','喉咙发','心跳','心脏','屏住呼吸','呼吸一滞','咬着嘴唇','咬了咬嘴唇','咬嘴唇','咬住嘴唇','脸红','脸颊发','耳根','眼眶','腿软','冷汗','冒汗','后背一凉','头皮发麻']
LIKE_EXCL=re.compile(r'(好像|想像|图像|偶像|录像|影像|画像|肖像|像素|头像|雕像|镜像|人像|塑像|佛像|不像话)')
SIMILE=['仿佛','如同','宛如','犹如','似的','好似','恍若','宛若','一般地']
EMO=['难过','伤心','失落','心疼','委屈','害怕','恐惧','慌','愤怒','生气','开心','高兴','兴奋','绝望','心酸','酸涩','后悔','遗憾','不甘','羡慕','嫉妒','感动','愧疚','紧张','怅然','惆怅','心寒','难受','欢喜','烦躁','不安','惊喜','尴尬','无力']
TURN=re.compile(r'(却|倒是|倒也|反而|偏偏|居然|竟然|竟|反倒)')
SUMUP=re.compile(r'(还挺|也算|总算|不过是|而已|罢了|才是|就是这样|连.{0,6}都|怪好看|比.{0,6}还)')
COLLOQ=['卧槽','好家伙','我靠','靠！','妈的','特么','尼玛','牛逼','傻B','谁懂','这谁顶得住','啊呸','嘿嘿','哈哈','呜呜','嗯哼','咳咳']
PART=['吧','呢','嘛','呀','啊','哦','喔','哈','咯','啦','呗']
BRANDS=['奔驰','宝马','宾利','爱马仕','劳力士','保时捷','法拉利','迈巴赫','LV','香奈儿','古驰','迪奥','卡地亚','浪琴','西铁城','五菱','百达翡丽','欧米茄','特斯拉','华为','苹果','iPhone','mate','茅台','星巴克','肯德基','麦当劳','拼多多','抖音','小红书','微信','淘宝','美团','奥迪','大G','巴宝莉','宝格丽','阿迪','耐克','路易威登','普拉达','雅诗兰黛','兰蔻']
CNNUM='零一二两三四五六七八九十百千万亿'
NUM=re.compile(r'(\d+(?:[.,:：]\d+)*%%?|[%s]{2,}|[%s](?=[点分元块万亿圜岁号层楼棚年月天个张次米斤平秒周遍趟页行步辆台瓶杯件]))'%(CNNUM,CNNUM))
MONEY=re.compile(r'(\d+(?:\.\d+)?|[%s]+)\s*(元|块|万|亿|圜|w|W|k|K)'%CNNUM)
CLOCK=re.compile(r'(\d{1,2}[:：]\d{2}|[%s\d]{1,3}点(?:[%s\d]{1,3}分|半|整)?|\d+月\d+[日号]|周[一二三四五六日])'%(CNNUM,CNNUM))
FUNC1=set('是没不有像从又也把在一每再先连')

def clauses(sent): return [c for c in re.split(r'[，、；,;]',sent) if c.strip()]
def sentences(p): return [x for x in re.split(r'[。！？!?…]+[”」]?',p) if x.strip()]

def parallel_hits(p):
    hits=[]
    for s in re.split(r'[。！？!?]',p):
        cs=[c.strip('“”「」 ') for c in clauses(s)]
        run=1
        for i in range(1,len(cs)):
            a,b=cs[i-1],cs[i]
            same = len(a)>=2 and len(b)>=2 and (a[:2]==b[:2] or (a[0]==b[0] and a[0] in FUNC1))
            run = run+1 if same else 1
            if run==3: hits.append('，'.join(cs[i-2:i+1]))
    hits+= ['从A到B，从C到D:'+m for m in re.findall(r'从[^，。]{1,6}到[^，。]{1,6}，从[^，。]{1,6}到[^，。]{1,6}',p)]
    return hits

def ending_type(p):
    """叙述段（非对话、非【】、≥2个分句）的最后一个分句分类。判定顺序：比喻>转折反差>评价总结>情绪词>其他"""
    cs=[c for c in re.split(r'[，、；。！？!?,;]',p) if c.strip()]
    if len(cs)<2: return None
    last=cs[-1]
    if LIKE_EXCL.sub('',last).count('像') or any(w in last for w in SIMILE): return '比喻收尾'
    if TURN.search(last): return '转折反差收尾'
    if SUMUP.search(last): return '评价总结收尾'
    if any(w in last for w in EMO): return '情绪词收尾'
    return '平叙收尾'

def analyze(paras, label, keep_lines=False):
    P=[(ln,s) for ln,s in paras if not is_sep(s)]
    seps=sum(1 for _,s in paras if is_sep(s))
    text=''.join(s for _,s in P); N=L(text); K=N/1000
    lens=[L(s) for _,s in P]
    nar=[(ln,s) for ln,s in P if not is_dialog(s) and not is_sys(s)]
    dia=[(ln,s) for ln,s in P if is_dialog(s)]
    sysp=[(ln,s) for ln,s in P if is_sys(s)]
    nl=[L(s) for _,s in nar]
    def pct(xs,f): return round(100*sum(1 for x in xs if f(x))/len(xs),1) if xs else 0
    def q(xs,p): xs=sorted(xs); return xs[min(len(xs)-1,int(p*len(xs)))]
    R=collections.OrderedDict()
    R['样本']=label; R['有效字数']=N; R['段数']=len(P); R['分隔行']=seps
    R['段长_均值']=round(st.mean(lens),1); R['段长_中位']=st.median(lens); R['段长_P90']=q(lens,.9)
    R['段长_变异系数']=round(st.pstdev(lens)/st.mean(lens),2)
    for name,f in [('≤10',lambda x:x<=10),('11-20',lambda x:11<=x<=20),('21-40',lambda x:21<=x<=40),('41-60',lambda x:41<=x<=60),('61-80',lambda x:61<=x<=80),('>80',lambda x:x>80)]:
        R['段长分布%_'+name]=pct(lens,f)
    R['叙述段_均长']=round(st.mean(nl),1) if nl else 0; R['叙述段_中位']=st.median(nl) if nl else 0
    R['叙述段>60字%']=pct(nl,lambda x:x>60)
    sl=[L(x) for _,s in nar for x in sentences(s)]
    R['叙述句_均长']=round(st.mean(sl),1); R['叙述句_每句逗号分句']=round(st.mean([len(clauses(x)) for _,s in nar for x in sentences(s)]),2)
    R['对话段占比%']=round(100*len(dia)/len(P),1); R['【】段占比%']=round(100*len(sysp)/len(P),1)
    R['引号内字数占比%']=round(100*sum(quoted_chars(s) for _,s in P)/N,1)
    dq=[len(x) for _,s in P for x in re.findall(r'[“「]([^”」]*)[”」]',s)]
    R['每句台词均长']=round(st.mean(dq),1) if dq else 0
    # 身体词
    BRE=re.compile('|'.join(sorted(map(re.escape,BODY),key=len,reverse=True)))  # 最长优先、不重叠
    bc=collections.Counter(BRE.findall(text)); 
    R['身体反应词/千字']=round(sum(bc.values())/K,2); R['身体词明细']={w:c for w,c in bc.most_common() if c}
    like=LIKE_EXCL.sub('',text).count('像'); sim=sum(text.count(w) for w in SIMILE)
    R['比喻词/千字']=round((like+sim)/K,2); R['比喻明细']={'像(已排除好像/偶像等)':like, **{w:text.count(w) for w in SIMILE if text.count(w)}}
    R['破折号——/千字']=round(len(re.findall(r'——|--',text))/K,2)
    R['省略号/千字']=round(len(re.findall(r'…+|\.{3,}',text))/K,2)
    R['不是…是/而是/千字']=round(len(re.findall(r'不是[^。！？]{1,20}[，,]\s*(而)?是',text))/K,2)
    R['“又”/千字']=round(text.count('又')/K,2)
    # 段末
    et=collections.Counter(); ehits=[]
    for ln,s in nar:
        t=ending_type(s)
        if t: et[t]+=1
        if t and t!='平叙收尾' and keep_lines: ehits.append((ln,t,s[-24:]))
    tot=sum(et.values())
    R['叙述段末分类(≥2分句的叙述段)']={k:f'{v} ({round(100*v/tot,1)}%)' for k,v in et.most_common()}
    R['段末金句或情绪总结%(比喻+转折+评价+情绪)']=round(100*(tot-et['平叙收尾'])/tot,1) if tot else 0
    ph=[(ln,h) for ln,s in P for h in parallel_hits(s)]
    R['三段式排比/对仗/千字']=round(len(ph)/K,2); R['三段式命中数']=len(ph)
    # 物质细节
    R['数字/千字']=round(len(NUM.findall(text))/K,2)
    R['金额/千字']=round(len(MONEY.findall(text))/K,2)
    R['钟点日期/千字']=round(len(CLOCK.findall(text))/K,2)
    bcount={b:text.count(b) for b in BRANDS if text.count(b)}
    R['真实品牌/千字']=round(sum(bcount.values())/K,2)
    # 口语与不规整
    R['网络口语粗口/千字']=round(sum(text.count(w) for w in COLLOQ)/K,2)
    R['语气词/千字(台词外)']=round(sum(re.sub(r'[“「][^”」]*[”」]','',s).count(w) for _,s in P for w in PART)/K,2)
    R['语气词/千字(全部)']=round(sum(text.count(w) for w in PART)/K,2)
    R['叙述段带！或？%']=pct([s for _,s in nar],lambda s:bool(re.search(r'[！？!?]',s)))
    R['≤4字超短段%']=pct(lens,lambda x:x<=4)
    R['台词半截(以……/——收)%']=pct([s for _,s in dia],lambda s:bool(re.search(r'(…|——)[”」]',s)))
    R['感叹号/千字']=round(len(re.findall(r'[！!]',text))/K,2)
    R['情绪词直说/千字']=round(sum(text.count(w) for w in EMO)/K,2)
    R['“穿过/穿了过去/穿过去”次数']=len(re.findall(r'穿(了)?过(去)?',text))
    if keep_lines:
        R['_我方段末命中行']=ehits; R['_我方排比命中行']=ph
        R['_我方>60字叙述段']=[(ln,L(s)) for ln,s in nar if L(s)>60]
        R['_我方身体词行']=[(ln,[w for w in BODY if w in s]) for ln,s in P if any(w in s for w in BODY)]
        R['_我方比喻行']=[(ln) for ln,s in P if LIKE_EXCL.sub('',s).count('像') or any(w in s for w in SIMILE)]
    return R

