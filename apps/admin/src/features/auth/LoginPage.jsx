import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "./AuthContext";

const DEMO_EMAIL = "superadmin@skillgraph.dev";
const DEMO_PASSWORD = "SkillGraphAdmin123!";

export function LoginPage() {
  const [mode, setMode] = useState("login");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "",
    company_name: "",
    full_name: ""
  });
  const { login, registerOwner } = useAuth();
  const navigate = useNavigate();

  async function onSubmit(event) {
    event.preventDefault();
    setError("");

    try {
      if (mode === "login") {
        await login({ email: form.email, password: form.password });
      } else {
        await registerOwner({
          email: form.email,
          password: form.password,
          company_name: form.company_name,
          full_name: form.full_name || null
        });
      }
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err.message);
    }
  }

  function fillDemo() {
    setMode("login");
    setForm((prev) => ({
      ...prev,
      email: DEMO_EMAIL,
      password: DEMO_PASSWORD
    }));
  }

  return (
    <main className="auth-screen auth-enterprise">
      <section className="auth-showcase">
        <p className="eyebrow">SECURE ENTERPRISE ACCESS</p>
        <h1>SkillGraph Workspace</h1>
        <p>
          Единая платформа для AI-собеседований, тестирования и аналитики найма. Авторизация через защищённые cookie,
          роли и аудит действий.
        </p>
        <ul>
          <li>Owner, HR, Supervisor, Superadmin в одном контуре</li>
          <li>Автоматический скоринг и anti-cheat сигналы</li>
          <li>Кастомные тесты и быстрые ссылки кандидатам</li>
        </ul>
        <button type="button" className="secondary-btn" onClick={fillDemo}>
          Заполнить демо-логин superadmin
        </button>
      </section>

      <section className="auth-card auth-modern">
        <h2>{mode === "login" ? "Вход в личный кабинет" : "Регистрация компании"}</h2>
        <p>{mode === "login" ? "Управляйте процессом найма в одном окне" : "Создайте аккаунт Owner за 1 минуту"}</p>

        <div className="switcher">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            Войти
          </button>
          <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
            Регистрация
          </button>
        </div>

        <form onSubmit={onSubmit} className="auth-form">
          {mode === "register" ? (
            <label>
              Название компании
              <input
                value={form.company_name}
                onChange={(event) => setForm((prev) => ({ ...prev, company_name: event.target.value }))}
                required
              />
            </label>
          ) : null}

          {mode === "register" ? (
            <label>
              Имя и фамилия
              <input
                value={form.full_name}
                onChange={(event) => setForm((prev) => ({ ...prev, full_name: event.target.value }))}
              />
            </label>
          ) : null}

          <label>
            Рабочий email
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
              required
            />
          </label>

          <label>
            Пароль
            <input
              type={showPassword ? "text" : "password"}
              value={form.password}
              onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
              minLength={8}
              required
            />
          </label>

          <label className="inline-check">
            <input type="checkbox" checked={showPassword} onChange={(event) => setShowPassword(event.target.checked)} />
            <span>Показать пароль</span>
          </label>

          {error ? <div className="error-box">{error}</div> : null}
          <button type="submit" className="primary-btn">
            {mode === "login" ? "Открыть кабинет" : "Создать компанию"}
          </button>
        </form>
      </section>
    </main>
  );
}
