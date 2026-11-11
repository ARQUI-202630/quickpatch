import json, ssl, subprocess, time, urllib.request, yaml, datetime
RAIZ="/mnt/c/Users/USER/Desktop/Universida/8vo/quickpatch"; AP="/home/sebas/.config/quickpatch/ap-lab.sh"; ANS=RAIZ+"/infrastructure/ansible"
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def api(m,ruta,cuerpo=None,token=None):
    r=urllib.request.Request(f"https://10.43.100.168{ruta}",method=m,data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    r.add_header("Host","qa.quickpatch.internal"); r.add_header("Content-Type","application/json"); r.add_header("X-Channel-Id","quickpatch-mobile")
    if token: r.add_header("Authorization",f"Bearer {token}")
    try:
        with urllib.request.urlopen(r,context=ctx,timeout=20) as x: return x.status,json.loads(x.read() or b"null")
    except urllib.error.HTTPError as e: return e.code,None
    except Exception as e: return 0,str(e)
def ans(pb,*extra):
    return subprocess.run([AP,pb,*extra],cwd=ANS,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300).stdout
def now(): return datetime.datetime.now().strftime("%H:%M:%S")
def pend():
    o=ans("playbooks/_tmp-kafka.yml"); import re
    m=re.search(r"\"(\d+\|\d+)\"",o); return m.group(1) if m else o[-300:]
def lag(): 
    o=ans("playbooks/_tmp-lag.yml","-e","grupo=service-request"); 
    return [l.strip().strip('",') for l in o.splitlines() if "catalog.category" in l or "GROUP" in l][:4]
o=subprocess.run(["docker","run","--rm","--entrypoint","ansible-vault","-v",f"{RAIZ}:/quickpatch","-w","/quickpatch/infrastructure/ansible","-v","/home/sebas/.config/quickpatch/vault-pass:/run/vault-pass:ro","-e","ANSIBLE_VAULT_PASSWORD_FILE=/run/vault-pass","-e","ANSIBLE_CONFIG=/quickpatch/infrastructure/ansible/ansible.cfg","quickpatch-ansible","view","inventory/group_vars/all/vault.yml"],stdout=subprocess.PIPE,text=True)
a=yaml.safe_load(o.stdout)["vault_identity_admins"]["qa"]
c,b=api("POST","/api/v1/auth/login",{"email":a["admin_email"],"password":a["admin_password"]}); adm=b["accessToken"]; del a
def activas(): 
    c,x=api("GET","/api/v1/catalog/categories",token=adm); return sorted(i["name"] for i in x)
def replica():
    c,x=api("GET","/api/v1/service-requests/categories"); return c,(sorted(i["name"] for i in x) if isinstance(x,list) else x)

print(now(),"línea base: Catalog",len(activas()),"réplica",len(replica()[1]),"outbox pendientes|total",pend())
ids=[]
try:
    t0=time.time(); print(now(),"deteniendo Kafka (vm7)"); print(ans("playbooks/_tmp-kafka.yml","-e","accion=stop")[-120:].strip().splitlines()[-1])
    for n in ["Zz AC5-E4 prueba A","Zz AC5-E4 prueba B","Zz AC5-E4 prueba C","Zz AC5-E4 prueba D"]:
        c,r=api("POST","/api/v1/catalog/admin/categories",{"name":n,"description":"prueba AC5-E4, se borra"},adm); print(now(),"crear con Kafka caído",n,c)
        if isinstance(r,dict): ids.append(r.get("id"))
    time.sleep(15); print(now(),"outbox pendientes|total con Kafka caído:",pend())
finally:
    t1=time.time(); print(now(),"iniciando Kafka"); ans("playbooks/_tmp-kafka.yml","-e","accion=start")
esperadas=activas()
ok=None
for i in range(80):
    p=pend()
    if p.split("|")[0]=="0": ok=time.time()-t1; break
    time.sleep(5)
print(now(),"pendientes tras reiniciar Kafka:",p,"en",None if ok is None else f"{ok:.0f} s","sin intervención")
for i in range(40):
    c,r=replica()
    if c==200 and r==esperadas: print(now(),"réplica de ServiceRequest igual a Catalog:",len(r)); break
    time.sleep(3)
else: print(now(),"réplica distinta",c,r)
for i in ids: api("PATCH",f"/api/v1/catalog/admin/categories/{i}",{"active":False},adm)
time.sleep(10); print(now(),"limpieza: Catalog",len(activas()),"réplica",len(replica()[1]),"outbox",pend())
