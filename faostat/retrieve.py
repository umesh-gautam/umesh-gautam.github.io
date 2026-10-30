import csv,io,json,zipfile,hashlib,time
from urllib.request import Request,urlopen
from pathlib import Path
out=Path("out");out.mkdir(exist_ok=True)
urls=[
"https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip",
"https://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
]
raw=None;used=None;errors=[]
for url in urls:
 try:
  with urlopen(Request(url,headers={"User-Agent":"AcademicAgricultureResearch/1.0"}),timeout=160) as r:raw=r.read()
  if not zipfile.is_zipfile(io.BytesIO(raw)):raise ValueError("not a zip")
  used=url;break
 except Exception as e:errors.append(str(e))
if raw is None:
 (out/"FAILED.json").write_text(json.dumps({"errors":errors},indent=2));raise RuntimeError(str(errors))
z=zipfile.ZipFile(io.BytesIO(raw))
members=[n for n in z.namelist() if n.lower().endswith(".csv") and "all_data" in n.lower()]
if not members:raise RuntimeError("no normalized main CSV "+str(z.namelist()[:30]))
p=members[0]
print("SOURCE",used,"ZIP_BYTES",len(raw),"MEMBER",p,flush=True)
targets=("almond","hazelnut","pistachio","walnut","cashew","chestnut","brazil nut","pecan")
countries=("United States of America","Spain","Türkiye","Turkey","Iran (Islamic Republic of)","Australia","Georgia","Chile","China","Italy")
outfile=out/"FAOSTAT_TREE_NUT_OFFICIAL_1991_2019.csv"
n=0;counts={}
with z.open(p) as fd,open(outfile,"w",newline="",encoding="utf-8") as fo:
 txt=io.TextIOWrapper(fd,encoding="utf-8-sig",newline="")
 rd=csv.DictReader(txt);wr=csv.DictWriter(fo,fieldnames=rd.fieldnames);wr.writeheader()
 for r in rd:
  try:yr=int(r.get("Year","0"))
  except:continue
  if not 1991<=yr<=2019:continue
  area=r.get("Area","");item=r.get("Item","");el=r.get("Element","")
  if area not in countries or not any(q in item.lower() for q in targets):continue
  if el.lower() not in ("area harvested","production","yield"):continue
  wr.writerow(r);n+=1;counts[el]=counts.get(el,0)+1
meta={"origin":used,"zip_sha256":hashlib.sha256(raw).hexdigest(),"source_member":p,"rows":n,"by_element":counts,"errors":errors}
(out/"SOURCE_AND_COVERAGE.json").write_text(json.dumps(meta,indent=2))
print(json.dumps(meta),flush=True)
assert n>100,meta
