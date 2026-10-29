#!/usr/bin/env python3
"""Actual, public reanalysis download; no synthetic values. Source: Open-Meteo ERA5-Land / ERA5."""
import csv, gzip, io, json, math, os, sys, time, random, hashlib, calendar
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import date, timedelta, datetime, timezone

ROOT=Path("weather_research")
ROOT.mkdir(exist_ok=True)
TARGET=sys.argv[1] if len(sys.argv)>1 else "USA"
PART=int(os.environ.get("WEATHER_PART","0")); NPARTS=int(os.environ.get("WEATHER_PARTS","1"))
OUT=Path("weather_output")/TARGET/("part_"+str(PART))
(OUT/"raw_regions").mkdir(parents=True,exist_ok=True)
BASE="https://archive-api.open-meteo.com/v1/archive"
CONFIG={
 "USA":{"timezone":"America/Los_Angeles","frost":[2,3],"heat":[5,6,7],"water":[4,5,6,7],"nut":"Almonds"},
 "TUR":{"timezone":"Europe/Istanbul","frost":[3,4],"heat":[6,7,8],"water":[4,5,6,7],"nut":"Hazelnuts"}
}
cfg=CONFIG[TARGET]
SRC={
 "ERA5_LAND_TEMPS_ET0":("era5_land","temperature_2m_min,temperature_2m_max,et0_fao_evapotranspiration"),
 "ERA5_PRECIP":("era5","precipitation_sum")
}
def retrieve(lat,lon,source):
    model,daily=SRC[source]
    params={"latitude":str(lat),"longitude":str(lon),"start_date":"1991-01-01",
            "end_date":"2019-12-31","daily":daily,"models":model,"timezone":cfg["timezone"],
            "temperature_unit":"celsius","precipitation_unit":"mm","cell_selection":"nearest"}
    url=BASE+"?"+urlencode(params)
    error=""
    for attempt in range(5):
        try:
            req=Request(url,headers={"User-Agent":"TreeNutWeatherAcademicStudy/1.0","Accept":"application/json"})
            with urlopen(req,timeout=110) as response:
                raw=response.read()
                data=json.loads(raw)
            if data.get("error"): raise ValueError("API error: "+str(data.get("reason")))
            days=data.get("daily",{}).get("time",[])
            start=date(1991,1,1);expected=(date(2020,1,1)-start).days
            if len(days)!=expected or days[0]!="1991-01-01" or days[-1]!="2019-12-31":
                raise ValueError("Incomplete days "+str(len(days)))
            for variable in daily.split(","):
                if variable not in data["daily"] or len(data["daily"][variable])!=expected:raise ValueError("missing "+variable)
            return data,{"source":source,"model":model,"request_url":url,"status":"complete",
                          "bytes":len(raw),"payload_sha256":hashlib.sha256(raw).hexdigest(),
                          "returned_lat":data.get("latitude"),"returned_lon":data.get("longitude"),
                          "returned_elevation_m":data.get("elevation")}
        except (HTTPError,URLError,TimeoutError,ValueError,json.JSONDecodeError) as e:
            error=type(e).__name__+": "+str(e)[:220]
            print("RETRY",source,round(lat,3),attempt,error,flush=True)
            if attempt<4:time.sleep(min(7*(2**attempt),65)+random.random()*3)
    return None,{"source":source,"model":model,"request_url":url,"status":"failed","error":error}
def read_rows(path):
    with open(path,newline="") as f:return list(csv.DictReader(f))
def write_csv(path,rows):
    if not rows:return
    cols=list(dict.fromkeys(k for row in rows for k in row))
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore");w.writeheader();w.writerows(rows)
def real(x):
    if x is None:return None
    try:return float(x)
    except (ValueError,TypeError):return None
def getvalue(dic,key,index):
    a=dic.get(key,[])
    return real(a[index]) if index<len(a) else None
