#!/usr/bin/env python3
"""Download actual daily ERA5-Land temperature and ERA5 precipitation, 1990-2019.
Scientific caveat: site proxies are city coordinates, NOT orchard geolocations.
Dates are complete calendar days in the requested local timezone.
"""
import csv,gzip,json,hashlib,os,random,time,calendar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from datetime import date
P=Path("weather_supply")
regions=list(csv.DictReader(open(P/"pre2010_production_region_manifest.csv",encoding="utf8")))
part=int(os.environ.get("PART","0"));nparts=int(os.environ.get("PARTS","5"))
selected=[x for i,x in enumerate(regions) if i%nparts==part]
OUT=Path("measured_weather");OUT.mkdir(exist_ok=True)
timezone_map={"IRN":"Asia/Tehran","GEO":"Asia/Tbilisi","CHL":"America/Santiago","CHN":"Asia/Shanghai"}
def timezone(row):
 if row["exporter_iso3"]!="AUS":return timezone_map[row["exporter_iso3"]]
 return {"Sunraysia_Mildura":"Australia/Melbourne","Riverina_Griffith":"Australia/Sydney",
         "Riverland_Berri":"Australia/Adelaide","Adelaide_Plains":"Australia/Adelaide"}[row["region"]]
def fetch(row,model,var):
 params=dict(latitude=row["latitude"],longitude=row["longitude"],start_date="1990-01-01",
 end_date="2019-12-31",daily=var,models=model,timezone=timezone(row),cell_selection="land",
 temperature_unit="celsius",precipitation_unit="mm")
 u="https://archive-api.open-meteo.com/v1/archive?"+urlencode(params)
 for attempt in range(6):
  try:
   with urlopen(Request(u,headers={"User-Agent":"TreeNutResearchHistoricalClimate/1.0"}),timeout=120) as r:raw=r.read()
   j=json.loads(raw);v=j.get("daily",{});days=v.get("time",[])
   if j.get("error"):raise ValueError(str(j.get("reason")))
   if len(days)!=(date(2020,1,1)-date(1990,1,1)).days or days[0]!="1990-01-01" or days[-1]!="2019-12-31":
    raise ValueError("incomplete daily dates "+str(len(days)))
   for x in var.split(","):
    if x not in v or len(v[x])!=len(days):raise ValueError("variable missing "+x)
    if any(y is None for y in v[x]):raise ValueError("null observations "+x)
   return j,dict(status="complete",url=u,source_sha256=hashlib.sha256(raw).hexdigest(),size=len(raw),
     returned_lat=j.get("latitude"),returned_lon=j.get("longitude"),returned_timezone=j.get("timezone"),attempts=attempt+1)
  except Exception as e:
   err=repr(e)
   print("RETRY",row["region"],model,attempt,err[:120],flush=True)
   if attempt<5:time.sleep(min(3*2**attempt+random.random()*2,40))
 return None,dict(status="failed",url=u,error=err,attempts=6)
logs=[]
for row in selected:
 identity=row["exporter_iso3"]+"_"+row["nut_name"]+"_"+row["region"]
 print("START",identity,flush=True)
 tm,info_t=fetch(row,"era5_land","temperature_2m_min,temperature_2m_max")
 pr,info_p=fetch(row,"era5","precipitation_sum")
 for model,meta in [("era5_land",info_t),("era5",info_p)]:
  logs.append({**{"exporter_iso3":row["exporter_iso3"],"nut_name":row["nut_name"],"region":row["region"],
               "model":model,"weight_status":row["eligibility"],"timezone_requested":timezone(row)},**meta})
 if tm is not None and pr is not None:
  t=tm["daily"];p=pr["daily"]
  assert t["time"]==p["time"], identity
  with gzip.open(OUT/(identity+"_daily.csv.gz"),"wt",newline="",encoding="utf8") as f:
   w=csv.writer(f)
   w.writerow(["exporter_iso3","nut_name","region","date","tmin_C","tmax_C","precip_mm","lat_proxy","lon_proxy","source_t","source_p"])
   for day,low,high,rain in zip(t["time"],t["temperature_2m_min"],t["temperature_2m_max"],p["precipitation_sum"]):
    if low>high or rain<0:raise ValueError("Invalid weather "+identity+day)
    w.writerow([row["exporter_iso3"],row["nut_name"],row["region"],day,low,high,rain,
                row["latitude"],row["longitude"],"ERA5-Land","ERA5"])
  print("SUCCESS",identity,len(t["time"]),flush=True)
 else: print("FAILED_REGION",identity,flush=True)
 time.sleep(0.8)
 (OUT/"source_requests.json").write_text(json.dumps(logs,ensure_ascii=False,indent=2))
(OUT/"source_requests.json").write_text(json.dumps(logs,ensure_ascii=False,indent=2))
print("FINISHED",part,"of",nparts,"regions",len(selected),"source_success",sum(i["status"]=="complete" for i in logs),flush=True)
