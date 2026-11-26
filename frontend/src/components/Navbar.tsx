import React from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../api/AuthContext";

export const Navbar: React.FC = () => {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="site-header">
      <div className="container header-inner">
        <Link to="/" className="brand" aria-label="Inicio Calles Seguras Juárez">
          <span className="brand-badge" aria-hidden="true">CSJ</span>
          <span>Calles Seguras Juárez</span>
        </Link>

        <nav aria-label="Navegación principal" className="main-nav">
          <NavLink to="/" end>Explorar</NavLink>
          {usuario && <NavLink to="/reportar">+ Reportar</NavLink>}
          {usuario && <NavLink to="/mis-reportes">Mis reportes</NavLink>}
          {(usuario?.rol === "moderador" || usuario?.rol === "coordinador" || usuario?.rol === "enlace_municipal") && (
            <NavLink to="/moderacion">Moderación</NavLink>
          )}
          {usuario?.rol === "coordinador" && (
            <NavLink to="/admin">Tablero y Admin</NavLink>
          )}
        </nav>

        <div className="auth-controls">
          {usuario ? (
            <>
              <span className="user-pill" title={`Rol: ${usuario.rol}`}>
                {usuario.nombre} ({usuario.rol})
              </span>
              <button type="button" onClick={handleLogout} className="btn btn-outline-light btn-sm">
                Salir
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline-light btn-sm">Entrar</Link>
              <Link to="/registro" className="btn btn-primary btn-sm">Crear cuenta</Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
};