import { useState, useEffect } from "react";
import { getVerdicts, listBidders } from "../lib/api";
import { useAppStore } from "../lib/store";
import StatusBadge from "../components/StatusBadge";

export default function EvaluationResults({ onNext }: { onNext: () => void }) {
  const { activeTenderId, activeBidderId, setActiveBidder, unlockStep } = useAppStore();
  const [bidders, setBidders] = useState<any[]>([]);
  const [verdictData, setVerdictData] = useState<any>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeTenderId) return;
    listBidders(activeTenderId).then((r: any) => setBidders(r.data));
  }, [activeTenderId]);

  useEffect(() => {
    if (!activeBidderId) return;
    setLoading(true);
    getVerdicts(activeBidderId)
      .then((r: any) => setVerdictData(r.data))
      .finally(() => setLoading(false));
  }, [activeBidderId]);

  if (!activeTenderId)
    return <div className="page"><div className="card"><p>Please select a tender first.</p></div></div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Evaluation Results</h2>
        <p className="page-desc">View AI-generated verdicts for each bidder against the eligibility criteria.</p>
      </div>

      {bidders.length > 1 && (
        <div className="card">
          <h3>Select Bidder</h3>
          <div className="bidder-tabs">
            {bidders.filter((b) => b.status === "verdicts_computed").map((b) => (
              <button key={b.id}
                className={`btn ${activeBidderId === b.id ? "btn-primary" : ""}`}
                onClick={() => setActiveBidder(b.id)}>
                {b.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading && <div className="card"><div className="status-bar status-info"><div className="spinner" /> Loading verdicts...</div></div>}

      {verdictData && (
        <>
          <div className={`overall-verdict-card verdict-${verdictData.overall_verdict?.toLowerCase().replace(/ /g, "-")}`}>
            <h3>{verdictData.bidder_name}</h3>
            <div className="overall-verdict-label">Overall Verdict</div>
            <div className="overall-verdict-value">{verdictData.overall_verdict}</div>
          </div>

          <div className="card">
            <h3>Criterion-Level Verdicts</h3>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Criterion</th><th>Type</th><th>Mandatory</th>
                  <th>Extracted Value</th><th>Verdict</th><th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {verdictData.verdicts.map((v: any) => (
                  <>
                    <tr key={v.id} className="verdict-row" onClick={() => setExpanded(expanded === v.id ? null : v.id)}
                      style={{ cursor: "pointer" }}>
                      <td>{v.criterion_text}</td>
                      <td><StatusBadge status={v.criterion_type} size="sm" /></td>
                      <td>{v.is_mandatory ? "Yes" : "No"}</td>
                      <td className="value-cell">{v.extracted_value || "-"}</td>
                      <td><StatusBadge status={v.human_decision || v.verdict} /></td>
                      <td>
                        <span className="conf-inline">E:{(v.extraction_confidence * 100).toFixed(0)}%</span>
                        <span className="conf-inline">M:{(v.match_confidence * 100).toFixed(0)}%</span>
                      </td>
                    </tr>
                    {expanded === v.id && (
                      <tr key={`${v.id}-detail`} className="detail-row">
                        <td colSpan={6}>
                          <div className="verdict-detail">
                            <div className="detail-section">
                              <strong>Explanation:</strong>
                              <p>{v.explanation}</p>
                            </div>
                            {v.verbatim_quote && (
                              <div className="detail-section">
                                <strong>Source Quote:</strong>
                                <blockquote>{v.verbatim_quote}</blockquote>
                              </div>
                            )}
                            {v.source_doc && (
                              <div className="detail-section">
                                <strong>Source:</strong> {v.source_doc}
                              </div>
                            )}
                            {v.human_decision && (
                              <div className="detail-section">
                                <strong>Human Decision:</strong> {v.human_decision}
                                {v.human_reason && <p>Reason: {v.human_reason}</p>}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>

          <div className="page-actions">
            <button className="btn btn-primary" onClick={() => { unlockStep(4); onNext(); }}>
              Continue to Human Review
            </button>
          </div>
        </>
      )}
    </div>
  );
}
