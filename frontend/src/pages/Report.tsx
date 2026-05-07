import { useState } from "react";
import { generateReport, downloadReportUrl } from "../lib/api";
import { useAppStore } from "../lib/store";

export default function Report() {
  const { activeTenderId } = useAppStore();
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!activeTenderId) return;
    setGenerating(true);
    setError("");
    try {
      await generateReport(activeTenderId);
      setGenerated(true);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Report generation failed");
    }
    setGenerating(false);
  };

  if (!activeTenderId)
    return <div className="page"><div className="card"><p>Please complete the evaluation first.</p></div></div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Generate Report</h2>
        <p className="page-desc">
          Generate a consolidated PDF evaluation report with all criteria, verdicts, and human review decisions.
        </p>
      </div>

      <div className="card report-card">
        <div className="report-icon">Report</div>
        <h3>Consolidated Evaluation PDF Report</h3>
        <p>The report will include:</p>
        <ul className="report-features">
          <li>Tender summary and extracted criteria</li>
          <li>Per-bidder evaluation breakdown with citations</li>
          <li>Human review decisions with reviewer attribution</li>
          <li>Professional PDF file for official use</li>
        </ul>

        {!generated ? (
          <button className="btn btn-primary btn-lg" onClick={handleGenerate} disabled={generating}>
            {generating ? (
              <><div className="spinner spinner-sm" /> Generating PDF...</>
            ) : (
              "Generate PDF Report"
            )}
          </button>
        ) : (
          <div className="report-ready">
            <div className="status-bar status-success">PDF report generated successfully.</div>
            <a href={downloadReportUrl(activeTenderId)} target="_blank" rel="noreferrer"
              className="btn btn-primary btn-lg">
              Download PDF Report
            </a>
          </div>
        )}

        {error && <div className="status-bar status-error">{error}</div>}
      </div>
    </div>
  );
}
