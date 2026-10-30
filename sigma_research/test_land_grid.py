import json,urllib.request,urllib.parse
data=[("Tarragona",41.11910287,1.2584219),("Barcelona",41.38424664,2.17634927),("Alicante",38.34548705,-0.4831832),("Cadiz",36.52171152,-6.28414575),("Tenerife",28.46285408,-16.24720629)]
for name,lat,lon in data:
 for model in ["era5_land","era5"]:
  p=dict(latitude=lat,longitude=lon,start_date="1991-01-01",end_date="1991-01-10",daily="temperature_2m_min,temperature_2m_max",models=model,timezone="Europe/Madrid",cell_selection="land")
  u="https://archive-api.open-meteo.com/v1/archive?"+urllib.parse.urlencode(p)
  try:
   with urllib.request.urlopen(u,timeout=80) as f: x=json.load(f)
   vals=x.get("daily",{}).get("temperature_2m_min",[]); print(name,model,"null",sum(v is None for v in vals),"values",vals[:4],"coords",x.get("latitude"),x.get("longitude"),"e",x.get("reason"),flush=True)
  except Exception as e: print(name,model,"ERROR",str(e),flush=True)
