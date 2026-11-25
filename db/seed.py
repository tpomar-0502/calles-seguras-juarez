"""
Script de datos semilla (RNF-09).
Fuente del catálogo de colonias de Ciudad Juárez, Chihuahua:
Servicio Postal Mexicano (SEPOMEX) - Catálogo Nacional de Códigos Postales (Municipio 037 Juárez)
e Instituto Municipal de Investigación y Planeación (IMIP) de Ciudad Juárez.
"""
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import bcrypt
from app.core.database import SessionLocal
from app.models import (
    CategoriaReporte,
    Colonia,
    EstadoReporte,
    HistorialEstado,
    InteraccionReporte,
    NivelAgua,
    Reporte,
    RolUsuario,
    Sector,
    SeveridadBache,
    TipoDanoBache,
    TipoInteraccion,
    Usuario,
)

TZ_JUAREZ = ZoneInfo("America/Ciudad_Juarez")
import bcrypt

# 24 colonias reales de Ciudad Juárez con coordenadas reales aproximadas
COLONIAS_JUAREZ = [
    # Sector Centro-Norte
    ("Zona Centro", "32000", "Centro-Norte", 31.7385, -106.4850, "Av. 16 de Septiembre"),
    ("Partido Romero", "32030", "Centro-Norte", 31.7320, -106.4630, "Av. Hermanos Escobar"),
    ("Pronaf Condominio La Plata", "32315", "Centro-Norte", 31.7435, -106.4470, "Av. Benjamín Franklin"),
    ("Margaritas", "32300", "Centro-Norte", 31.7390, -106.4530, "Calle Ignacio Mejía"),
    ("El Barreal", "32040", "Centro-Norte", 31.7250, -106.4710, "Av. Vicente Guerrero"),
    ("Hidalgo", "32300", "Centro-Norte", 31.7360, -106.4690, "Calle Costa Rica"),
    # Sector Poniente
    ("Felipe Ángeles", "32100", "Poniente", 31.7475, -106.5180, "Calle Bernardo Norzagaray"),
    ("Altavista", "32120", "Poniente", 31.7340, -106.5090, "Calle Begonias"),
    ("Bellavista", "32130", "Poniente", 31.7410, -106.5010, "Calle Mariano Matamoros"),
    ("Chaveña", "32060", "Poniente", 31.7280, -106.4920, "Calle Libertad"),
    ("Plutarco Elías Calles", "32150", "Poniente", 31.7190, -106.5120, "Calle Isla Carolina"),
    ("Anapra", "32107", "Poniente", 31.7690, -106.5540, "Calle Rancho Anapra"),
    # Sector Sur-Oriente
    ("Campos Elíseos", "32472", "Sur-Oriente", 31.7095, -106.3820, "Blvd. Tomás Fernández"),
    ("Parque Industrial Antonio J. Bermúdez", "32470", "Sur-Oriente", 31.7180, -106.3950, "Av. Antonio J. Bermúdez"),
    ("Pradera Dorada", "32618", "Sur-Oriente", 31.6850, -106.4050, "Av. Ejército Nacional"),
    ("Satélite", "32540", "Sur-Oriente", 31.6940, -106.3890, "Av. Manuel Gómez Morín"),
    ("Valle del Sol", "32546", "Sur-Oriente", 31.6820, -106.3710, "Av. Valle del Sol"),
    ("Las Torres", "32575", "Sur-Oriente", 31.6350, -106.3780, "Av. de las Torres"),
    # Sector Sur
    ("Inf. Casas Grandes", "32600", "Sur", 31.6780, -106.4320, "Av. Tecnológico"),
    ("Nuevo Hipódromo", "32685", "Sur", 31.6620, -106.4280, "Blvd. Óscar Flores"),
    ("Zaragoza", "32550", "Sur", 31.6480, -106.3490, "Av. Waterfill"),
    ("Parajes del Sur", "32575", "Sur", 31.5920, -106.3840, "Blvd. Zaragoza"),
    ("Senderos de San Isidro", "32575", "Sur", 31.5840, -106.3650, "Av. Miguel de la Madrid"),
    ("Kilómetro 20", "32695", "Sur", 31.6080, -106.4410, "Carretera Panamericana"),
]


