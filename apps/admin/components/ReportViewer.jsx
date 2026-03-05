export function ReportViewer({ report }) {
  if (!report) {
    return null;
  }

  return (
    <section>
      <h4>{report.report_type}</h4>
      <p>{report.summary}</p>
      <pre>{JSON.stringify(report.content, null, 2)}</pre>
    </section>
  );
}
