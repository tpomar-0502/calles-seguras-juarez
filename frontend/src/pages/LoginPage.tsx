// frontend/src/pages/LoginPage.tsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await login(correo, password);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="container page-content narrow-box">
      <h1>Iniciar sesión</h1>
      <form onSubmit={handleSubmit} className="panel-box form-stack">
        {error && <p className="error-box" role="alert">{error}</p>}
        <div className="form-group">
          <label htmlFor="log-correo">Correo electrónico</label>
          <input id="log-correo" type="email" required value={correo} onChange={(e) => setCorreo(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="log-pass">Contraseña</label>
          <input id="log-pass" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button type="submit" className="btn btn-primary" disabled={enviando}>
          {enviando ? "Ingresando..." : "Entrar"}
        </button>
        <p>¿No tienes cuenta? <Link to="/registro">Regístrate aquí</Link></p>
      </form>
    </div>
  );
};