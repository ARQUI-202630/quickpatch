"""SCRUM-644 en QA: llave pública, login con encryptedPassword, llave desconocida y contraseña en claro. No imprime claves."""
import json, ssl, subprocess, base64, urllib.request, yaml
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
RAIZ="/mnt/c/Users/USER/Desktop/Universida/8vo/quickpatch"
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def api(m,ruta,cuerpo=None,token=None):
    r=urllib.request.Request(f"https://10.43.100.168{ruta}",method=m,data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    r.add_header("Host","qa.quickpatch.internal"); r.add_header("Content-Type","application/json"); r.add_header("X-Channel-Id","quickpatch-mobile")
    try:
        with urllib.request.urlopen(r,context=ctx,timeout=30) as x: return x.status,json.loads(x.read() or b"null")
    except urllib.error.HTTPError as e:
        try: return e.code,json.loads(e.read() or b"null")
        except Exception: return e.code,None
c,k=api("GET","/v1/auth/password-key") if False else api("GET","/api/v1/auth/password-key")
print("GET password-key:",c,{x:(v if x!='publicKey' else v[:30]+'…') for x,v in (k or {}).items()})
o=subprocess.run(["docker","run","--rm","--entrypoint","ansible-vault","-v",f"{RAIZ}:/quickpatch","-w","/quickpatch/infrastructure/ansible","-v","/home/sebas/.config/quickpatch/vault-pass:/run/vault-pass:ro","-e","ANSIBLE_VAULT_PASSWORD_FILE=/run/vault-pass","-e","ANSIBLE_CONFIG=/quickpatch/infrastructure/ansible/ansible.cfg","quickpatch-ansible","view","inventory/group_vars/all/vault.yml"],stdout=subprocess.PIPE,text=True)
a=yaml.safe_load(o.stdout)["vault_identity_admins"]["qa"]; em,pw=a["admin_email"],a["admin_password"]; del a
pub=serialization.load_der_public_key(base64.b64decode(k["publicKey"]))
def enc(p): return base64.b64encode(pub.encrypt(p.encode(),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))).decode()
c,b=api("POST","/api/v1/auth/login",{"email":em,"encryptedPassword":{"keyId":k["keyId"],"ciphertext":enc(pw)}}); print("login cifrado:",c,"token" if b and b.get("accessToken") else b)
c,b=api("POST","/api/v1/auth/login",{"email":em,"encryptedPassword":{"keyId":"no-existe","ciphertext":enc(pw)}}); print("llave desconocida:",c,b)
c,b=api("POST","/api/v1/auth/login",{"email":em,"encryptedPassword":{"keyId":k["keyId"],"ciphertext":enc(pw+'x')}}); print("clave mala cifrada:",c)
c,b=api("POST","/api/v1/auth/login",{"email":em,"password":pw}); print("clave en claro (compatibilidad):",c)
