import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import { useAuth } from "../features/auth/AuthContext";

export function AdminLayout() {
  const { session, logout } = useAuth();
  const [theme, setTheme] = useState(() => localStorage.getItem("sg-admin-theme") || "dark");
  const navigate = useNavigate();

  const navItems =
    session?.role === "SUPERADMIN"
      ? [
          { to: "/app/superadmin", label: "Платформа" },
          { to: "/app/analytics", label: "Отчёты" },
          { to: "/app/settings", label: "Настройки" }
        ]
      : [
          { to: "/app/dashboard", label: "Dashboard" },
          { to: "/app/analytics", label: "Аналитика" },
          { to: "/app/interviews", label: "Интервью" },
          { to: "/app/settings", label: "Настройки" }
        ];

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("sg-admin-theme", theme);
  }, [theme]);

  async function onLogout() {
    await logout();
    navigate("/", { replace: true });
  }

  return (
    <div className="layout-shell">
      <aside className="sidebar">
        <div className="sidebar-block">
          <div className="sidebar-brand">
            <span className="brand-logo">SG</span>
            <div>
              <h2>SkillGraph</h2>
              <p>Talent Intelligence</p>
            </div>
          </div>
          <div className="role-pill">{session?.role}</div>
        </div>

        <nav>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-actions">
          <button className="secondary-btn" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            Тема: {theme === "dark" ? "Тёмная" : "Светлая"}
          </button>
          <button className="danger-btn" onClick={onLogout}>
            Выйти
          </button>
        </div>
      </aside>

      <section className="content-shell">
        <header className="topbar">
          <div>
            <h1>Talent Intelligence Workspace</h1>
            <p>{session?.email}</p>
          </div>
        </header>
        <Outlet />
      </section>
    </div>
  );
}
