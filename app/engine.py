from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo
import swisseph as swe

ENGINE_VERSION = "0.1.0"
CALCULATION_REFERENCE = "ForceTeller-style workflow; independent deterministic engine"

STEMS = [
    {"index":0,"ko":"갑","hanja":"甲","roman":"Gap","element":"Wood","yin_yang":"Yang"},
    {"index":1,"ko":"을","hanja":"乙","roman":"Eul","element":"Wood","yin_yang":"Yin"},
    {"index":2,"ko":"병","hanja":"丙","roman":"Byeong","element":"Fire","yin_yang":"Yang"},
    {"index":3,"ko":"정","hanja":"丁","roman":"Jeong","element":"Fire","yin_yang":"Yin"},
    {"index":4,"ko":"무","hanja":"戊","roman":"Mu","element":"Earth","yin_yang":"Yang"},
    {"index":5,"ko":"기","hanja":"己","roman":"Gi","element":"Earth","yin_yang":"Yin"},
    {"index":6,"ko":"경","hanja":"庚","roman":"Gyeong","element":"Metal","yin_yang":"Yang"},
    {"index":7,"ko":"신","hanja":"辛","roman":"Sin","element":"Metal","yin_yang":"Yin"},
    {"index":8,"ko":"임","hanja":"壬","roman":"Im","element":"Water","yin_yang":"Yang"},
    {"index":9,"ko":"계","hanja":"癸","roman":"Gye","element":"Water","yin_yang":"Yin"},
]

BRANCHES = [
    {"index":0,"ko":"자","hanja":"子","roman":"Ja","animal":"Rat","element":"Water","yin_yang":"Yang"},
    {"index":1,"ko":"축","hanja":"丑","roman":"Chuk","animal":"Ox","element":"Earth","yin_yang":"Yin"},
    {"index":2,"ko":"인","hanja":"寅","roman":"In","animal":"Tiger","element":"Wood","yin_yang":"Yang"},
    {"index":3,"ko":"묘","hanja":"卯","roman":"Myo","animal":"Rabbit","element":"Wood","yin_yang":"Yin"},
    {"index":4,"ko":"진","hanja":"辰","roman":"Jin","animal":"Dragon","element":"Earth","yin_yang":"Yang"},
    {"index":5,"ko":"사","hanja":"巳","roman":"Sa","animal":"Snake","element":"Fire","yin_yang":"Yin"},
    {"index":6,"ko":"오","hanja":"午","roman":"O","animal":"Horse","element":"Fire","yin_yang":"Yang"},
    {"index":7,"ko":"미","hanja":"未","roman":"Mi","animal":"Goat","element":"Earth","yin_yang":"Yin"},
    {"index":8,"ko":"신","hanja":"申","roman":"Sin","animal":"Monkey","element":"Metal","yin_yang":"Yang"},
    {"index":9,"ko":"유","hanja":"酉","roman":"Yu","animal":"Rooster","element":"Metal","yin_yang":"Yin"},
    {"index":10,"ko":"술","hanja":"戌","roman":"Sul","animal":"Dog","element":"Earth","yin_yang":"Yang"},
    {"index":11,"ko":"해","hanja":"亥","roman":"Hae","animal":"Pig","element":"Water","yin_yang":"Yin"},
]

HIDDEN_STEMS = {
    0:[9],1:[5,9,7],2:[0,2,4],3:[1],4:[4,1,9],5:[2,4,6],
    6:[3,5],7:[5,3,1],8:[6,8,4],9:[7],10:[4,7,3],11:[8,0]
}

TEN_GODS = {
    "friend":("Friend / Companion","비견","比肩"),
    "rob_wealth":("Rob Wealth","겁재","劫財"),
    "eating_god":("Eating God","식신","食神"),
    "hurting_officer":("Hurting Officer","상관","傷官"),
    "indirect_wealth":("Indirect Wealth","편재","偏財"),
    "direct_wealth":("Direct Wealth","정재","正財"),
    "seven_killings":("Seven Killings / Indirect Officer","편관","偏官"),
    "direct_officer":("Direct Officer","정관","正官"),
    "indirect_resource":("Indirect Resource","편인","偏印"),
    "direct_resource":("Direct Resource","정인","正印"),
}

GENERATES={"Wood":"Fire","Fire":"Earth","Earth":"Metal","Metal":"Water","Water":"Wood"}
CONTROLS={"Wood":"Earth","Fire":"Metal","Earth":"Water","Metal":"Wood","Water":"Fire"}

