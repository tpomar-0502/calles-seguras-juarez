"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-11-24 20:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("correo", sa.String(150), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "rol",
            sa.Enum("CIUDADANO", "MODERADOR", "COORDINADOR", "ENLACE_MUNICIPAL", name="rolusuario"),
            nullable=False,
        ),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("acepto_privacidad", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usuarios_correo", "usuarios", ["correo"])

    op.create_table(
        "sectores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(80), nullable=False, unique=True),
        sa.Column("descripcion", sa.String(255), nullable=True),
    )

    op.create_table(
        "colonias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("codigo_postal", sa.String(10), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sector_id", sa.Integer(), sa.ForeignKey("sectores.id"), nullable=False),
        sa.UniqueConstraint("nombre", "sector_id", name="uq_colonia_sector"),
    )
    op.create_index("ix_colonias_nombre", "colonias", ["nombre"])

    op.create_table(
        "usuario_colonias_interes",
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("colonia_id", sa.Integer(), sa.ForeignKey("colonias.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "reportes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("folio", sa.String(25), nullable=False, unique=True),
        sa.Column("categoria", sa.Enum("BACHE", "ENCHARCAMIENTO", name="categoriareporte"), nullable=False),
        sa.Column(
            "estado",
            sa.Enum(
                "RECIBIDO",
                "VALIDADO",
                "PROGRAMADO",
                "EN_REPARACION",
                "REPARADO",
                "RECHAZADO",
                "ACTIVO",
                "HISTORICO",
                name="estadoreporte",
            ),
            nullable=False,
        ),
        sa.Column("calle", sa.String(180), nullable=False),
        sa.Column("referencia", sa.String(200), nullable=True),
        sa.Column("latitud", sa.Float(), nullable=False),
        sa.Column("longitud", sa.Float(), nullable=False),
        sa.Column("colonia_id", sa.Integer(), sa.ForeignKey("colonias.id"), nullable=False),
        sa.Column(
            "tipo_dano",
            sa.Enum("BACHE", "HUNDIMIENTO", "GRIETA", "ALCANTARILLA_SIN_TAPA", name="tipodanobache"),
            nullable=True,
        ),
        sa.Column("tamano_bache", sa.String(40), nullable=True),
        sa.Column("profundidad_aprox", sa.String(40), nullable=True),
        sa.Column("carril_afectado", sa.String(60), nullable=True),
        sa.Column("severidad", sa.Enum("BAJA", "MEDIA", "ALTA", name="severidadbache"), nullable=True),
        sa.Column("alcantarilla_senalizada", sa.Boolean(), nullable=True),
        sa.Column(
            "nivel_agua",
            sa.Enum("LADO_CALLE", "UN_CARRIL", "MEDIA_LLANTA", "INTRANSITABLE", name="nivelagua"),
            nullable=True,
        ),
        sa.Column("riesgo_vehiculos_personas", sa.Boolean(), nullable=True),
        sa.Column("vigente_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("descripcion", sa.String(500), nullable=False),
        sa.Column("fecha_reporte", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_reparacion", sa.Date(), nullable=True),
        sa.Column("motivo_rechazo", sa.String(255), nullable=True),
        sa.Column("folio_principal_id", sa.Integer(), sa.ForeignKey("reportes.id"), nullable=True),
        sa.Column("autor_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
    )
    op.create_index("ix_reportes_folio", "reportes", ["folio"])
    op.create_index("ix_reportes_estado", "reportes", ["estado"])
    op.create_index("ix_reportes_categoria", "reportes", ["categoria"])

    op.create_table(
        "historial_estados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporte_id", sa.Integer(), sa.ForeignKey("reportes.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "estado_anterior",
            sa.Enum(
                "RECIBIDO",
                "VALIDADO",
                "PROGRAMADO",
                "EN_REPARACION",
                "REPARADO",
                "RECHAZADO",
                "ACTIVO",
                "HISTORICO",
                name="estadoreporte",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "estado_nuevo",
            sa.Enum(
                "RECIBIDO",
                "VALIDADO",
                "PROGRAMADO",
                "EN_REPARACION",
                "REPARADO",
                "RECHAZADO",
                "ACTIVO",
                "HISTORICO",
                name="estadoreporte",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("comentario_publico", sa.Text(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("fecha_cambio", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "interacciones_reporte",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporte_id", sa.Integer(), sa.ForeignKey("reportes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.Enum("CONFIRMACION", "DESMENTIDO", name="tipointeraccion"), nullable=False),
        sa.Column("ciclo_vigencia", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("interacciones_reporte")
    op.drop_table("historial_estados")
    op.drop_table("reportes")
    op.drop_table("usuario_colonias_interes")
    op.drop_table("colonias")
    op.drop_table("sectores")
    op.drop_table("usuarios")