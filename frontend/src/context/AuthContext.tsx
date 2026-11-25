import React, { createContext, useContext, useEffect, useState } from "react";
import { apiFetch } from "../api/client";
import { Usuario } from "../types";

interface AuthContextType {
  usuario: Usuario | null;
  token: string | null;
  cargando: boolean;
  login: (correo: string, password: string) => Promise<void>;
  register: (nombre: string, correo: string, password: string, acepto: boolean) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Cierre por inactividad de 30 minutos (HU-01.2 CA4)
const INACTIVITY_MS = 30 * 60 * 1000;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem("csj_token"));
  const [cargando, setCargando] = useState<boolean>(true);

  const logout = () => {
    sessionStorage.removeItem("csj_token");
    setToken(null);
    setUsuario(null);
  };

  useEffect(() => {
    if (!token) {
      setCargando(false);
      return;
    }
    apiFetch<Usuario>("/auth/me")
      .then((u) => setUsuario(u))
      .catch(() => logout())
      .finally(() => setCargando(false));
  }, [token]);

  // Control de inactividad
  useEffect(() => {
    if (!usuario) return;
    let timer = window.setTimeout(() => {
      logout();
      alert("Tu sesión se cerró por inactividad (30 minutos). Inicia sesión nuevamente.");
    }, INACTIVITY_MS);

    const resetTimer = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => logout(), INACTIVITY_MS);
    };

    window.addEventListener("click", resetTimer);
    window.addEventListener("keydown", resetTimer);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("click", resetTimer);
      window.removeEventListener("keydown", resetTimer);
    };
  }, [usuario]);

  const login = async (correo: string, password: string) => {
    const body = new URLSearchParams();
    body.append("username", correo);
    body.append("password", password);

    const data = await apiFetch<{ access_token: string; usuario: Usuario }>("/auth/login", {
      method: "POST",
      body,
    });
    sessionStorage.setItem("csj_token", data.access_token);
    setToken(data.access_token);
    setUsuario(data.usuario);
  };

  const register = async (nombre: string, correo: string, password: string, acepto: boolean) => {
    const data = await apiFetch<{ access_token: string; usuario: Usuario }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ nombre, correo, password, acepto_privacidad: acepto }),
    });
    sessionStorage.setItem("csj_token", data.access_token);
    setToken(data.access_token);
    setUsuario(data.usuario);
  };

  return (
    <AuthContext.Provider value={{ usuario, token, cargando, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}