def run_seed():
    db = SessionLocal()
    try:
        if db.query(Usuario).count() > 0:
            print("Seed ya aplicado previamente. Omitiendo.")
            return

        print("Insertando usuarios de prueba por rol...")
        hashed = bcrypt.hashpw("Juarez2026!".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        usuarios_data = [
            ("Ana Ciudadana", "ciudadano@callesjuarez.org", RolUsuario.CIUDADANO),
            ("Carlos Moderador", "moderador@callesjuarez.org", RolUsuario.MODERADOR),
            ("Laura Coordinadora", "coordinador@callesjuarez.org", RolUsuario.COORDINADOR),
            ("Ing. Roberto Enlace", "enlace@juarez.gob.mx", RolUsuario.ENLACE_MUNICIPAL),
            ("Vecino Juárez 2", "vecino2@callesjuarez.org", RolUsuario.CIUDADANO),
        ]
        usuarios = []
        for nombre, correo, rol in usuarios_data:
            u = Usuario(nombre=nombre, correo=correo, password_hash=hashed, rol=rol, activo=True, acepto_privacidad=True)
            db.add(u)
            usuarios.append(u)
        db.flush()

        print("Insertando sectores y 24 colonias reales de Ciudad Juárez...")
        sectores_map = {}
        for _, _, sec_nombre, _, _, _ in COLONIAS_JUAREZ:
            if sec_nombre not in sectores_map:
                sec = Sector(nombre=sec_nombre, descripcion=f"Sector operativo {sec_nombre} en Ciudad Juárez")
                db.add(sec)
                db.flush()
                sectores_map[sec_nombre] = sec

        colonias_objs = []
        for col_nombre, cp, sec_nombre, lat, lon, calle_base in COLONIAS_JUAREZ:
            col = Colonia(nombre=col_nombre, codigo_postal=cp, sector_id=sectores_map[sec_nombre].id, activa=True)
            db.add(col)
            db.flush()
            colonias_objs.append((col, lat, lon, calle_base))

        print("Generando 500 reportes distribuidos en las últimas 12 semanas...")
        random.seed(42)
        ahora = datetime.now(TZ_JUAREZ)
        bch_seq = 1
        enc_seq = 1

        estados_bache_pool = [
            EstadoReporte.RECIBIDO,
            EstadoReporte.VALIDADO,
            EstadoReporte.PROGRAMADO,
            EstadoReporte.EN_REPARACION,
            EstadoReporte.REPARADO,
            EstadoReporte.RECHAZADO,
        ]
        pesos_bache = [0.22, 0.28, 0.12, 0.10, 0.22, 0.06]

        for i in range(500):
            col, base_lat, base_lon, calle_base = random.choice(colonias_objs)
            dias_atras = random.randint(0, 83)  # 12 semanas = 84 días
            horas_atras = random.randint(0, 23)
            fecha_rep = ahora - timedelta(days=dias_atras, hours=horas_atras)

            lat = round(base_lat + random.uniform(-0.006, 0.006), 6)
            lon = round(base_lon + random.uniform(-0.006, 0.006), 6)
            calle = f"{calle_base} #{random.randint(100, 4500)}"
            autor = random.choice([usuarios[0], usuarios[4]])

            es_bache = random.random() < 0.78  # ~390 baches y ~110 encharcamientos

            if es_bache:
                folio = f"BCH-2026-{bch_seq:06d}"
                bch_seq += 1
                tipo_d = random.choice(list(TipoDanoBache))
                sev = SeveridadBache.ALTA if tipo_d == TipoDanoBache.ALCANTARILLA_SIN_TAPA else random.choice(list(SeveridadBache))
                estado = random.choices(estados_bache_pool, weights=pesos_bache, k=1)[0]

                fecha_rep_fin = None
                motivo_rech = None
                if estado == EstadoReporte.REPARADO:
                    dias_duracion = random.randint(2, max(2, min(25, dias_atras)))
                    fecha_rep_fin = (fecha_rep + timedelta(days=dias_duracion)).date()
                elif estado == EstadoReporte.RECHAZADO:
                    motivo_rech = "Duplicado o fuera de jurisdicción vial"

                rep = Reporte(
                    folio=folio,
                    categoria=CategoriaReporte.BACHE,
                    estado=estado,
                    calle=calle,
                    referencia=f"Cerca de cruce principal en {col.nombre}",
                    latitud=lat,
                    longitud=lon,
                    colonia_id=col.id,
                    tipo_dano=tipo_d,
                    tamano_bache=random.choice(["chico", "mediano", "grande"]) if tipo_d == TipoDanoBache.BACHE else None,
                    profundidad_aprox=random.choice(["5 cm", "12 cm", "20 cm"]) if tipo_d == TipoDanoBache.BACHE else None,
                    carril_afectado=random.choice(["Derecho", "Central", "Izquierdo"]),
                    severidad=sev,
                    alcantarilla_senalizada=random.choice([True, False]) if tipo_d == TipoDanoBache.ALCANTARILLA_SIN_TAPA else None,
                    descripcion=f"Reporte ciudadano de {tipo_d.value.replace('_', ' ')} sobre {calle} en {col.nombre}.",
                    fecha_reporte=fecha_rep,
                    fecha_reparacion=fecha_rep_fin,
                    motivo_rechazo=motivo_rech,
                    autor_id=autor.id,
                )
                db.add(rep)
                db.flush()

                db.add(
                    HistorialEstado(
                        reporte_id=rep.id,
                        estado_anterior=None,
                        estado_nuevo=EstadoReporte.RECIBIDO,
                        comentario_publico="Reporte recibido en plataforma.",
                        usuario_id=autor.id,
                        fecha_cambio=fecha_rep,
                    )
                )
                if estado != EstadoReporte.RECIBIDO:
                    db.add(
                        HistorialEstado(
                            reporte_id=rep.id,
                            estado_anterior=EstadoReporte.RECIBIDO,
                            estado_nuevo=estado,
                            comentario_publico=f"Actualización de seguimiento a {estado.value}.",
                            usuario_id=usuarios[1].id,
                            fecha_cambio=fecha_rep + timedelta(hours=12),
                        )
                    )
            else:
                folio = f"ENC-2026-{enc_seq:06d}"
                enc_seq += 1
                nivel = random.choice(list(NivelAgua))
                # Dejar ~18 encharcamientos activos recientes para la demo
                if i >= 475:
                    fecha_rep = ahora - timedelta(hours=random.randint(1, 3))
                    estado = EstadoReporte.ACTIVO
                    vigente_hasta = fecha_rep + timedelta(hours=6)
                else:
                    estado = EstadoReporte.HISTORICO
                    vigente_hasta = fecha_rep + timedelta(hours=6)

                rep = Reporte(
                    folio=folio,
                    categoria=CategoriaReporte.ENCHARCAMIENTO,
                    estado=estado,
                    calle=calle,
                    referencia=f"Paso vial en {col.nombre}",
                    latitud=lat,
                    longitud=lon,
                    colonia_id=col.id,
                    nivel_agua=nivel,
                    riesgo_vehiculos_personas=True if nivel == NivelAgua.INTRANSITABLE else False,
                    vigente_hasta=vigente_hasta,
                    descripcion=f"Acumulación de agua ({nivel.value}) reportada en {calle}.",
                    fecha_reporte=fecha_rep,
                    autor_id=autor.id,
                )
                db.add(rep)
                db.flush()

                db.add(
                    HistorialEstado(
                        reporte_id=rep.id,
                        estado_anterior=None,
                        estado_nuevo=EstadoReporte.ACTIVO,
                        comentario_publico="Encharcamiento publicado como activo.",
                        usuario_id=autor.id,
                        fecha_cambio=fecha_rep,
                    )
                )

            # Agregar algunas confirmaciones aleatorias
            if random.random() < 0.35:
                confirmador = usuarios[4] if autor.id == usuarios[0].id else usuarios[0]
                db.add(
                    InteraccionReporte(
                        reporte_id=rep.id,
                        usuario_id=confirmador.id,
                        tipo=TipoInteraccion.CONFIRMACION,
                        creado_en=fecha_rep + timedelta(minutes=45),
                    )
                )

        db.commit()
        print("Seed completado: 5 usuarios, 4 sectores, 24 colonias y 500 reportes cargados.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()