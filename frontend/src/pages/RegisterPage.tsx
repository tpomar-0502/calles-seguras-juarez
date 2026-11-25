// frontend/src/pages/RegisterPage.tsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [acepto, setAcepto] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      setError("La contraseña debe tener al menos 8 caracteres y combinar letras y números.");
      return;
    }
    if (!acepto) {
      setError("Debes aceptar el aviso de privacidad para crear tu cuenta.");
      return;
    }

    setEnviando(true);
    try {
      await register(nombre, correo, password, acepto);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="container page-content narrow-box">
      <h1>Crear cuenta ciudadana</h1>
      <form onSubmit={handleSubmit} className="panel-box form-stack">
        {error && <p className="error-box" role="alert">{error}</p>}
        <div className="form-group">
          <label htmlFor="reg-nombre">Nombre completo</label>
          <input id="reg-nombre" type="text" required value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="reg-correo">Correo electrónico</label>
          <input id="reg-correo" type="email" required value={correo} onChange={(e) => setCorreo(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="reg-pass">Contraseña (mínimo 8 caracteres, letras y números)</label>
          <input id="reg-pass" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="checkbox-label">
            <input type="checkbox" checked={acepto} onChange={(e) => setAcepto(e.target.checked)} />
            Acepto el Aviso de Privacidad: mis datos personales nunca serán mostrados en reportes públicos ni exportaciones.
          </label>
        </div>
        <button type="submit" className="btn btn-primary" disabled={enviando}>
          {enviando ? "Creando cuenta..." : "Registrarme"}
        </button>
        <p>¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link></p>
      </form>
    </div>
  );
};