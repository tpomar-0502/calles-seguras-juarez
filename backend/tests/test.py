import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models import Colonia, RolUsuario, Sector, Usuario

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    sec = Sector(nombre="Centro-Norte")
    db.add(sec)
    db.flush()
    col = Colonia(nombre="Zona Centro", codigo_postal="32000", sector_id=sec.id, activa=True)
    db.add(col)
    db.add(
        Usuario(
            nombre="Moderador Test",
            correo="mod@test.com",
            password_hash=get_password_hash("Juarez2026!"),
            rol=RolUsuario.MODERADOR,
            activo=True,
        )
    )
    db.add(
        Usuario(
            nombre="Coordinador Test",
            correo="coord@test.com",
            password_hash=get_password_hash("Juarez2026!"),
            rol=RolUsuario.COORDINADOR,
            activo=True,
        )
    )
    db.commit()
    db.close()
    yield


def obtener_token(correo: str, password: str = "Juarez2026!") -> str:
    res = client.post("/api/v1/auth/login", data={"username": correo, "password": password})
    return res.json()["access_token"]


def test_01_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_02_registro_ciudadano_exitoso():
    res = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Omar Ciudadano",
            "correo": "omar@test.com",
            "password": "Password123",
            "acepto_privacidad": True,
        },
    )
    assert res.status_code == 201
    assert res.json()["usuario"]["rol"] == "ciudadano"


def test_03_registro_rechaza_password_debil():
    res = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Omar",
            "correo": "omar2@test.com",
            "password": "abc",
            "acepto_privacidad": True,
        },
    )
    assert res.status_code == 422


def test_04_crear_reporte_bache_en_juarez():
    client.post(
        "/api/v1/auth/register",
        json={"nombre": "C1", "correo": "c1@test.com", "password": "Password123", "acepto_privacidad": True},
    )
    token = obtener_token("c1@test.com", "Password123")
    res = client.post(
        "/api/v1/reportes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "categoria": "bache",
            "calle": "Av. 16 de Septiembre #500",
            "latitud": 31.7385,
            "longitud": -106.4850,
            "colonia_id": 1,
            "tipo_dano": "bache",
            "tamano_bache": "mediano",
            "profundidad_aprox": "10 cm",
            "carril_afectado": "Derecho",
            "descripcion": "Bache profundo frente a comercio",
        },
    )
    assert res.status_code == 201
    assert res.json()["folio"].startswith("BCH-")
    assert res.json()["estado"] == "Recibido"


def test_05_rechazar_reporte_fuera_de_juarez():
    client.post(
        "/api/v1/auth/register",
        json={"nombre": "C2", "correo": "c2@test.com", "password": "Password123", "acepto_privacidad": True},
    )
    token = obtener_token("c2@test.com", "Password123")
    res = client.post(
        "/api/v1/reportes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "categoria": "encharcamiento",
            "calle": "Calle El Paso TX",
            "latitud": 31.95,
            "longitud": -106.48,
            "colonia_id": 1,
            "nivel_agua": "cubre un carril",
            "descripcion": "Fuera de municipio",
        },
    )
    assert res.status_code == 400


def test_06_control_acceso_ciudadano_no_puede_validar():
    client.post(
        "/api/v1/auth/register",
        json={"nombre": "C3", "correo": "c3@test.com", "password": "Password123", "acepto_privacidad": True},
    )
    token_c = obtener_token("c3@test.com", "Password123")
    creado = client.post(
        "/api/v1/reportes",
        headers={"Authorization": f"Bearer {token_c}"},
        json={
            "categoria": "bache",
            "calle": "Av. Tecnológico #1200",
            "latitud": 31.72,
            "longitud": -106.45,
            "colonia_id": 1,
            "tipo_dano": "grieta",
            "descripcion": "Grieta longitudinal",
        },
    ).json()

    res = client.patch(
        f"/api/v1/reportes/{creado['folio']}/estado",
        headers={"Authorization": f"Bearer {token_c}"},
        json={"estado_nuevo": "Validado"},
    )
    assert res.status_code == 403


def test_07_moderador_valida_reporte_y_guarda_historial():
    client.post(
        "/api/v1/auth/register",
        json={"nombre": "C4", "correo": "c4@test.com", "password": "Password123", "acepto_privacidad": True},
    )
    token_c = obtener_token("c4@test.com", "Password123")
    creado = client.post(
        "/api/v1/reportes",
        headers={"Authorization": f"Bearer {token_c}"},
        json={
            "categoria": "bache",
            "calle": "Av. Juárez #200",
            "latitud": 31.74,
            "longitud": -106.48,
            "colonia_id": 1,
            "tipo_dano": "alcantarilla_sin_tapa",
            "alcantarilla_senalizada": False,
            "descripcion": "Alcantarilla abierta sin señalizar",
        },
    ).json()
    assert creado["severidad"] == "Alta"

    token_m = obtener_token("mod@test.com")
    val = client.patch(
        f"/api/v1/reportes/{creado['folio']}/estado",
        headers={"Authorization": f"Bearer {token_m}"},
        json={"estado_nuevo": "Validado", "comentario_publico": "Confirmado en campo"},
    )
    assert val.status_code == 200
    assert val.json()["estado"] == "Validado"
    assert len(val.json()["historial"]) == 2


def test_08_deteccion_duplicado_cercano():
    client.post(
        "/api/v1/auth/register",
        json={"nombre": "C5", "correo": "c5@test.com", "password": "Password123", "acepto_privacidad": True},
    )
    token_c = obtener_token("c5@test.com", "Password123")
    client.post(
        "/api/v1/reportes",
        headers={"Authorization": f"Bearer {token_c}"},
        json={
            "categoria": "bache",
            "calle": "Calle Ignacio Mejía #400",
            "latitud": 31.7390,
            "longitud": -106.4530,
            "colonia_id": 1,
            "tipo_dano": "hundimiento",
            "descripcion": "Hundimiento en carril central",
        },
    )
    dup = client.get("/api/v1/reportes/verificar-duplicados?categoria=bache&lat=31.7391&lon=-106.4530")
    assert dup.status_code == 200
    assert len(dup.json()) == 1


def test_09_tablero_indicadores_protegido():
    token_coord = obtener_token("coord@test.com")
    res = client.get("/api/v1/admin/tablero", headers={"Authorization": f"Bearer {token_coord}"})
    assert res.status_code == 200
    assert "total_reportes" in res.json()


def test_10_exportacion_xml_anonima():
    token_coord = obtener_token("coord@test.com")
    res = client.get("/api/v1/admin/exportar?formato=xml", headers={"Authorization": f"Bearer {token_coord}"})
    assert res.status_code == 200
    assert "application/xml" in res.headers["content-type"]