# -*- coding: utf-8 -*-
"""单章硬指标自检（写作纪律 第9节硬指标＋第10节启发式；阈值来自 references/我的写法vs真人写法_全书版.md 第五、六节）。
独立版：只需 Python 3.8+ 标准库；同目录需有 selfcheck_metrics.py；baseline_866.json 可选（缺了用内置同一组数字）。
基准：参考书全书 1–866 章去重统计，只含数字，不含原文。

用法（在仓库根目录）：
  python3 scripts/chapter_selfcheck.py 正文/第003章-交付版.md        # 自动从“第N章”标题下一行起算
  python3 scripts/chapter_selfcheck.py 章.md --start 4               # 手动指定正文起始行（1起）
  python3 scripts/chapter_selfcheck.py a.md b.md --no-color          # 多章；写进文件时关颜色（--color 强制标红）
  python3 scripts/chapter_selfcheck.py 章.md --json                  # 机器可读
退出码：0=全部达标；1=有超标项（便于在流程里卡住）。
说明：脚本只量“能数的东西”；R23骨架重复、R24说停就停等仍要人读。指标达标不等于写得好，只是交三组审核前的底线。
"""
import sys, os, re, json, argparse, collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import selfcheck_metrics as C

FALLBACK={'叙述段_均长':23.2,'叙述段>60字%':1.0,'叙述句_每句逗号分句':2.24,'身体反应词/千字':0.76,'“又”/千字':1.34,
          '不是…是/而是/千字':0.04,'段末金句或情绪总结%(比喻+转折+评价+情绪)':6.7,'语气词/千字(全部)':3.64,
          '感叹号/千字':3.82,'叙述段带！或？%':5.7,'情绪词直说/千字':1.19,'章首段':17.0,'章末段':22.9}
def baseline():
    b=dict(FALLBACK); p={}
    f=os.path.join(HERE,'baseline_866.json')
    if os.path.exists(f):
        d=json.load(open(f,encoding='utf-8'))
        r=[x for x in d['res'] if x['样本']=='原书1-866全量去重'][0]
        for k in b:
            if k in r: b[k]=r[k]
        p=d.get('percentile',{})
    return b,p

# (显示名, analyze键或特殊键, 方向, 阈值, 规则号)  方向: '<=' 上限, '>=' 下限, 'in' 区间
CHECKS=[
 ('叙述段均长(字)',            '叙述段_均长',            'in',(21,26),'R1'),
 ('>60字叙述段占比%',          '叙述段>60字%',           '<=',2.6,'R1'),
 ('>60字叙述段个数(按2500字折算)','_n60',                '<=',1,'R1'),
 ('每句逗号分句',              '叙述句_每句逗号分句',     '<=',2.5,'R2'),
 ('单句最多分句',              '_maxcl',                 '<=',4,'R2'),
 ('身体词/千字',               '身体反应词/千字',         '<=',1.1,'R3'),
 ('同一身体词全章最多次数',     '_bodymax',               '<=',1,'R3'),
 ('情绪词直说/千字',           '情绪词直说/千字',         'in',(0.4,2.0),'R4'),
 ('“又”/千字',                 '“又”/千字',              '<=',2.2,'R9'),
 ('段末金句率%',               '段末金句或情绪总结%(比喻+转折+评价+情绪)','<=',10,'R7'),
 ('“不是…，是”次数',           '_bushi',                 '<=',1,'R8'),
 ('章首第一段(字)',            '_head',                  '<=',18,'R20'),
 ('章末最后一段(字)',          '_tail',                  '<=',22,'R21'),
 ('语气词/千字(全部)',          '语气词/千字(全部)',       '>=',2.0,'R16'),
 ('感叹号/千字',               '感叹号/千字',             '>=',1.3,'R16'),
 ('叙述段带！或？%',            '叙述段带！或？%',          '>=',3.0,'R16'),
]
BASEKEY={'_head':'章首段','_tail':'章末段','_bushi':'不是…是/而是/千字'}

