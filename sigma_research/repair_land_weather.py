import os, csv, gzip, json, hashlib, urllib.parse, urllib.request, time, random
from pathlib import Path
sites={
"Tarragona":(41.11910287,1.2584219),
"Barcelona":(41.38424664,2.17634927),
"Alicante___Alacant":(38.34548705,-0.4831832),
"Cadiz":(36.52171152,-6.28414575),
"Santa_Cruz_de_Tenerife":(28.46285408,-16.24720629),
"Almeria":(36.83892362,-2.46413188),
"Siskiyou":(41.59268663387329,-122.5403677631641)
}
part=int(os.environ.get("PART","0"));nparts=3
out=Path("repaired_weather");out.mkdir(exist_ok=True)
logs=[]
for idx,(n,(lat,lon)) in enumerate(sites.items()):
 if idx%nparts!=part:continue
 print("START",n,flush=True)
 loc={}
 for model,variables in [("era5_land","temperature_2m_min,temperature_2m_max"),("era5","precipitation_sum")]:
  q=dict(latitude=lat,longitude=lon,start_date="1991-01-01",end_date="2019-12-31",daily=variables,models=model,timezone="America/Los_Angeles" if n=="Siskiyou" else "Europe/Madrid",cell_selection="land")
  url="https://archive-api.open-meteo.com/v1/archive?"+urllib.parse.urlencode(q)
  err=""
  for attempt in range(6):
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"TreeNutIVValidation/1.0"}),timeout=120) as req:raw=req.read()
    j=json.loads(raw);days=j.get("daily",{}).get("time",[])
    if j.get("error") or len(days)!=10592 or days[0]!="1991-01-01" or days[-1]!="2019-12-31":raise ValueError("invalid response "+str(j.get("reason")))
    if any((v not in j["daily"] or any(x is None for x in j["daily"][v])) for v in variables.split(",")):raise ValueError("null data")
    loc[model]=j
    logs.append({"region":n,"model":model,"status":"verified","source_sha256":hashlib.sha256(raw).hexdigest(),"returned_lat":j.get("latitude"),"returned_lon":j.get("longitude"),"url":url})
    break
   except Exception as e:
    err=str(e)
    print("RETRY",n,model,attempt,err[:120],flush=True)
    if attempt<5:time.sleep(min(3*(2**attempt)+random.random()*3,36))
  if model not in loc:logs.append({"region":n,"model":model,"status":"failed","error":err})
  time.sleep(1)
 if len(loc)!=2:continue
 t=loc["era5_land"]["daily"];p=loc["era5"]["daily"]
 assert t["time"]==p["time"]
 with gzip.open(out/(n+"_daily.csv.gz"),"wt",newline="") as f:
  w=csv.writer(f);w.writerow(["region","province","date","tmin_C","tmax_C","precip_mm","requested_lat","requested_lon"])
  for i in range(10592):w.writerow([n,n,t["time"][i],t["temperature_2m_min"][i],t["temperature_2m_max"][i],p["precipitation_sum"][i],lat,lon])
 print("VALIDATED",n,len(t["time"]),flush=True)
(out/"repair_log.json").write_text(json.dumps(logs,indent=2))
