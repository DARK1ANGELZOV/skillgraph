export function SkillGraph({ score }) {
  const value = Number(score ?? 0);
  return (
    <div>
      <h4>SkillGraph Score</h4>
      <progress max="100" value={value} />
      <p>{value}%</p>
    </div>
  );
}
