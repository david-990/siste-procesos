"""Test completo: login -> subir imagen a /mapa -> verificar visualizacion desde B2"""
import requests
import re
import os

BASE = "http://127.0.0.1:5000"
s = requests.Session()

# 1. GET login page
r = s.get(f"{BASE}/login")
m = re.search(r'<input[^>]*name="_csrf_token"[^>]*value="([^"]+)"', r.text)
if not m:
    print("ERROR: No se encontro CSRF token en /login")
    exit(1)
csrf = m.group(1)
print("1. CSRF token obtenido de /login")

# 2. POST login
r = s.post(
    f"{BASE}/login",
    data={"username": "admin", "password": "admin123", "_csrf_token": csrf},
    allow_redirects=False,
)
print(f"2. Login status: {r.status_code}")
if r.status_code not in (302, 303):
    print("LOGIN FALLO!")
    print(r.text[:500])
    exit(1)

# 3. Follow redirect to panel
r = s.get(f"{BASE}/panel")
print(f"3. Panel cargado: {r.status_code}")

# 4. GET /mapa para nuevo CSRF token
r = s.get(f"{BASE}/mapa")
m = re.search(r'<input[^>]*name="_csrf_token"[^>]*value="([^"]+)"', r.text)
if m:
    csrf = m.group(1)
print("4. Pagina /mapa cargada")

# 5. Upload PNG a /mapa
png_path = "test_mapa.png"
if not os.path.exists(png_path):
    print(f"ERROR: No existe {png_path}")
    exit(1)

with open(png_path, "rb") as f:
    r = s.post(
        f"{BASE}/mapa",
        data={"_csrf_token": csrf},
        files={"imagen": ("test_mapa.png", f, "image/png")},
        allow_redirects=False,
    )
    print(f"5. Upload status: {r.status_code}")

    if r.status_code in (302, 303):
        # Follow redirect
        r = s.get(f"{BASE}/mapa")
        print(f"   /mapa post-upload: {r.status_code}")

        # Search for image tags
        imgs = re.findall(r'<img[^>]+>', r.text)
        if imgs:
            for img in imgs[:3]:
                print(f"   IMG tag: {img[:250]}")
        else:
            print("   No se encontraron tags <img> en la pagina")

        # Check for signed URL (B2)
        if "signed_url" in r.text or "X-Amz-Signature" in r.text or "AWSAccessKeyId" in r.text:
            print("   >>> IMAGEN SERVIDA DESDE B2/S3! <<<")
        elif "https://" in r.text and any(x in r.text for x in [".png", ".jpg", ".jpeg", ".webp"]):
            print("   Se encontro URL de imagen https en la pagina")
        elif "static/uploads" in r.text:
            print("   Imagen servida desde static/uploads (local)")
        else:
            print("   No se detecto URL de imagen en la pagina")
            # Check flash messages
            flashes = re.findall(r'class="[^"]*flash[^"]*"[^>]*>([^<]+)', r.text)
            if flashes:
                for f in flashes:
                    print(f"   Flash: {f}")
    else:
        print(f"   Response body: {r.text[:500]}")

print("\n--- PRUEBA COMPLETADA ---")
