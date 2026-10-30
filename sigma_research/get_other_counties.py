import csv,json,gzip,hashlib,os,time,random,datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
root=Path("sigma_research")
out=Path("weather_data");out.mkdir(exist_ok=True)
part=int(os.environ.get("PART","0"));nparts=int(os.environ.get("NPARTS","3"))
sites=list(csv.DictReader(open(root/"additional_counties.csv")))
sites=[r for i,r in enumerate(sites) if i%nparts==part]
logs=[]
for site in sites:
    name=site["region"];lat=float(site["latitude"]);lon=float(site["longitude"])
    values={};valid=True
    for model,vars in [("era5_land","temperature_2m_min,temperature_2m_max"),("era5","precipitation_sum")]:
        params=dict(latitude=str(lat),longitude=str(lon),start_date="1991-01-01",end_date="2019-12-31",daily=vars,models=model,timezone="America/Los_Angeles")
        url="https://archive-api.open-meteo.com/v1/archive?"+urlencode(params)
        error=None
        for attempt in range(4):
            try:
                with urlopen(Request(url,headers={"User-Agent":"AcademicTreeNutWeather/1.0"}),timeout=90) as r: raw=r.read()
                j=json.loads(raw)
                if j.get("error"):raise ValueError(j.get("reason","unknown"))
                t=j.get("daily",{}).get("time",[])
                if len(t)!=10592 or t[0]!="1991-01-01" or t[-1]!="2019-12-31":raise ValueError("incorrect dates "+str(len(t)))
                if any(len(j["daily"].get(v,[]))!=10592 for v in vars.split(",")):raise ValueError("missing variable")
                values[model]=j
                logs.append(dict(region=name,model=model,status="ok",url=url,sha256=hashlib.sha256(raw).hexdigest(),n_days=len(t),lat=j.get("latitude"),lon=j.get("longitude")))
                break
            except Exception as e:
                error=str(e)
                if attempt<3:time.sleep(2+attempt*4+random.random())
        if model not in values:
            logs.append(dict(region=name,model=model,status="failed",url=url,error=error))
            valid=False
        time.sleep(1)
    if not valid:continue
    t=values["era5_land"]["daily"];p=values["era5"]["daily"]
    if t["time"]!=p["time"]:raise ValueError("time mismatch "+name)
    file=out/(name.replace(" ","_")+"_daily.csv.gz")
    with gzip.open(file,"wt",newline="") as f:
        w=csv.writer(f);w.writerow(["region","date","tmin_C","tmax_C","precip_mm","requested_lat","requested_lon"])
        for day,tmin,tmax,prec in zip(t["time"],t["temperature_2m_min"],t["temperature_2m_max"],p["precipitation_sum"]):
            w.writerow([name,day,tmin,tmax,prec,lat,lon])
    print("DONE",name,10592,flush=True)
with open(out/"source_log.json","w") as f:json.dump(logs,f,indent=2)
print("PART_FINISHED",part,len(sites),sum(x["status"]=="ok" for x in logs),flush=True)
