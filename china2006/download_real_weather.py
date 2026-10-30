import csv,os,json,gzip,time,hashlib,random
from urllib.request import urlopen,Request
from urllib.parse import urlencode
from pathlib import Path
from datetime import date
sites=list(csv.DictReader(open("china2006/additional_provinces.csv")))
part=int(os.environ.get("PART","0"));npart=4
out=Path("real_china_weather");out.mkdir(exist_ok=True)
audit=[]
for i,row in enumerate(sites):
 if i%npart!=part:continue
 reg=row["province"];lat=row["latitude"];lon=row["longitude"]
 weather={};print("START",reg,flush=True)
 for model,fields in [("era5_land","temperature_2m_min,temperature_2m_max"),("era5","precipitation_sum")]:
  q=dict(latitude=lat,longitude=lon,start_date="1990-01-01",end_date="2019-12-31",
    daily=fields,models=model,timezone="Asia/Shanghai",cell_selection="land")
  u="https://archive-api.open-meteo.com/v1/archive?"+urlencode(q)
  reason="";valid=False
  for retry in range(6):
   try:
    with urlopen(Request(u,headers={"User-Agent":"TreeNutIVClimateAcademic/1.0"}),timeout=100) as request: b=request.read()
    r=json.loads(b);d=r.get("daily",{})
    if r.get("error") or len(d.get("time",[]))!=10957:raise ValueError("invalid API days "+str(r.get("reason")))
    if any(len(d.get(f,[]))!=10957 or any(x is None for x in d[f]) for f in fields.split(",")):raise ValueError("missing values")
    weather[model]=d;valid=True
    audit.append({"province":reg,"model":model,"status":"success","url":u,"sha256":hashlib.sha256(b).hexdigest(),"returned_lat":r.get("latitude"),"returned_lon":r.get("longitude")})
    break
   except Exception as ex:
    reason=str(ex);print("RETRY",reg,model,retry,reason[:90],flush=True)
    if retry<5:time.sleep(min(2*2**retry+random.random(),35))
  if not valid:audit.append({"province":reg,"model":model,"status":"failed","error":reason,"url":u})
  time.sleep(.7)
 if len(weather)==2:
  a=weather["era5_land"];b=weather["era5"]
  assert a["time"]==b["time"]
  with gzip.open(out/(reg+"_daily.csv.gz"),"wt",newline="") as f:
   w=csv.writer(f);w.writerow(["exporter_iso3","nut_name","region","date","tmin_C","tmax_C","precip_mm","lat_proxy","lon_proxy"])
   for vals in zip(a["time"],a["temperature_2m_min"],a["temperature_2m_max"],b["precipitation_sum"]):
    w.writerow(["CHN","Walnuts",reg,*vals,lat,lon])
  print("DONE",reg,10957,flush=True)
(out/"request_log.json").write_text(json.dumps(audit,indent=2))
