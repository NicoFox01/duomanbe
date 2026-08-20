"""create domain tables (quotations, applications, employees)

Revision ID: 0002_domain
Revises: 0001_cronjobs
Create Date: 2026-08-17

"""
from alembic import op

revision: str = "0002_domain"
down_revision: str | None = "0001_cronjobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------- ENUMS ----------
    op.execute(
        """
        CREATE TYPE quotation_status AS ENUM (
            'Pendiente',
            'Contactado',
            'Cotización Presentada',
            'Propuesta Confirmada',
            'Cancelada',
            'Rechazada'
        )
        """
    )
    op.execute(
        """
        CREATE TYPE candidate_status AS ENUM (
            'Postulado',
            'Visto',
            'Contactado',
            'Entrevistado',
            'No aplica',
            'Contratado'
        )
        """
    )
    op.execute(
        """
        CREATE TYPE residency_zone AS ENUM (
            'CABA',
            'GBA Norte',
            'GBA Sur',
            'GBA Oeste'
        )
        """
    )

    # ---------- QUOTATIONS ----------
    op.execute(
        """
        CREATE TABLE quotations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            full_name VARCHAR(150) NOT NULL,
            email VARCHAR(150) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            company VARCHAR(150),
            location VARCHAR(200) NOT NULL,
            services TEXT[] NOT NULL DEFAULT '{}',
            notes TEXT,
            status quotation_status NOT NULL DEFAULT 'Pendiente',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
        )
        """
    )

    # ---------- APPLICATIONS ----------
    op.execute(
        """
        CREATE TABLE applications (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            full_name VARCHAR(150) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            email VARCHAR(150) NOT NULL,
            zone residency_zone NOT NULL,
            target_role VARCHAR(150) NOT NULL,
            resume_url TEXT NOT NULL,
            status candidate_status NOT NULL DEFAULT 'Postulado',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
        )
        """
    )

    # ---------- EMPLOYEES ----------
    op.execute(
        """
        CREATE TABLE employees (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            full_name VARCHAR(150) NOT NULL,
            email VARCHAR(150),
            phone VARCHAR(50) NOT NULL,
            role VARCHAR(100) NOT NULL,
            specialties TEXT[] DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
        )
        """
    )

    # ---------- ÍNDICES ----------
    op.execute("CREATE INDEX idx_quotations_status ON quotations(status) WHERE is_active = TRUE")
    op.execute("CREATE INDEX idx_quotations_created_at ON quotations(created_at DESC)")

    op.execute("CREATE INDEX idx_applications_status ON applications(status) WHERE is_active = TRUE")
    op.execute("CREATE INDEX idx_applications_created_at ON applications(created_at DESC)")

    op.execute("CREATE INDEX idx_employees_created_at ON employees(created_at DESC)")

    # ---------- TRIGGER updated_at ----------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = timezone('utc'::text, now());
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for table in ("quotations", "applications", "employees"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """
        )

    # ---------- RLS (acceso solo vía service role) ----------
    for table in ("quotations", "applications", "employees", "cronjobs"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in ("quotations", "applications", "employees"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP TABLE IF EXISTS employees")
    op.execute("DROP TABLE IF EXISTS applications")
    op.execute("DROP TABLE IF EXISTS quotations")

    op.execute("DROP TYPE IF EXISTS residency_zone")
    op.execute("DROP TYPE IF EXISTS candidate_status")
    op.execute("DROP TYPE IF EXISTS quotation_status")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")