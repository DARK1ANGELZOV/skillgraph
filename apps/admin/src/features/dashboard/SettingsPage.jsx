import { useEffect, useState } from "react";

import { api } from "../../lib/api";

export function SettingsPage() {
  const [company, setCompany] = useState(null);
  const [billing, setBilling] = useState(null);
  const [invite, setInvite] = useState({ email: "", role: "HR_JUNIOR" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api("/companies/current"), api("/companies/billing")])
      .then(([companyData, billingData]) => {
        setCompany(companyData);
        setBilling(billingData);
      })
      .catch((err) => setError(err.message));
  }, []);

  async function updateCompany(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const updated = await api("/companies/current", {
        method: "PUT",
        body: JSON.stringify({ name: company.name })
      });
      setCompany(updated);
      setMessage("Company updated");
    } catch (err) {
      setError(err.message);
    }
  }

  async function sendInvite(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const data = await api("/auth/invites", {
        method: "POST",
        body: JSON.stringify(invite)
      });
      setMessage(`Invite token: ${data.token}`);
      setInvite({ email: "", role: "HR_JUNIOR" });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="grid-layout">
      <section className="card">
        <h3>Company Settings</h3>
        <form onSubmit={updateCompany} className="form-grid">
          <input
            value={company?.name ?? ""}
            onChange={(event) => setCompany((prev) => ({ ...prev, name: event.target.value }))}
          />
          <button className="primary-btn" type="submit">
            Save
          </button>
        </form>
      </section>

      <section className="card">
        <h3>Invite Team Member</h3>
        <form onSubmit={sendInvite} className="form-grid">
          <input
            type="email"
            value={invite.email}
            placeholder="Email"
            onChange={(event) => setInvite((prev) => ({ ...prev, email: event.target.value }))}
            required
          />
          <select value={invite.role} onChange={(event) => setInvite((prev) => ({ ...prev, role: event.target.value }))}>
            <option value="HR_SENIOR">HR_SENIOR</option>
            <option value="HR_JUNIOR">HR_JUNIOR</option>
            <option value="SUPERVISOR">SUPERVISOR</option>
          </select>
          <button className="primary-btn" type="submit">
            Send invite
          </button>
        </form>
      </section>

      <section className="card">
        <h3>Billing</h3>
        <pre>{JSON.stringify(billing, null, 2)}</pre>
      </section>

      {message ? <div className="success-box">{message}</div> : null}
      {error ? <div className="error-box">{error}</div> : null}
    </div>
  );
}
