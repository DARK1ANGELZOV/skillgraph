import { useEffect, useState } from "react";

import { api } from "../../lib/api";

export function AnalyticsPage() {
  const [reports, setReports] = useState([]);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api("/analytics/reports"), api("/analytics/executive-summary")])
      .then(([reportsData, summaryData]) => {
        setReports(reportsData);
        setSummary(summaryData);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <section className="card">
      <h3>Analytics & Reports</h3>
      <p>Supervisor role remains read-only. Owner/HR can review full AI report and executive summary.</p>
      {error ? <div className="error-box">{error}</div> : null}
      {summary ? <pre>{JSON.stringify(summary, null, 2)}</pre> : null}

      <div className="chart-grid">
        {reports.map((report) => (
          <article key={report.id} className="mini-card">
            <small>{report.report_type}</small>
            <h4>{report.summary}</h4>
            <pre>{JSON.stringify(report.content, null, 2)}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}