# --- §10 可脚本化启发式（风格草案「§自检脚本可新增指标」；【待用户阅读反馈】）---
# 只做关键词／句式粗检，命中＝提醒人读，不等于定罪。太主观的项见文件末 TODO。
IDFACE_PAT = re.compile(
    r'(我(?:就是|可是|正是).{0,12}(?:总裁|董事长|少爷|大小姐|继承人|会长|董事)|'
    r'(?:全场|在场|众人|宾客).{0,8}(?:震惊|哗然|寂静|倒吸)|'
    r'(?:脸(?:都)?(?:发白|煞白|苍白)|脸色大变|腿软))'
)
FORMULA_BREAK_PAT = re.compile(
    r'(?:电话(?:突然|忽然)?(?:响|来了)|手机(?:突然|忽然)?(?:响|震动)|系统(?:提示|弹窗|语音)|'
    r'外敌(?:突袭|袭击)|评级(?:弹窗|提示)|倒计时(?:面板|弹窗))'
)
# 章末主题总结：末段含「原来／其实／这一刻他才明白／意义在于」类收束
ENDING_SUMMARY_PAT = re.compile(
    r'(?:原来如此|这一刻.{0,6}才(?:明白|懂|知道)|意义在于|不禁感慨|他终于明白|'
    r'这一切都是|所谓的.{0,8}不过是)'
)
# 硬钩迹象（末2段）vs 软着陆（末段更短／语气缓和）
HARD_HOOK_PAT = re.compile(r'(?:会死|杀了|血|尸体|枪声|爆炸|门被撞开|救命|不——|！{2,}|危险)')
SOFT_LAND_PAT = re.compile(r'(?:先|慢慢|暂时|回去|明天|先这样|算了|深呼吸|水|茶|坐下来)')
# 同意边界粗检：亲密语境下出现停／不要后，后文仍有继续身体接触词 → warn（人读确认）
INTIMACY_PAT = re.compile(r'(?:吻|嘴唇|胸|腰|腿|抱紧|压[在下]|解开|褪|喘|呼吸紊乱|贴[近着]|手指(?:滑|探|伸))')
STOP_PAT = re.compile(r'(?:停下|说停就停|不要了|别这样|放开我|够了|我不想)')
CONTINUE_PAT = re.compile(r'(?:继续|又吻|再次|仍旧|还是(?:抱|吻|压)|不顾|没有停)')
# 章末钩子类型粗分（单章报告类型；跨章同型连续需另账）
HOOK_TYPES = [
    ('认知裂口', re.compile(r'(?:原来|不对|不是这样|她才发现|他才知道|怎么会)')),
    ('决断句', re.compile(r'(?:决定|必须|不能再|从此|就这样办|我选)')),
    ('选择钩', re.compile(r'(?:还是|或者|要不要|选哪|怎么办)')),
    ('威胁钩', re.compile(r'(?:会死|杀|血|枪声|爆炸|倒计时|来不及)')),
    ('半句残响', re.compile(r'(?:……|…$|——$|他说|她说|听见)')),
    ('时间戳', re.compile(r'(?:凌晨|三点|分钟后|第二天|那天|日后)')),
    ('物件位移', re.compile(r'(?:门|钥匙|戒指|信封|照片|杯子|手机).{0,8}(?:掉|移|放|落|不见|还在)')),
    ('跳切空景', re.compile(r'(?:窗外|走廊|空无一人|灯灭|只剩|安静)')),
]


def find_start(path):
    lines=open(path,encoding='utf-8').read().split('\n')
    for i,l in enumerate(lines[:12],1):
        if re.match(r'^\s*#*\s*第\s*\d+\s*章',l.strip()): return i+1
    return 1

