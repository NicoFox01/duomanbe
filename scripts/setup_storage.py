"""Crea el bucket privado `resumes` en Supabase Storage (idempotente).

Uso (desde la raíz del backend, Duomanbe/):
    python scripts/setup_storage.py

Usa la Service Role Key del .env.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from supabase import create_client  # noqa: E402

from app.core.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        sys.exit("Supabase no configurado. Revisá el .env.")

    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    bucket = settings.BUCKET_RESUMES
    existing = client.storage.list_buckets()
    if any(b.name == bucket for b in existing):
        print(f"El bucket '{bucket}' ya existe. Nada que hacer.")
        return

    client.storage.create_bucket(bucket, options={"public": False})
    print(f"Bucket privado '{bucket}' creado correctamente.")


if __name__ == "__main__":
    main()