import json, ssl, subprocess, urllib.request, yaml
RAIZ="/mnt/c/Users/USER/Desktop/Universida/8vo/quickpatch"
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def api(host,m,ruta,cuerpo=None,token=None):
    r=urllib.request.Request(f"https://10.43.100.168{ruta}",method=m,data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    r.add_header("Host",host); r.add_header("Content-Type","application/json"); r.add_header("X-Channel-Id","quickpatch-mobile")
    if token: r.add_header("Authorization",f"Bearer {token}")
    try:
        with urllib.request.urlopen(r,context=ctx,timeout=20) as x: return x.status,json.loads(x.read() or b"null")
    except urllib.error.HTTPError as e: return e.code,None
o=subprocess.run(["docker","run","--rm","--entrypoint","ansible-vault","-v",f"{RAIZ}:/quickpatch","-w","/quickpatch/infrastructure/ansible","-v","/home/sebas/.config/quickpatch/vault-pass:/run/vault-pass:ro","-e","ANSIBLE_VAULT_PASSWORD_FILE=/run/vault-pass","-e","ANSIBLE_CONFIG=/quickpatch/infrastructure/ansible/ansible.cfg","quickpatch-ansible","view","inventory/group_vars/all/vault.yml"],stdout=subprocess.PIPE,text=True)
v=yaml.safe_load(o.stdout); a=v["vault_identity_admins"]["qa"]
c,b=api("qa.quickpatch.internal","POST","/api/v1/auth/login",{"email":a["admin_email"],"password":a["admin_password"]}); tok=b["accessToken"]; del a
print("token de QA contra QA  /api/v1/users/me:",api("qa.quickpatch.internal","GET","/api/v1/users/me",token=tok)[0])
print("token de QA contra PRODUCCIÓN /api/v1/users/me:",api("quickpatch.internal","GET","/api/v1/users/me",token=tok)[0])
print("sin token contra producción:",api("quickpatch.internal","GET","/api/v1/users/me")[0])
kq=v["vault_jwt_keys"]; print("llaves JWT por ambiente distintas:", kq["qa"]["public"]!=kq["produccion"]["public"] if "public" in kq.get("qa",{}) else list(kq.keys()))
