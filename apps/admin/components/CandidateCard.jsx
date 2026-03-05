export function CandidateCard({ candidate }) {
  if (!candidate) {
    return null;
  }

  return (
    <article>
      <h4>{candidate.full_name}</h4>
      <p>{candidate.email}</p>
      <small>Status: {candidate.status}</small>
    </article>
  );
}