SIX_COMBINATIONS={frozenset((0,1)):"Earth",frozenset((2,11)):"Wood",frozenset((3,10)):"Fire",frozenset((4,9)):"Metal",frozenset((5,8)):"Water",frozenset((6,7)):"Earth"}
CLASHES={frozenset(x) for x in [(0,6),(1,7),(2,8),(3,9),(4,10),(5,11)]}
HARMS={frozenset(x) for x in [(0,7),(1,6),(2,5),(3,4),(8,11),(9,10)]}
BREAKS={frozenset(x) for x in [(0,9),(3,6),(4,1),(7,10),(2,11),(8,5)]}
THREE_HARMONY={frozenset((8,0,4)):"Water",frozenset((11,3,7)):"Wood",frozenset((2,6,10)):"Fire",frozenset((5,9,1)):"Metal"}

GROWTH_STAGES=[
    ("Birth / Long Life","장생","長生"),("Bath","목욕","沐浴"),("Crown and Belt","관대","冠帶"),
    ("Establishment","건록","建祿"),("Imperial Prosperity","제왕","帝旺"),("Decline","쇠","衰"),
    ("Illness","병","病"),("Death","사","死"),("Tomb","묘","墓"),("Extinction","절","絶"),
    ("Conception","태","胎"),("Nurture","양","養"),
]
GROWTH_BIRTH_BRANCH={0:11,1:6,2:2,3:9,4:2,5:9,6:5,7:0,8:8,9:3}
VOID_BRANCHES_BY_XUN={0:(10,11),1:(8,9),2:(6,7),3:(4,5),4:(2,3),5:(0,1)}

class CalculationError(ValueError): pass

def _jd(dt: datetime) -> float:
    u=dt.astimezone(timezone.utc)
    h=u.hour+u.minute/60+u.second/3600
    return swe.julday(u.year,u.month,u.day,h,swe.GREG_CAL)

def _sun_lon(jd: float) -> float:
    xx,_=swe.calc_ut(jd,swe.SUN,swe.FLG_MOSEPH|swe.FLG_SPEED)
    return xx[0]%360

def _norm180(x: float) -> float: return (x+180)%360-180

def _crossing(target: float,start: float,end: float,step: float=.25) -> float:
    x=start; f0=_norm180(_sun_lon(x)-target)
    while x<=end:
        nx=x+step; f=_norm180(_sun_lon(nx)-target)
        if f0<=0<=f and f-f0<90:
            lo,hi=x,nx
            for _ in range(50):
                mid=(lo+hi)/2
                if _norm180(_sun_lon(mid)-target)>=0: hi=mid
                else: lo=mid
            return (lo+hi)/2
        x,f0=nx,f
    raise CalculationError("Solar longitude crossing not found")

def _li_chun(year:int)->float:
    c=datetime(year,2,4,12,tzinfo=timezone.utc)
    j=_jd(c)
    return _crossing(315,j-4,j+4)

def _jdn(y:int,m:int,d:int)->int:
    a=(14-m)//12; yy=y+4800-a; mm=m+12*a-3
    return d+(153*mm+2)//5+365*yy+yy//4-yy//100+yy//400-32045

def _ten_god(dm:int,target:int)->dict[str,str]:
    a,b=STEMS[dm],STEMS[target]
    same=a["yin_yang"]==b["yin_yang"]
    if a["element"]==b["element"]: key="friend" if same else "rob_wealth"
    elif GENERATES[a["element"]]==b["element"]: key="eating_god" if same else "hurting_officer"
    elif CONTROLS[a["element"]]==b["element"]: key="indirect_wealth" if same else "direct_wealth"
    elif CONTROLS[b["element"]]==a["element"]: key="seven_killings" if same else "direct_officer"
    else: key="indirect_resource" if same else "direct_resource"
    en,ko,hj=TEN_GODS[key]
    return {"key":key,"en":en,"ko":ko,"hanja":hj}

def _stem(i:int,dm:Optional[int]=None,day_master=False)->dict[str,Any]:
    p=dict(STEMS[i])
    p["ten_god"]={"key":"day_master","en":"Day Master","ko":"일간","hanja":"日干"} if day_master else (_ten_god(dm,i) if dm is not None else None)
    return p

def _branch(i:int,dm:int)->dict[str,Any]:
    p=dict(BRANCHES[i]); p["hidden_stems"]=[_stem(s,dm) for s in HIDDEN_STEMS[i]]
    return p

def _growth(dm:int,b:int)->dict[str,Any]:
    start=GROWTH_BIRTH_BRANCH[dm]; direction=1 if STEMS[dm]["yin_yang"]=="Yang" else -1
    idx=((b-start)*direction)%12
    en,ko,hj=GROWTH_STAGES[idx]
    return {"index":idx,"en":en,"ko":ko,"hanja":hj}

