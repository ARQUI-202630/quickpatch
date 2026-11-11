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
print(now(),"línea base Catalog:",activas()); print(now(),"réplica:",replica())
t0=time.time(); print(now(),"escalando service-request a 0"); ans("playbooks/_tmp-escalar.yml","-e","ambiente=qa","-e","servicio=service-request","-e","replicas=0")
for i in range(12):
    c,_=api("GET","/api/v1/service-requests/categories")
    if c!=200: break
    time.sleep(3)
print(now(),"con el consumidor en 0, la ruta responde HTTP",c)
ids=[]
for n in ["Zz AC5-E3 prueba A","Zz AC5-E3 prueba B","Zz AC5-E3 prueba C"]:
    c,r=api("POST","/api/v1/catalog/admin/categories",{"name":n,"description":"prueba AC5-E3, se borra"},adm); print(now(),"crear",n,c)
    if isinstance(r,dict): ids.append(r.get("id"))
if len(ids)>=2:
    print(now(),"desactivar B",api("PATCH",f"/api/v1/catalog/admin/categories/{ids[1]}",{"active":False},adm)[0])
esperadas=activas(); print(now(),"Catalog activas ahora:",len(esperadas),"; incluye pruebas:",[n for n in esperadas if n.startswith("Zz")])
time.sleep(10); print(now(),"lag del grupo con el consumidor caído:"); [print("   ",l) for l in lag()]
t1=time.time(); print(now(),"subiendo service-request a 1"); ans("playbooks/_tmp-escalar.yml","-e","ambiente=qa","-e","servicio=service-request","-e","replicas=1")
ok=None
for i in range(60):
    c,r=replica()
    if c==200 and r==esperadas: ok=time.time()-t1; break
    time.sleep(3)
print(now(),"réplica igual a Catalog tras",None if ok is None else f"{ok:.0f} s","| réplica:",len(r) if isinstance(r,list) else r)
print(now(),"lag después:"); [print("   ",l) for l in lag()]
for i in ids: api("PATCH",f"/api/v1/catalog/admin/categories/{i}",{"active":False},adm)
time.sleep(8); print(now(),"limpieza: Catalog",len(activas()),"réplica",len(replica()[1]) if isinstance(replica()[1],list) else replica())
