import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function LandingPage() {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function extractToken(value) {
    const raw = value.trim();
    if (!raw) {
      return "";
    }

    if (raw.includes("/interview/")) {
      const parts = raw.split("/interview/");
      const candidatePart = parts[parts.length - 1];
      return candidatePart.split("?")[0].split("#")[0];
    }

    return raw;
  }

  function onSubmit(event) {
    event.preventDefault();
    setError("");

    const normalizedToken = extractToken(token);
    if (normalizedToken.length < 10) {
      setError("Magic link token is too short.");
      return;
    }
    navigate(`/interview/${normalizedToken}`);
  }

  return (
    <main className="candidate-shell">
      <section className="hero-card">
        <h1>SkillGraph AI Interview</h1>
        <p>
          Structured interview platform with AI-generated role questions, sentiment analysis, and
          transparent scoring for hiring teams.
        </p>

        <div className="info-grid">
          <article>
            <h3>How It Works</h3>
            <p>HR sends a magic link. You pass AI interview + tests, then HR receives full structured report.</p>
          </article>
          <article>
            <h3>What Is Evaluated</h3>
            <p>Technical depth, soft skills, logical thinking, psychological stability and nervousness level.</p>
          </article>
          <article>
            <h3>Privacy</h3>
            <p>No registration required. Access is limited to your interview token and all anti-cheat events are logged.</p>
          </article>
        </div>

        <form onSubmit={onSubmit} className="token-form">
          <input
            placeholder="Paste token or full interview link"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            required
          />
          {error ? <div className="error-inline">{error}</div> : null}
          <button className="primary-btn" type="submit">
            Start interview
          </button>
        </form>
      </section>
    </main>
  );
}
