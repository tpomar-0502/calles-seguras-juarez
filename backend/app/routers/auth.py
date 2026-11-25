from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import RolUsuario, Usuario
from app.schemas.schemas import TokenOut, UsuarioOut, UsuarioRegistro
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(data: UsuarioRegistro, db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(Usuario.correo == data.correo.lower()).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado en la plataforma.",
        )
    usuario = Usuario(
        nombre=data.nombre.strip(),
        correo=data.correo.lower(),
        password_hash=get_password_hash(data.password),
        rol=RolUsuario.CIUDADANO,
        activo=True,
        acepto_privacidad=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    token = create_access_token({"sub": usuario.correo, "rol": usuario.rol.value})
    return TokenOut(access_token=token, usuario=UsuarioOut.model_validate(usuario))


@router.post("/login", response_model=TokenOut)
def iniciar_sesion(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.correo == form_data.username.lower()).first()
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta se encuentra suspendida.",
        )
    token = create_access_token({"sub": usuario.correo, "rol": usuario.rol.value})
    return TokenOut(access_token=token, usuario=UsuarioOut.model_validate(usuario))


@router.get("/me", response_model=UsuarioOut)
def perfil_actual(current_user: Usuario = Depends(get_current_user)):
    return current_user