sites=[r for i,r in enumerate([x for x in read_rows(ROOT/"pre2010_region_sites.csv") if x["country_iso3"]==TARGET]) if i%NPARTS==PART]
log=[];metrics=[];all_complete=0;total_daily=0
for pos,s in enumerate(sites,1):
    region=s["region"];lat=float(s["latitude"]);lon=float(s["longitude"])
    print(f"START {TARGET} {pos}/{len(sites)} {region}",flush=True)
    sources={}
    for src in SRC:
        payload,info=retrieve(lat,lon,src)
        info.update({"exporter_iso3":TARGET,"nut_name":cfg["nut"],"region":region,
                      "requested_lat":lat,"requested_lon":lon,"weight":s["pre2010_orchard_weight"]})
        log.append(info)
        if payload is not None:sources[src]=payload
        time.sleep(1.1)
    if len(sources)!=2:continue
    temp=sources["ERA5_LAND_TEMPS_ET0"]["daily"]
    prec=sources["ERA5_PRECIP"]["daily"]
    if temp["time"]!=prec["time"]:raise ValueError("ERA5 vs ERA5Land date mismatch "+region)
    rows=[]
    for idx,day in enumerate(temp["time"]):
        rows.append({"exporter_iso3":TARGET,"nut_name":cfg["nut"],"region":region,"date":day,
                     "latitude_requested":lat,"longitude_requested":lon,
                     "pre2010_orchard_weight":s["pre2010_orchard_weight"],
                     "tmin_C":getvalue(temp,"temperature_2m_min",idx),
                     "tmax_C":getvalue(temp,"temperature_2m_max",idx),
                     "et0_mm":getvalue(temp,"et0_fao_evapotranspiration",idx),
                     "precip_mm":getvalue(prec,"precipitation_sum",idx),
                     "source_temperature":"ERA5-Land via Open-Meteo",
                     "source_precipitation":"ERA5 via Open-Meteo"})
    p=OUT/"raw_regions"/(TARGET+"_"+region.replace(" ","_")+"_daily_1991_2019.csv.gz")
    with gzip.open(p,"wt",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    all_complete+=1;total_daily+=len(rows)
    for year in range(1991,2020):
        yrows=[r for r in rows if r["date"].startswith(str(year)+"-")]
        d={"exporter_iso3":TARGET,"nut_name":cfg["nut"],"region":region,
           "year":year,"weight_2008":s["pre2010_orchard_weight"],
           "area_2008":s["area_2008"],"latitude":lat,"longitude":lon,
           "source":"OPENMETEO_ERA5LAND_TEMP_ET0_PLUS_ERA5_PRECIP",
           "spatial_method":"2008 fixed acreage weighted administrative CENTROIDS"}
        phases={"frost":cfg["frost"],"heat":cfg["heat"],"water":cfg["water"]}
        calc={}
        for ph,months in phases.items():
            grp=[r for r in yrows if int(r["date"][5:7]) in months]
            expected=sum(calendar.monthrange(year,m)[1] for m in months)
            calc[ph]=grp
            d[f"{ph}_daily_valid"]=len(grp)==expected and len({r["date"] for r in grp})==expected
        def enough(a,key):
            values=[r[key] for r in a if r[key] is not None]
            return len(values)>=0.99*len(a) and len(a)>0
        f=calc["frost"];h=calc["heat"];w=calc["water"]
        d["frost_degree_days_below2"]=sum(max(2-r["tmin_C"],0) for r in f) if d["frost_daily_valid"] and enough(f,"tmin_C") and all(r["tmin_C"] is not None for r in f) else ""
        d["frost_days_below0"]=sum(r["tmin_C"]<0 for r in f) if d["frost_daily_valid"] and all(r["tmin_C"] is not None for r in f) else ""
        d["heat_degree_days_above35"]=sum(max(r["tmax_C"]-35,0) for r in h) if d["heat_daily_valid"] and all(r["tmax_C"] is not None for r in h) else ""
        d["heat_days_ge35"]=sum(r["tmax_C"]>=35 for r in h) if d["heat_daily_valid"] and all(r["tmax_C"] is not None for r in h) else ""
        d["water_precip_mm"]=sum(r["precip_mm"] for r in w) if d["water_daily_valid"] and all(r["precip_mm"] is not None for r in w) else ""
        d["water_et0_mm"]=sum(r["et0_mm"] for r in w) if d["water_daily_valid"] and all(r["et0_mm"] is not None for r in w) else ""
        d["water_precip_minus_et0_mm"]=(d["water_precip_mm"]-d["water_et0_mm"]) if isinstance(d["water_precip_mm"],float) and isinstance(d["water_et0_mm"],float) else ""
        d["n_daily_rows"]=len(yrows)
        metrics.append(d)
    del rows
    write_csv(OUT/"region_year_checkpoint.csv",metrics)
    write_csv(OUT/"source_request_log_checkpoint.csv",log)
    print("COMPLETED",TARGET,region,"days",len(temp["time"]),flush=True)
write_csv(OUT/"region_year_weather_1991_2019.csv",metrics)
write_csv(OUT/"source_request_log.csv",log)
status={"status":"complete" if all_complete==len(sites) else "partial",
        "country":TARGET,"sites_complete":all_complete,"sites_target":len(sites),
        "real_daily_rows":total_daily,"real_region_year_rows":len(metrics),
        "generated_utc":datetime.now(timezone.utc).isoformat(),
        "source_temperature":"Open-Meteo ERA5-Land temperature/ET0",
        "source_precipitation":"Open-Meteo ERA5 (coarser than ERA5-Land)",
        "spatial_method":"administrative centroid; not true orchard pixels"}
(OUT/"STATUS.json").write_text(json.dumps(status,indent=2))
print("FINAL",json.dumps(status),flush=True)
