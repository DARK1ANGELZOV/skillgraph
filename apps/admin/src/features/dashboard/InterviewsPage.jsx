import { useEffect, useState } from "react";

import { api } from "../../lib/api";

export function InterviewsPage() {
  const [interviews, setInterviews] = useState([]);
  const [selected, setSelected] = useState(null);
  const [tests, setTests] = useState([]);
  const [testDefinitions, setTestDefinitions] = useState([]);
  const [customTest, setCustomTest] = useState({
    title: "Кастомный тест руководителя",
    category: "manager_custom",
    duration_sec: 900,
    questions_json: JSON.stringify(
      [
        {
          text: "Как вы приоритизируете задачи при ограниченных сроках?",
          options: [
            "Игнорирую риски",
            "Собираю вводные и оцениваю влияние на бизнес",
            "Делаю всё параллельно",
            "Жду указаний"
          ],
          correct_index: 1
        }
      ],
      null,
      2
    )
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    api("/interviews")
      .then(setInterviews)
      .catch((err) => setError(err.message));
  }, []);

  async function openInterview(interviewId) {
    try {
      const [detail, testResults] = await Promise.all([api(`/interviews/${interviewId}`), api(`/tests/interview/${interviewId}`)]);
      setSelected(detail);
      setTests(testResults);
      const definitions = await api(`/tests/interview/${interviewId}/definitions`);
      setTestDefinitions(definitions);
    } catch (err) {
      setError(err.message);
    }
  }

  async function createCustomTest(event) {
    event.preventDefault();
    if (!selected) {
      return;
    }
    setError("");
    setMessage("");
    try {
      const payload = {
        title: customTest.title,
        category: customTest.category,
        duration_sec: Number(customTest.duration_sec),
        questions: JSON.parse(customTest.questions_json)
      };
      await api(`/tests/interview/${selected.id}/custom`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setMessage("Кастомный тест создан и доступен кандидату по ссылке на тесты.");
      const definitions = await api(`/tests/interview/${selected.id}/definitions`);
      setTestDefinitions(definitions);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="grid-layout">
      <section className="card">
        <h3>Реестр интервью</h3>
        {error ? <div className="error-box">{error}</div> : null}
        <div className="table">
          <div className="table-head table-six">
            <span>Интервью</span>
            <span>Статус</span>
            <span>Итоговый балл</span>
            <span>Рекомендация</span>
            <span>Suspicious</span>
            <span>Действие</span>
          </div>
          {interviews.map((interview) => (
            <div key={interview.id} className="table-row table-six">
              <span className="mono">{interview.id.slice(0, 12)}...</span>
              <span>{interview.status}</span>
              <span>{interview.score ? `${interview.score.overall_score}%` : "N/A"}</span>
              <span>{interview.score?.recommendation ?? "-"}</span>
              <span>{interview.score?.rationale?.signals?.anti_cheat_penalty ?? "-"}</span>
              <button className="secondary-btn" onClick={() => openInterview(interview.id)} type="button">
                Открыть
              </button>
            </div>
          ))}
        </div>
      </section>

      {selected ? (
        <section className="card">
          <h3>Детали интервью</h3>
          <p>
            Кандидат: <strong>{selected.candidate?.full_name}</strong> ({selected.candidate?.email})
          </p>
          <p>
            Навыки: {(selected.candidate?.skills ?? []).join(", ") || "-"} | Опыт: {selected.candidate?.experience_years ?? "-"}{" "}
            лет
          </p>
          <p className="mono">AI-ссылка: {window.location.origin}/interview/{selected.candidate?.magic_link_token}</p>
          <p className="mono">Тесты: {window.location.origin}/interview/{selected.candidate?.magic_link_token}?mode=tests</p>
          <p>Подозрительных событий: {selected.suspicious_events_count}</p>

          <h4>Скоринг</h4>
          <pre>{JSON.stringify(selected.score, null, 2)}</pre>

          <h4>Результаты тестов</h4>
          <pre>{JSON.stringify(tests, null, 2)}</pre>

          <h4>Доступные тесты</h4>
          <pre>{JSON.stringify(testDefinitions, null, 2)}</pre>

          <h4>Создать кастомный тест</h4>
          <form onSubmit={createCustomTest} className="form-grid">
            <input
              value={customTest.title}
              onChange={(event) => setCustomTest((prev) => ({ ...prev, title: event.target.value }))}
              placeholder="Название теста"
              required
            />
            <input
              value={customTest.category}
              onChange={(event) => setCustomTest((prev) => ({ ...prev, category: event.target.value }))}
              placeholder="Категория"
              required
            />
            <input
              type="number"
              min="60"
              max="7200"
              value={customTest.duration_sec}
              onChange={(event) => setCustomTest((prev) => ({ ...prev, duration_sec: event.target.value }))}
            />
            <textarea
              value={customTest.questions_json}
              onChange={(event) => setCustomTest((prev) => ({ ...prev, questions_json: event.target.value }))}
              style={{ minHeight: 180 }}
            />
            <button className="primary-btn" type="submit">
              Создать тест
            </button>
          </form>
          {message ? <div className="success-box">{message}</div> : null}
        </section>
      ) : null}
    </div>
  );
}
