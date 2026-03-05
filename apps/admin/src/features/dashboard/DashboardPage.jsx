import { useEffect, useState } from "react";

import { api } from "../../lib/api";

export function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [vacancies, setVacancies] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [form, setForm] = useState({ title: "", department: "Engineering", seniority: "middle", requirements: "" });
  const [candidateForm, setCandidateForm] = useState({
    full_name: "",
    email: "",
    vacancy_id: "",
    experience_years: "",
    skills: "",
    education: ""
  });
  const [lastMagicLink, setLastMagicLink] = useState("");
  const [error, setError] = useState("");

  async function loadData() {
    try {
      const [summaryData, vacancyData, candidateData] = await Promise.all([
        api("/analytics/executive-summary"),
        api("/vacancies"),
        api("/candidates")
      ]);
      setSummary(summaryData);
      setVacancies(vacancyData);
      setCandidates(candidateData);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function createVacancy(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/vacancies", { method: "POST", body: JSON.stringify(form) });
      setForm({ title: "", department: "Engineering", seniority: "middle", requirements: "" });
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function sendMagicLink(event) {
    event.preventDefault();
    setError("");
    try {
      const candidate = await api("/candidates/magic-link", {
        method: "POST",
        body: JSON.stringify({
          full_name: candidateForm.full_name,
          email: candidateForm.email,
          vacancy_id: candidateForm.vacancy_id || null,
          experience_years: candidateForm.experience_years ? Number(candidateForm.experience_years) : null,
          skills: candidateForm.skills
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          education: candidateForm.education || null
        })
      });
      setCandidateForm({
        full_name: "",
        email: "",
        vacancy_id: "",
        experience_years: "",
        skills: "",
        education: ""
      });
      setLastMagicLink(candidate.interview_link || `${window.location.origin}/interview/${candidate.magic_link_token}`);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="grid-layout">
      <section className="card metric-row">
        <Metric label="Total interviews" value={summary?.total_interviews ?? 0} />
        <Metric label="Completed" value={summary?.completed_interviews ?? 0} />
        <Metric label="Average score" value={summary ? `${summary.avg_score}%` : "0%"} />
        <Metric label="Recommended" value={summary?.recommended_count ?? 0} />
        <Metric label="Conditional" value={summary?.conditional_count ?? 0} />
        <Metric label="Rejected" value={summary?.rejected_count ?? 0} />
      </section>

      <section className="card">
        <h3>Создать вакансию</h3>
        <form onSubmit={createVacancy} className="form-grid">
          <input
            placeholder="Позиция"
            value={form.title}
            onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            required
          />
          <input
            placeholder="Департамент"
            value={form.department}
            onChange={(event) => setForm((prev) => ({ ...prev, department: event.target.value }))}
            required
          />
          <input
            placeholder="Грейд"
            value={form.seniority}
            onChange={(event) => setForm((prev) => ({ ...prev, seniority: event.target.value }))}
          />
          <textarea
            placeholder="Требования"
            value={form.requirements}
            onChange={(event) => setForm((prev) => ({ ...prev, requirements: event.target.value }))}
            required
          />
          <button className="primary-btn" type="submit">
            Сохранить вакансию
          </button>
        </form>
      </section>

      <section className="card">
        <h3>Пригласить кандидата</h3>
        <form onSubmit={sendMagicLink} className="form-grid">
          <input
            placeholder="ФИО кандидата"
            value={candidateForm.full_name}
            onChange={(event) => setCandidateForm((prev) => ({ ...prev, full_name: event.target.value }))}
            required
          />
          <input
            type="email"
            placeholder="Email кандидата"
            value={candidateForm.email}
            onChange={(event) => setCandidateForm((prev) => ({ ...prev, email: event.target.value }))}
            required
          />
          <select
            value={candidateForm.vacancy_id}
            onChange={(event) => setCandidateForm((prev) => ({ ...prev, vacancy_id: event.target.value }))}
          >
            <option value="">Без привязки к вакансии</option>
            {vacancies.map((vacancy) => (
              <option key={vacancy.id} value={vacancy.id}>
                {vacancy.title}
              </option>
            ))}
          </select>
          <input
            type="number"
            min="0"
            placeholder="Опыт (лет)"
            value={candidateForm.experience_years}
            onChange={(event) => setCandidateForm((prev) => ({ ...prev, experience_years: event.target.value }))}
          />
          <input
            placeholder="Навыки через запятую"
            value={candidateForm.skills}
            onChange={(event) => setCandidateForm((prev) => ({ ...prev, skills: event.target.value }))}
          />
          <textarea
            placeholder="Образование"
            value={candidateForm.education}
            onChange={(event) => setCandidateForm((prev) => ({ ...prev, education: event.target.value }))}
          />
          <button className="primary-btn" type="submit">
            Отправить ссылку
          </button>
        </form>
        {lastMagicLink ? (
          <div>
            <p>
              Ссылка на AI-собеседование: <span className="mono">{lastMagicLink}</span>
            </p>
            <p>
              Ссылка на тесты: <span className="mono">{lastMagicLink}?mode=tests</span>
            </p>
          </div>
        ) : null}
      </section>

      <section className="card">
        <h3>Последние кандидаты</h3>
        <div className="table">
          <div className="table-head table-six">
            <span>Имя</span>
            <span>Email</span>
            <span>Статус</span>
            <span>Навыки</span>
            <span>AI-собес</span>
            <span>Тесты</span>
          </div>
          {candidates.map((candidate) => (
            <div className="table-row table-six" key={candidate.id}>
              <span>{candidate.full_name}</span>
              <span>{candidate.email}</span>
              <span>{candidate.status}</span>
              <span>{(candidate.skills || []).slice(0, 2).join(", ") || "-"}</span>
              <span className="mono">{candidate.interview_link ? candidate.interview_link.slice(0, 34) : "-"}</span>
              <span className="mono">{candidate.tests_link ? candidate.tests_link.slice(0, 34) : "-"}</span>
            </div>
          ))}
        </div>
      </section>

      {error ? <div className="error-box">{error}</div> : null}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <article>
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}