def measure(path,start=None):
    st=start or find_start(path)
    paras=C.load_mine(path,st)
    paras=[(ln,s) for ln,s in paras if not s.startswith('状态：')]
    R=C.analyze(paras,os.path.basename(path),keep_lines=True)
    P=[(ln,s) for ln,s in paras if not C.is_sep(s)]
    text=''.join(s for _,s in P)
    nar=[(ln,s) for ln,s in P if not C.is_dialog(s) and not C.is_sys(s)]
    n60=[(ln,C.L(s)) for ln,s in nar if C.L(s)>60]
    R['_n60_raw']=len(n60); R['_n60']=round(len(n60)*2500/max(R['有效字数'],1),1); R['_n60_lines']=n60
    cl=[(ln,len(C.clauses(x))) for ln,s in nar for x in C.sentences(s)]
    R['_maxcl']=max((c for _,c in cl),default=0); R['_maxcl_lines']=[ln for ln,c in cl if c>4]
    bd=R.get('身体词明细',{}); R['_bodymax']=max(bd.values(),default=0)
    R['_bushi_lines']=[ln for ln,s in P if re.search(r'不是[^。！？]{1,20}[，,]\s*(而)?是',s)]
    R['_bushi']=len(re.findall(r'不是[^。！？]{1,20}[，,]\s*(而)?是',text))
    R['_head']=C.L(P[0][1]); R['_head_ln']=P[0][0]
    R['_tail']=C.L(P[-1][1]); R['_tail_ln']=P[-1][0]
    R['_start']=st
    # §10 启发式（不进 CHECKS 硬阈值；报告区单独列出）
    id_hits=[(ln,s) for ln,s in P if IDFACE_PAT.search(s)]
    fb_hits=[(ln,s) for ln,s in P if FORMULA_BREAK_PAT.search(s)]
    R['_idface']=len(id_hits); R['_idface_lines']=[ln for ln,_ in id_hits]
    R['_formula']=len(fb_hits); R['_formula_lines']=[ln for ln,_ in fb_hits]
    tail_s=P[-1][1] if P else ''
    R['_ending_summary']=1 if ENDING_SUMMARY_PAT.search(tail_s) else 0
    # 硬钩后软着陆：末两段有硬钩词且末段更短或含缓和词 → ok；有硬钩且末段仍硬且长 → warn
    last2=''.join(s for _,s in P[-2:]) if len(P)>=2 else tail_s
    hard=bool(HARD_HOOK_PAT.search(last2))
    soft=bool(SOFT_LAND_PAT.search(tail_s)) or (R['_tail']<=22 and not HARD_HOOK_PAT.search(tail_s))
    if hard and soft: R['_soft_land']='ok_soft_after_hard'
    elif hard and not soft: R['_soft_land']='warn_hard_no_soft'
    else: R['_soft_land']='n/a'
    # 同意边界粗检
    consent_warn=[]
    for i,(ln,s) in enumerate(P):
        if STOP_PAT.search(s) and (INTIMACY_PAT.search(s) or (i>0 and INTIMACY_PAT.search(P[i-1][1]))):
            nxt=''.join(x for _,x in P[i+1:i+4])
            if CONTINUE_PAT.search(nxt) or INTIMACY_PAT.search(nxt):
                consent_warn.append(ln)
    R['_consent_warn']=len(consent_warn); R['_consent_lines']=consent_warn
    # 章末钩子类型（末段；可多标）
    hooks=[name for name,pat in HOOK_TYPES if pat.search(tail_s)]
    R['_hook_types']=hooks or ['未识别']
    return R

def ok(v,d,t):
    if d=='<=': return v<=t
    if d=='>=': return v>=t
    return t[0]<=v<=t[1]

