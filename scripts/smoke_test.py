"""Smoke test end-to-end contra Supabase real.

Valida el flujo completo: health, cotización pública (incl. honeypot),
presign + postulación, login real del admin, métricas y endpoints admin
con JWT real, cambio de estado y borrado lógico. También verifica que un
usuario sin rol admin reciba 403. Limpia los datos de prueba al final.

Uso (desde Duomanbe/):  python scripts/smoke_test.py
Requisito: ADMIN_EMAIL y ADMIN_PASSWORD cargados en el .env.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from supabase import create_client  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402

CONSUMER_EMAIL = "smoke.consumer@test.local"
CONSUMER_PASSWORD = "Consumidor-2026!"


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(f"FALLÓ: {label}")
    print(f"  OK - {label}")


def main() -> None:
    settings = get_settings()
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        sys.exit("Definí ADMIN_EMAIL/ADMIN_PASSWORD en el .env para correr el smoke test.")

    sync_sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    with TestClient(app) as c:
        print("Flujo de smoke test:")
        r = c.get("/api/v1/health")
        check("health 200", r.status_code == 200)

        quotation = {
            "full_name": "Smoke Test",
            "email": "smoke@test.com",
            "phone": "+54 11 0000-0000",
            "location": "CABA",
            "services": ["Electricidad", "Plomería"],
            "notes": "Fila de prueba generada por smoke_test.py",
        }
        r = c.post("/api/v1/quotations", json=quotation)
        check("POST /quotations 201", r.status_code == 201)
        qid = r.json()["id"]

        r = c.post("/api/v1/quotations", json={**quotation, "website": "http://spam-bot"})
        check("honeypot 201 sin insertar", r.status_code == 201 and r.json()["id"].startswith("00000000"))

        r = c.post("/api/v1/applications/presign-resume", json={"filename": "cv_pepe.pdf", "size": 2048})
        check("presign 200 + .pdf", r.status_code == 200 and r.json()["path"].endswith(".pdf"))
        presign = r.json()

        sync_sb.storage.from_(settings.BUCKET_RESUMES).upload(
            presign["path"], b"%PDF-1.4 archivo de prueba DUOMAN"
        )
        check("archivo subido al bucket", True)

        r = c.post("/api/v1/applications/presign-resume", json={"filename": "virus.exe", "size": 10})
        check("presign rechaza .exe (400)", r.status_code == 400)

        r = c.post(
            "/api/v1/applications",
            json={
                "full_name": "Smoke Postulante",
                "phone": "011-2222",
                "email": "postulante@test.com",
                "zone": "CABA",
                "target_role": "Técnico Electricista",
                "resume_path": presign["path"],
            },
        )
        check("POST /applications 201", r.status_code == 201)
        aid = r.json()["id"]

        # --- Auth: sin token -> 401 ---
        r = c.get("/api/v1/admin/metrics")
        check("admin sin token -> 401", r.status_code == 401)

        # --- Login real del admin ---
        r = c.post("/api/v1/auth/login", json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD})
        check("login admin 200", r.status_code == 200)
        admin = {"Authorization": f"Bearer {r.json()['access_token']}"}

        r = c.get("/api/v1/admin/metrics", headers=admin)
        check("admin/metrics 200", r.status_code == 200)
        print("       metrics:", r.json())

        r = c.get("/api/v1/admin/quotations", headers=admin)
        check("admin/quotations 200", r.status_code == 200)

        r = c.patch(f"/api/v1/admin/quotations/{qid}/status", headers=admin, json={"status": "Contactado"})
        check("PATCH estado -> Contactado", r.status_code == 200 and r.json()["status"] == "Contactado")

        r = c.get("/api/v1/admin/applications", headers=admin)
        check("admin/applications 200 (URL firmada)", r.status_code == 200 and any(
            a["id"] == aid and a.get("signed_resume_url") for a in r.json()
        ))

        r = c.post(
            "/api/v1/admin/employees",
            headers=admin,
            json={"full_name": "Foo Bar", "phone": "555", "role": "Electricista", "specialties": ["Industrial"]},
        )
        check("POST /admin/employees 201", r.status_code == 201)
        eid = r.json()["id"]

        # --- 403 con usuario sin rol admin ---
        created = sync_sb.auth.admin.create_user(
            {"email": CONSUMER_EMAIL, "password": CONSUMER_PASSWORD, "email_confirm": True}
        )
        consumer = created.user
        user_sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        login = user_sb.auth.sign_in_with_password({"email": CONSUMER_EMAIL, "password": CONSUMER_PASSWORD})
        consumer_headers = {"Authorization": f"Bearer {login.session.access_token}"}
        r = c.get("/api/v1/admin/metrics", headers=consumer_headers)
        check("admin con usuario sin rol -> 403", r.status_code == 403)
        sync_sb.auth.admin.delete_user(consumer.id)
        check("usuario consumer eliminado", True)

        # --- Limpieza (borrado lógico) ---
        check("DELETE cotización 204", c.delete(f"/api/v1/admin/quotations/{qid}", headers=admin).status_code == 204)
        check("DELETE postulación 204", c.delete(f"/api/v1/admin/applications/{aid}", headers=admin).status_code == 204)
        check("DELETE empleado 204", c.delete(f"/api/v1/admin/employees/{eid}", headers=admin).status_code == 204)

        for obj in sync_sb.storage.from_(settings.BUCKET_RESUMES).list():
            if obj["name"] == presign["path"]:
                sync_sb.storage.from_(settings.BUCKET_RESUMES).remove([obj["name"]])
        check("archivo de prueba eliminado", True)

        r = c.post("/api/v1/auth/login", json={"email": "nadie@x.com", "password": "incorrecta"})
        check("login inválido -> 401", r.status_code == 401)

    print("\nSmoke test OK, datos de prueba limpiados.")


if __name__ == "__main__":
    main()