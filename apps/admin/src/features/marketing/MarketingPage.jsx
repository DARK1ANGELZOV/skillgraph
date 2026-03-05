import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";

const TRUSTED_COMPANIES = ["SberTech", "T-Bank", "VK Tech", "Yandex Cloud", "Positive", "Selectel"];

const HOW_IT_WORKS = [
  {
    title: "1. Запуск вакансии",
    text: "HR или руководитель создаёт вакансию, задаёт требования и уровень кандидата."
  },
  {
    title: "2. Ссылка кандидату",
    text: "SkillGraph выдаёт magic link: кандидат проходит AI-интервью и тесты без регистрации."
  },
  {
    title: "3. Отчёт и решение",
    text: "Система формирует структурированный отчёт: скоринг, риски, сильные стороны и рекомендация."
  }
];

const AUDIENCES = [
  {
    title: "Owner",
    text: "Полный контроль компании, ролей, процессов найма и управленческих метрик."
  },
  {
    title: "HR-команда",
    text: "Быстрое создание вакансий, отправка ссылок и массовый просмотр результатов."
  },
  {
    title: "Руководители",
    text: "Executive summary по кандидатам с акцентом на риски и влияние на команду."
  },
  {
    title: "Кандидаты",
    text: "Один magic link для интервью и тестов, понятный сценарий и прозрачные этапы."
  }
];

const CORE_FEATURES = [
  {
    title: "AI как реальный интервьюер",
    text: "Динамический диалог, уточняющие вопросы и контроль времени ответа в формате живого интервью."
  },
  {
    title: "Кастомные тесты от команды",
    text: "HR и руководители создают собственные тесты, отправляют ссылку и получают результаты в одном кабинете."
  },
  {
    title: "Executive-режим",
    text: "Короткая управленческая сводка по каждому кандидату с финальной рекомендацией."
  },
  {
    title: "Безопасность и аудит",
    text: "Логирование подозрительных действий, RBAC, аудит событий и разделение компаний."
  },
  {
    title: "Инфраструктура под масштаб",
    text: "Multi-company архитектура для тысяч команд с централизованным мониторингом."
  },
  {
    title: "Единое окно управления",
    text: "Интервью, тестирование, отчёты и аналитика собраны в одной продуктовой среде."
  }
];

const ANALYTICS_STACK = [
  "Технический уровень",
  "Soft skills",
  "Логическое мышление",
  "Психологическая устойчивость",
  "Уровень волнения",
  "Anti-cheat сигналы"
];

const FAQ = [
  {
    q: "Насколько интервью похоже на реальное?",
    a: "Модель ведёт структурированный диалог, задаёт технические и поведенческие вопросы и адаптируется по ответам кандидата."
  },
  {
    q: "Можно ли создавать свои тесты?",
    a: "Да. HR и руководители создают кастомные тесты в кабинете и отправляют отдельную ссылку кандидату."
  },
  {
    q: "Сколько занимает внедрение?",
    a: "Базовый запуск занимает 1 рабочий день: роли, вакансии, кандидаты и аналитика доступны сразу."
  },
  {
    q: "Есть multi-company режим?",
    a: "Да, SkillGraph построен как multi-tenant SaaS с изоляцией данных между компаниями."
  }
];

