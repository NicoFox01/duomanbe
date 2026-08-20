"""Asigna/verifica el rol del admin en Supabase Auth (app_metadata.role).

Uso (desde la raíz del backend, Duomanbe/):
    python scripts/set_admin_role.py                      -> lista usuarios y su rol actual
    python scripts/set_admin_role.py <email>              -> setea app_metadata.role = "admin"
    python scripts/set_admin_role.py <email> <rol>        -> setea otro rol (ej: consumer)

Usa la Service Role Key. NO exponer este script en el frontend.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.supabase import get_supabase_service_client  # noqa: E402


def extract(resp):
    if hasattr(resp, "model_dump"):
        return resp.model_dump()
    if hasattr(resp, "dict"):
        return resp.dict()
    return resp


def as_dict(user):
    if isinstance(user, dict):
        return user
    if hasattr(user, "model_dump"):
        return user.model_dump()
    return {"id": getattr(user, "id"), "email": getattr(user, "email", ""), "app_metadata": getattr(user, "app_metadata", None)}


def main() -> None:
    email_arg = sys.argv[1] if len(sys.argv) > 1 else None
    role_arg = sys.argv[2] if len(sys.argv) > 2 else "admin"

    client = get_supabase_service_client()
    if client is None:
        sys.exit("Supabase no configurado. Revisá DUOMAN .env (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY).")

    data = extract(client.auth.admin.list_users())
    users = data.get("users", data) if isinstance(data, dict) else data

    if not email_arg:
        print("Usuarios actuales en Supabase Auth:")
        for u in users:
            u = as_dict(u)
            md = u.get("app_metadata") or {}
            role = md.get("role", "SIN ROL")
            print(f"  - {u.get('email')!r:40} id={u.get('id')}  rol={role!r}")
        return

    target = next((as_dict(u) for u in users if as_dict(u).get("email") == email_arg), None)
    if target is None:
        sys.exit(f"No se encontró el usuario con email {email_arg!r}. Listado:\n  " + "\n  ".join(as_dict(u).get("email", "") for u in users))

    user_id = target["id"]
    app_metadata = dict(target.get("app_metadata") or {})

    if app_metadata.get("role") == role_arg:
        print(f"El usuario {email_arg!r} ya tiene rol {role_arg!r}. Nada que hacer.")
        return

    resp = client.auth.admin.update_user_by_id(user_id, {"app_metadata": {**app_metadata, "role": role_arg}})
    updated = extract(resp)
    print(f"Rol asignado: {email_arg!r} -> role={updated.get('app_metadata', {}).get('role')!r}")

    if role_arg == "admin":
        print("Recordá volver a loguearte (o re-sign in) para que el JWT incluya el nuevo role.")


if __name__ == "__main__":
    main()