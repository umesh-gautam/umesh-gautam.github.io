import csv,json,gzip,hashlib,os,time,random
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
root=Path("sigma_research");out=Path("weather_output");out.mkdir(exist_ok=True)
sites=list(csv.DictReader(open(root/"spain_2008_province_weights.csv")))
unique={r["province"]:(r["latitude"],r["longitude"]) for r in sites}
part=int(os.environ.get("PART","0"));nparts=int(os.environ.get("NPARTS","4"))
todo=[(k,v) for i,(k,v) in enumerate(unique.items()) if i%nparts==part]
logs=[]
for name,(lat,lon) in todo:
    values={}
    for model,variables in [("era5_land","temperature_2m_min,temperature_2m_max"),("era5","precipitation_sum")]:
        q=dict(latitude=lat,longitude=lon,start_date="1991-01-01",end_date="2019-12-31",daily=variables,models=model,timezone="Europe/Madrid",cell_selection="nearest")
        url="https://archive-api.open-meteo.com/v1/archive?"+urlencode(q)
        error=""
        for attempt in range(5):
            try:
                with urlopen(Request(url,headers={"User-Agent":"AcademicTreeNutWeatherSpain/1.0"}),timeout=90) as response:raw=response.read()
                js=json.loads(raw)
                if js.get("error"):raise ValueError(js.get("reason"))
                days=js.get("daily",{}).get("time",[])
                if len(days)!=10592 or days[0]!="1991-01-01" or days[-1]!="2019-12-31":raise ValueError("time coverage "+str(len(days)))
                if any(len(js["daily"].get(v,[]))!=10592 for v in variables.split(",")):raise ValueError("missing variable")
                values[model]=js
                logs.append({"province":name,"model":model,"status":"complete","query":url,"sha256_response":hashlib.sha256(raw).hexdigest(),"returned_lat":js.get("latitude"),"returned_lon":js.get("longitude")})
                break
            except Exception as e:
                error=repr(e)
                if attempt<4:time.sleep(2+attempt*4+random.random())
        if model not in values:logs.append({"province":name,"model":model,"status":"failed","query":url,"error":error})
        time.sleep(.4)
    if len(values)!=2:continue
    ta=values["era5_land"]["daily"];pr=values["era5"]["daily"]
    if ta["time"]!=pr["time"]:raise ValueError("date mismatch")
    with gzip.open(out/(name.replace(" ","_").replace("/","_")+"_daily.csv.gz"),"wt",newline="") as f:
        w=csv.writer(f);w.writerow(["province","date","tmin_C","tmax_C","precip_mm","requested_lat","requested_lon"])
        for vals in zip([name]*10592,ta["time"],ta["temperature_2m_min"],ta["temperature_2m_max"],pr["precipitation_sum"],[lat]*10592,[lon]*10592):w.writerow(vals)
    print("DONE",name,10592,flush=True)
(out/"source_log.json").write_text(json.dumps(logs,indent=2,ensure_ascii=False))
print("FINISH",part,len(todo),sum(x["status"]=="complete" for x in logs),flush=True)