export function MarketingPage() {
  const [token, setToken] = useState("");
  const navigate = useNavigate();

  function openInterview(event) {
    event.preventDefault();
    const clean = normalizeToken(token);
    if (!clean) {
      return;
    }
    navigate(`/interview/${clean}`);
  }

  return (
    <main className="marketing">
      <header className="landing-nav">
        <div className="brand-box">
          <span className="brand-logo">SG</span>
          <div>
            <strong>SkillGraph</strong>
            <p>AI-платформа для найма и развития талантов</p>
          </div>
        </div>
        <div className="landing-actions">
          <a href="#how-it-works">Как работает</a>
          <a href="#pricing">Тарифы</a>
          <a href="#faq">FAQ</a>
          <Link className="primary-btn" to="/auth">
            Войти в кабинет
          </Link>
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">ENTERPRISE AI-HR PLATFORM</p>
          <h1>SkillGraph проводит AI-собеседования и даёт глубокую аналитику по каждому кандидату</h1>
          <p>
            Полный hiring-loop в одном продукте: интервью, тесты, оценка рисков и управленческий отчёт для финального
            решения.
          </p>
          <div className="hero-buttons">
            <Link className="primary-btn" to="/auth">
              Перейти в личный кабинет
            </Link>
            <a className="secondary-btn" href="#how-it-works">
              Посмотреть платформу
            </a>
          </div>
          <div className="hero-meta">
            <span>14 дней бесплатно</span>
            <span>Поддержка 24/7</span>
            <span>Быстрый запуск за 1 день</span>
          </div>
        </div>

        <div className="hero-stats">
          <article>
            <p>Скорость закрытия вакансий</p>
            <strong>+42%</strong>
          </article>
          <article>
            <p>Снижение ручной нагрузки HR</p>
            <strong>-57%</strong>
          </article>
          <article>
            <p>Среднее время интервью</p>
            <strong>18 мин</strong>
          </article>
        </div>

        <form className="token-card" onSubmit={openInterview}>
          <h3>Кандидатский вход</h3>
          <p>Одна ссылка для AI-собеседования и тестов.</p>
          <input
            placeholder="Вставьте токен или ссылку"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            required
          />
          <button className="primary-btn" type="submit">
            Начать интервью
          </button>
        </form>
      </section>

      <section className="trust-strip">
        <p>Нам доверяют команды, которым нужен прогнозируемый и быстрый найм:</p>
        <div className="trust-grid trust-grid-inline">
          {TRUSTED_COMPANIES.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </section>

      <section className="section-shell" id="how-it-works">
        <div className="section-head">
          <p className="eyebrow">HOW IT WORKS</p>
          <h2>Как работает SkillGraph</h2>
          <p>Пошаговый сценарий от запуска вакансии до финального решения по кандидату.</p>
        </div>
        <div className="process-grid">
          {HOW_IT_WORKS.map((item) => (
            <article key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-shell" id="for-whom">
        <div className="section-head">
          <p className="eyebrow">FOR TEAMS</p>
          <h2>Для кого предназначен SkillGraph</h2>
        </div>
        <div className="audience-grid">
          {AUDIENCES.map((item) => (
            <article className="audience-card" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-shell">
        <div className="section-head">
          <p className="eyebrow">DEEP ANALYTICS</p>
          <h2>Глубокая аналитика по каждому кандидату</h2>
          <p>От базового скоринга к реальной управленческой диагностике и оценке рисков найма.</p>
        </div>
        <div className="insight-grid">
          {ANALYTICS_STACK.map((item) => (
            <article key={item}>
              <h4>{item}</h4>
            </article>
          ))}
        </div>
      </section>

      <section className="section-shell">
        <div className="section-head">
          <p className="eyebrow">PLATFORM CAPABILITIES</p>
          <h2>Что умеет платформа</h2>
        </div>
        <div className="feature-grid">
          {CORE_FEATURES.map((item) => (
            <article key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="pricing" className="pricing-block">
        <div className="section-head">
          <p className="eyebrow">PRICING</p>
          <h2>
            <span>ПОДПИСКА</span> НА SKILLGRAPH
          </h2>
        </div>
        <div className="pricing-grid">
          <article className="price-card">
            <h3>Starter</h3>
            <p>Что входит:</p>
            <ul>
              <li>Тестирование кандидатов</li>
              <li>Базовый Dashboard</li>
              <li>До 50 интервью в месяц</li>
            </ul>
            <strong>Цена: 80 000 ₽ / месяц</strong>
          </article>
          <article className="price-card featured">
            <h3>Enterprise</h3>
            <p>Что входит:</p>
            <ul>
              <li>AI-интервью + тестирование</li>
              <li>Глубокая аналитика и отчёты</li>
              <li>Dashboard + API + RBAC</li>
            </ul>
            <strong>Цена: 600 000 ₽ / месяц</strong>
          </article>
          <article className="price-card">
            <h3>Growth</h3>
            <p>Что входит:</p>
            <ul>
              <li>AI-интервью</li>
              <li>Тестирование</li>
              <li>Аналитика по департаментам</li>
            </ul>
            <strong>Цена: 250 000 ₽ / месяц</strong>
          </article>
        </div>
      </section>

      <section id="faq" className="faq-block">
        <div className="section-head">
          <p className="eyebrow">FAQ</p>
          <h2>Часто задаваемые вопросы</h2>
        </div>
        <div className="faq-grid">
          {FAQ.map((item) => (
            <article key={item.q}>
              <h4>{item.q}</h4>
              <p>{item.a}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="cta">
        <h2>Готовы трансформировать HR-процессы?</h2>
        <p>Запустите SkillGraph и переведите интервью в управляемую систему с прозрачным качеством найма.</p>
        <Link className="primary-btn" to="/auth">
          Перейти в личный кабинет
        </Link>
        <p>14 дней бесплатно • поддержка 24/7 • быстрый запуск команды</p>
      </section>

      <footer className="site-footer">
        <div className="footer-brand">
          <div className="brand-box">
            <span className="brand-logo">SG</span>
            <div>
              <strong>SkillGraph</strong>
              <p>AI-платформа для найма и развития талантов</p>
            </div>
          </div>
          <small>© 2026 SkillGraph. Все права защищены.</small>
        </div>
        <div>
          <h4>Продукт</h4>
          <a href="#how-it-works">Возможности</a>
          <a href="#pricing">Тарифы</a>
          <a href="#for-whom">Для кого</a>
          <a href="#">Безопасность</a>
          <a href="#">Changelog</a>
        </div>
        <div>
          <h4>Ресурсы</h4>
          <a href="#">Документация</a>
          <a href="#">API</a>
          <a href="#">Блог</a>
          <a href="#">Кейсы</a>
          <a href="#">Вебинары</a>
        </div>
        <div>
          <h4>Компания</h4>
          <a href="#">О нас</a>
          <a href="#">Карьера</a>
          <a href="#">Контакты</a>
          <a href="#">Партнеры</a>
          <a href="#">Пресса</a>
        </div>
        <div>
          <h4>Юридическое</h4>
          <a href="#">Политика конфиденциальности</a>
          <a href="#">Условия использования</a>
          <a href="#">Обработка данных</a>
          <a href="#">Cookies</a>
          <small>Made with AI • Москва, Россия</small>
        </div>
      </footer>
    </main>
  );
}

function normalizeToken(value) {
  const raw = value.trim();
  if (!raw) {
    return "";
  }
  if (raw.includes("/interview/")) {
    const chunk = raw.split("/interview/").pop() || "";
    return chunk.split("?")[0].split("#")[0];
  }
  return raw;
}
