import { useEffect, useState } from "react";

import { api } from "../../lib/api";

export function SuperadminPage() {
  const [overview, setOverview] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [audit, setAudit] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api("/superadmin/overview"), api("/superadmin/companies"), api("/superadmin/audit?limit=80")])
      .then(([overviewData, companiesData, auditData]) => {
        setOverview(overviewData);
        setCompanies(companiesData);
        setAudit(auditData);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="grid-layout">
      {error ? <div className="error-box">{error}</div> : null}

      <section className="card metric-row">
        <Metric label="Companies" value={overview?.companies_count ?? 0} />
        <Metric label="Users" value={overview?.users_count ?? 0} />
        <Metric label="Interviews" value={overview?.interviews_count ?? 0} />
      </section>

      <section className="card">
        <h3>AI Model Status</h3>
        <div className="table">
          <div className="table-head table-five">
            <span>Service</span>
            <span>Role</span>
            <span>Loaded</span>
            <span>Version</span>
            <span>RAM</span>
          </div>
          {(overview?.model_statuses ?? []).map((model) => (
            <div className="table-row table-five" key={`${model.service_name}-${model.model_role}`}>
              <span>{model.service_name}</span>
              <span>{model.model_role}</span>
              <span>{model.is_loaded ? "yes" : "no"}</span>
              <span>{model.version}</span>
              <span>{model.ram_usage_mb} MB</span>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h3>Companies</h3>
        <div className="table">
          <div className="table-head table-five">
            <span>Company</span>
            <span>Users</span>
            <span>Interviews</span>
            <span>Completed</span>
            <span>ID</span>
          </div>
          {companies.map((company) => (
            <div key={company.company_id} className="table-row table-five">
              <span>{company.company_name}</span>
              <span>{company.users_count}</span>
              <span>{company.interviews_count}</span>
              <span>{company.completed_interviews_count}</span>
              <span className="mono">{company.company_id.slice(0, 12)}...</span>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h3>Audit Feed</h3>
        <div className="table">
          <div className="table-head table-five">
            <span>Action</span>
            <span>Entity</span>
            <span>Company</span>
            <span>Time</span>
            <span>Payload</span>
          </div>
          {audit.map((item) => (
            <div key={item.id} className="table-row table-five">
              <span>{item.action}</span>
              <span>{item.entity_type}</span>
              <span className="mono">{item.company_id ? `${item.company_id.slice(0, 8)}...` : "-"}</span>
              <span>{new Date(item.created_at).toLocaleString()}</span>
              <span className="mono">{JSON.stringify(item.payload).slice(0, 38)}...</span>
            </div>
          ))}
        </div>
      </section>
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
