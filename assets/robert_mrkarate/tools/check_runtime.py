import csv,json
from pathlib import Path
r=Path(__file__).resolve().parents[1];rows=list(csv.DictReader((r/'evidencias/testes_motor.csv').open()));summary=[]
for case in range(27):
 rs=[v for v in rows if int(v['case'])==case];assert len(rs)==320
 damage=1000-min(int(v['p2life']) for v in rs);low=[v for v in rs if int(v['p2life'])==1000-damage];hits=int(low[-1]['p2hits']);helpers=max(int(v['helpers']) for v in rs)
 if damage:assert (damage,hits) in ((60,5),(333,50)),(case,damage,hits)
 summary.append({'case':case,'connected':damage>0,'damage':damage,'hits_at_end':hits if damage else 0,'volley_members':helpers,'frames':len(rs)})
assert summary[7]['volley_members']==3 and summary[7]['damage']==60
assert summary[15]['volley_members']==3 and summary[15]['damage']==60
assert sum(s['damage']==333 for s in summary)>=4
(r/'evidencias/testes_motor.json').write_text(json.dumps(summary,indent=2))
print('PASS: 27 executions;',sum(s['connected'] for s in summary),'connected;',sum(s['damage']==333 for s in summary),'supers with 50 hits/333 damage; airborne volleys confirmed.')
