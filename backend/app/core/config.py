from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Calles Seguras Juárez API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql://csj_user:csj_password_seguro_2026@localhost:5432/calles_seguras_juarez"
    SECRET_KEY: str = "cambia_esta_clave_secreta_en_produccion_2026_itcj"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Límites y reglas de negocio documentadas (RN-01 a RN-10)
    TIMEZONE: str = "America/Ciudad_Juarez"
    MAX_REPORTES_POR_HORA: int = 10
    RADIO_DUPLICADO_BACHE_M: float = 30.0
    RADIO_DUPLICADO_ENCHARCAMIENTO_M: float = 50.0
    VIGENCIA_ENCHARCAMIENTO_HORAS: int = 6
    DESMENTIDOS_PARA_HISTORICO: int = 3

    # Bounding box aproximado del Municipio de Juárez, Chihuahua
    JUAREZ_LAT_MIN: float = 31.10
    JUAREZ_LAT_MAX: float = 31.82
    JUAREZ_LON_MIN: float = -106.95
    JUAREZ_LON_MAX: float = -106.05

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()