def report(R,b,pct,color=True):
    red=(lambda s:'\033[31m'+s+'\033[0m') if color else (lambda s:s)
    out=[]; bad=0
    out.append(f"== {R['样本']}  正文自第{R['_start']}行起  有效字数 {R['有效字数']}  段数 {R['段数']}")
    out.append(f"{'指标':<22}{'实测':>8}  {'阈值':<12}{'原书全书':>8}  {'原书P10/P50/P90':<18}结果  规则")
    for name,key,d,t,rule in CHECKS:
        v=R[key]; base=b.get(BASEKEY.get(key,key),'')
        if key=='_bushi': base=f"{base}/千字"
        pp=pct.get(key); ps=f"{pp['P10']}/{pp['P50']}/{pp['P90']}" if pp else '-'
        ts=(f"{t[0]}–{t[1]}" if d=='in' else f"{d}{t}")
        good=ok(v,d,t); bad+=0 if good else 1
        line=f"{name:<22}{v:>8}  {ts:<12}{str(base):>8}  {ps:<18}{'达标' if good else '✗越界(标红)'}  {rule}"
        out.append(line if good else red(line))
    # 定位（便于改文）
    loc=[]
    if R['_n60_lines']: loc.append('>60字叙述段 行号(字数): '+'、'.join(f'{a}({c})' for a,c in R['_n60_lines']))
    if R['_maxcl_lines']: loc.append('单句>4分句 行号: '+'、'.join(map(str,sorted(set(R['_maxcl_lines'])))))
    bd={w:c for w,c in R.get('身体词明细',{}).items()}
    if bd: loc.append('身体词明细: '+'、'.join(f'{w}×{c}' for w,c in bd.items()))
    if R['_bushi_lines']: loc.append('“不是…，是” 行号: '+'、'.join(map(str,R['_bushi_lines'])))
    eh=[ln for ln,t,_ in R.get('_我方段末命中行',[])]
    if eh: loc.append('段末金句/转折/评价/情绪收尾 行号: '+'、'.join(map(str,eh)))
    loc.append(f"章首段在第{R['_head_ln']}行，章末段在第{R['_tail_ln']}行")
    # §10 启发式提醒（风格草案建议新增；待用户阅读反馈）
    if R.get('_idface'):
        loc.append(f"亮身份骨架词命中 {R['_idface']} 处 行号: "+'、'.join(map(str,R['_idface_lines']))+'（§10.4／§9.3，人读确认）')
    if R.get('_formula'):
        loc.append(f"公式打断词命中 {R['_formula']} 处 行号: "+'、'.join(map(str,R['_formula_lines']))+'（§10.4／§9.3，人读确认）')
    if R.get('_ending_summary'):
        loc.append('章末疑似主题总结句（§10.1-7，人读确认）')
    sl=R.get('_soft_land','n/a')
    if sl!='n/a':
        loc.append(f'硬钩后软着陆启发式: {sl}（鬼夫 CDB／§10.3，人读确认）')
    loc.append('章末钩子类型粗分: '+'/'.join(R.get('_hook_types',['未识别']))+'（§10／草案，人读确认；跨章同型另账）')
    if R.get('_consent_warn'):
        loc.append(f'同意边界疑似违规 {R["_consent_warn"]} 处 行号: '+'、'.join(map(str,R['_consent_lines']))+'（§10 同意抽检，人读确认；拒绝后仍继续＝硬失败）')
    out += ['  · '+x for x in loc]
    out.append(f"  越界 {bad} 项 / 共 {len(CHECKS)} 项。R23骨架、R24说停就停、R13打断来源等需人读。")
    out.append('  §10启发式: 亮身份／公式打断／章末总结／硬钩软着陆／章末钩型／同意边界已粗检；其余见文件末 TODO（待反馈后启用）。')
    return '\n'.join(out),bad

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('files',nargs='+'); ap.add_argument('--start',type=int)
    ap.add_argument('--no-color',action='store_true'); ap.add_argument('--color',action='store_true'); ap.add_argument('--json',action='store_true')
    a=ap.parse_args(); b,pct=baseline(); allbad=0; js=[]
    color=(a.color or sys.stdout.isatty()) and not a.no_color
    for f in a.files:
        R=measure(f,a.start)
        if a.json:
            js.append({'file':f,**{name:R[key] for name,key,*_ in CHECKS}})
            allbad+=sum(1 for name,key,d,t,_ in CHECKS if not ok(R[key],d,t))
        else:
            s,bad=report(R,b,pct,color); print(s); print(); allbad+=bad
    if a.json: print(json.dumps(js,ensure_ascii=False,indent=1))
    sys.exit(1 if allbad else 0)


# --- §10 / 风格草案「建议新增」中偏主观、暂不进硬检（待用户阅读反馈后启用）---
# TODO 待反馈后启用: 章末钩子类型「跨章」同型连续 ≤2——单章粗分已启用；跨章需状态账
# TODO 待反馈后启用: 第三方视角占比／「被看见」拍数（1–2 拍）——需视角标注
# TODO 待反馈后启用: 道具回收跨度／未回收列表——需全书账本
# TODO 待反馈后启用: 残响触发物理理由完备率（≥1～2 条介质）——需残响段标注
# TODO 待反馈后启用: 有声无像／半句停法占比——需残响段标注
# TODO 待反馈后启用: 程序挡板密度（合法拒绝 vs 蛮力）——需自救链标注
# TODO 待反馈后启用: 澄清／声明失败率——需网暴线标注
# 同意边界：已做关键词粗检（_consent_warn）；精细「说停就停可核验动作」仍待亲密段标注
# TODO 待反馈后启用: 旁观伦理标记全书次数上限（§10.5 拍板后）
# TODO 待反馈后启用: 分级披露同事件两套叙述——需事件标注
# 章末钩子类型：单章粗分已报（_hook_types）；相邻章同型连续 ≤2 仍需跨章状态