def _pillar(si:int,bi:int,dm:int,name:str)->dict[str,Any]:
    return {"name":name,"label":f"{STEMS[si]['roman']}-{BRANCHES[bi]['roman']} ({STEMS[si]['hanja']}{BRANCHES[bi]['hanja']})",
            "stem":_stem(si,dm,day_master=name=="day"),"branch":_branch(bi,dm),"growth_stage":_growth(dm,bi)}

def _day_index(dt:datetime,boundary:str)->tuple[int,date]:
    d=dt.date()
    if boundary=="zi_start" and dt.hour>=23: d+=timedelta(days=1)
    return (_jdn(d.year,d.month,d.day)+49)%60,d

def _hour_branch(dt:datetime)->int:
    return int((((dt.hour+dt.minute/60)+1)%24)//2)

def _solar_correct(local:datetime,lon:float)->dict[str,Any]:
    dst=local.dst() or timedelta(0)
    off=local.utcoffset() or timedelta(0)
    standard=off-dst
    meridian=standard.total_seconds()/3600*15
    long_min=4*(lon-meridian)
    eot=swe.time_equ(_jd(local.astimezone(timezone.utc)))*1440
    corrected=local.replace(tzinfo=None)-dst+timedelta(minutes=long_min+eot)
    return {"corrected":corrected,"longitude_correction_minutes":long_min,"equation_of_time_minutes":eot,
            "total_clock_to_solar_minutes":-dst.total_seconds()/60+long_min+eot}

def _month_index(jd:float,lon:float)->tuple[int,float,float]:
    k=int(((lon-315)%360)//30)
    prev=(315+30*k)%360; nxt=(prev+30)%360
    pj=_crossing(prev,jd-40,jd+.001); nj=_crossing(nxt,jd-.001,jd+40)
    return k,(jd-pj)*1440,(nj-jd)*1440

def _relationships(pillars:dict[str,Any])->dict[str,list]:
    items=[(n,p["branch"]["index"]) for n,p in pillars.items() if p]
    out={"six_combinations":[],"three_harmony":[],"clashes":[],"harms":[],"breaks":[]}
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            pa,a=items[i]; pb,b=items[j]; key=frozenset((a,b)); rec={"pillars":[pa,pb],"branches":[BRANCHES[a]["hanja"],BRANCHES[b]["hanja"]]}
            if key in SIX_COMBINATIONS: out["six_combinations"].append({**rec,"element":SIX_COMBINATIONS[key]})
            if key in CLASHES: out["clashes"].append(rec)
            if key in HARMS: out["harms"].append(rec)
            if key in BREAKS: out["breaks"].append(rec)
    bset={b for _,b in items}
    for tri,e in THREE_HARMONY.items():
        if tri.issubset(bset): out["three_harmony"].append({"branches":[BRANCHES[x]["hanja"] for x in sorted(tri)],"element":e})
    return out

def _elements(pillars:dict[str,Any])->dict[str,int]:
    out={e:0 for e in ["Wood","Fire","Earth","Metal","Water"]}
    for p in pillars.values():
        if not p: continue
        out[p["stem"]["element"]]+=1; out[p["branch"]["element"]]+=1
        for hs in p["branch"]["hidden_stems"]: out[hs["element"]]+=1
    return out

def _sexagenary_index(s:int,b:int)->int:
    for i in range(60):
        if i%10==s and i%12==b:return i
    raise CalculationError("Invalid stem/branch parity")

def _daewoon(pillars:dict[str,Any],prev_min:float,next_min:float,sex:str,direction:str)->dict[str,Any]:
    ys=pillars["year"]["stem"]["index"]
    if direction=="auto":
        if sex not in {"male","female"}: return {"status":"needs_method_input","cycles":[]}
        yang=STEMS[ys]["yin_yang"]=="Yang"
        forward=(sex=="male" and yang) or (sex=="female" and not yang)
    else: forward=direction=="forward"
    d=1 if forward else -1
    days=abs((next_min if d==1 else prev_min)/1440)
    start=days/3
    mi=_sexagenary_index(pillars["month"]["stem"]["index"],pillars["month"]["branch"]["index"])
    dm=pillars["day"]["stem"]["index"]; cycles=[]
    for n in range(1,9):
        idx=(mi+d*n)%60; s,b=idx%10,idx%12
        cycles.append({"cycle_number":n,"start_age":round(start+(n-1)*10,3),"end_age":round(start+n*10,3),
                       "stem":_stem(s,dm),"branch":_branch(b,dm),"ten_god":_ten_god(dm,s)})
    return {"status":"calculated","direction":"forward" if d==1 else "backward","start_age_years":round(start,6),"cycles":cycles}

def calculate_chart(data:dict[str,Any])->dict[str,Any]:
    bd=date.fromisoformat(data["birth_date"]); status=data.get("time_status","exact")
    tz=ZoneInfo(data["timezone"]); lat=float(data["latitude"]); lon=float(data["longitude"])
    if status=="unknown": h,m=12,0
    else:
        h,m=map(int,data["birth_time"].split(":")[:2])
    local=datetime(bd.year,bd.month,bd.day,h,m,tzinfo=tz)
    utc=local.astimezone(timezone.utc); jd=_jd(utc)
    corr=_solar_correct(local,lon); effective=corr["corrected"] if data.get("use_true_solar_time",True) else local.replace(tzinfo=None)
    boundary=data.get("day_boundary","midnight")
    lc=_li_chun(local.year); sy=local.year if jd>=lc else local.year-1
    ys=(sy-4)%10; yb=(sy-4)%12
    sl=_sun_lon(jd); mi,prev_min,next_min=_month_index(jd,sl); mb=(2+mi)%12; ms=(2*ys+2+mi)%10
    di,effective_date=_day_index(effective,boundary); ds,db=di%10,di%12
    hs=hb=None
    if status!="unknown":
        hb=_hour_branch(effective); hs=(2*ds+hb)%10
    pillars={"year":_pillar(ys,yb,ds,"year"),"month":_pillar(ms,mb,ds,"month"),"day":_pillar(ds,db,ds,"day"),
             "hour":_pillar(hs,hb,ds,"hour") if hs is not None else None}
    warnings=[]
    safety=float(data.get("boundary_safety_minutes",120))
    if abs((jd-lc)*1440)<=safety:warnings.append("YEAR PILLAR BOUNDARY CASE")
    if min(prev_min,next_min)<=safety:warnings.append("MONTH PILLAR BOUNDARY CASE")
    if status=="unknown":warnings.append("HOUR PILLAR OMITTED — BIRTH TIME UNKNOWN")
    voids=VOID_BRANCHES_BY_XUN[di//10]
    return {
        "calculation_status":"deterministic; ForceTeller compatibility validation pending",
        "certified_forceteller_match":False,
        "engine":{"version":ENGINE_VERSION,"calculation_reference":CALCULATION_REFERENCE,
                  "year_boundary":"exact solar longitude 315° (Ipchun)",
                  "month_boundary":"12 sectional solar terms, 30° intervals from 315°",
                  "day_anchor":"(Gregorian JDN + 49) mod 60; 1949-10-01 = 甲子",
                  "day_boundary":boundary,"true_solar_time":bool(data.get("use_true_solar_time",True))},
        "identity":{"name":data.get("name",""),"nickname":data.get("nickname",""),"sex":data.get("sex","unspecified")},
        "birth":{"original_date":bd.isoformat(),"original_time":None if status=="unknown" else data.get("birth_time"),
                 "time_status":status,"place_label":data.get("place",""),"latitude":lat,"longitude":lon,
                 "iana_timezone":data["timezone"],"historical_utc_offset":str(local.utcoffset()),"dst":str(local.dst()),
                 "resolved_utc":utc.isoformat(),"civil_local":local.isoformat(),"corrected_solar_local":corr["corrected"].isoformat(),
                 "effective_for_day_hour":effective.isoformat(),"effective_day_date":effective_date.isoformat(),
                 "solar_correction":{k:v for k,v in corr.items() if k!="corrected"}},
        "astronomy":{"birth_jd_ut":jd,"solar_longitude_degrees":sl},
        "boundary_check":{"safety_window_minutes":safety,"warnings":warnings,"boundary_sensitive":bool(warnings)},
        "pillars":pillars,"day_master":_stem(ds,ds,day_master=True),
        "five_elements":{"combined_unweighted_presence":_elements(pillars),
                         "note":"Presence counts are not strength percentages."},
        "relationships":_relationships(pillars),
        "void":{"void_branches":[dict(BRANCHES[i]) for i in voids],
                "natal_hits":[n for n,p in pillars.items() if p and p["branch"]["index"] in voids]},
        "daewoon":_daewoon(pillars,prev_min,next_min,str(data.get("sex","unspecified")).lower(),data.get("luck_direction","auto")),
        "interpretation":{"status":"separate_layer","message":"Interpretation must never alter calculated values."}
    }

def calculate_day(date_iso:str)->dict[str,Any]:
    d=date.fromisoformat(date_iso); idx=(_jdn(d.year,d.month,d.day)+49)%60; s,b=idx%10,idx%12
    return {"date":date_iso,"sexagenary_index":idx,"stem":dict(STEMS[s]),"branch":dict(BRANCHES[b]),
            "label":f"{STEMS[s]['roman']}-{BRANCHES[b]['roman']} ({STEMS[s]['hanja']}{BRANCHES[b]['hanja']})"}
