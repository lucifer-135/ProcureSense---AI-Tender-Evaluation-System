import { useState, useEffect } from "react";
import { getReviewQueue, submitReview } from "../lib/api";
import { useAppStore } from "../lib/store";

export default function HumanReview({ onNext }: { onNext: () => void }) {
  const { activeTenderId, unlockStep } = useAppStore();
  const [queue, setQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewData, setReviewData] = useState<Record<number, { decision: string; reason: string; reviewer: string }>>({});
  const [submitting, setSubmitting] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState<Set<number>>(new Set());

  const fetchQueue = async () => {
    if (!activeTenderId) return;
    setLoading(true);
    try {
      const res = await getReviewQueue(activeTenderId);
      setQueue(res.data);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchQueue(); }, [activeTenderId]);

  const handleSubmit = async (verdictId: number) => {
    const data = reviewData[verdictId];
    if (!data?.decision) return;
    setSubmitting(verdictId);
    try {
      await submitReview(verdictId, data);
      setSubmitted((prev) => new Set(prev).add(verdictId));
      fetchQueue();
    } catch {}
    setSubmitting(null);
  };

  const setField = (verdictId: number, field: string, value: string) => {
    setReviewData((prev) => ({
      ...prev,
      [verdictId]: { ...(prev[verdictId] || { decision: "", reason: "", reviewer: "" }), [field]: value },
    }));
  };

  const remaining = queue.length;

  if (!activeTenderId)
    return <div className="page"><div className="card"><p>Please select a tender first.</p></div></div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Human Review Queue</h2>
        <p className="page-desc">
          Review cases flagged by the AI as needing manual evaluation. {remaining} items remaining.
        </p>
      </div>

      {loading ? (
        <div className="card"><div className="status-bar status-info"><div className="spinner" /> Loading review queue...</div></div>
      ) : queue.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <span className="empty-icon">Complete</span>
            <h3>All Reviews Complete</h3>
            <p>No items require manual review. You can proceed to generate the report.</p>
          </div>
          <div className="page-actions">
            <button className="btn btn-primary btn-lg" onClick={() => { unlockStep(5); onNext(); }}>
              Generate Report
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="review-count">
            <span className="review-badge">{remaining}</span> items need your review
          </div>

          {queue.map((item) => (
            <div key={item.verdict_id} className={`card review-card ${submitted.has(item.verdict_id) ? "review-done" : ""}`}>
              <div className="review-header">
                <div>
                  <span className="review-bidder">{item.bidder_name}</span>
                  <span className={`badge badge-sm badge-${item.criterion_type.toLowerCase()}`}>{item.criterion_type}</span>
                </div>
                <span className="conf-tag">
                  E: {(item.extraction_confidence * 100).toFixed(0)}% | M: {(item.match_confidence * 100).toFixed(0)}%
                </span>
              </div>

              <div className="review-criterion">
                <strong>Criterion:</strong> {item.criterion_text}
              </div>

              {item.extracted_value && (
                <div className="review-evidence">
                  <strong>Extracted Value:</strong> {item.extracted_value}
                </div>
              )}

              {item.verbatim_quote && (
                <blockquote className="review-quote">{item.verbatim_quote}</blockquote>
              )}

              <div className="review-reason">
                <strong>Why flagged:</strong> {item.explanation}
              </div>

              {!submitted.has(item.verdict_id) && (
                <div className="review-form">
                  <div className="review-decision">
                    <label className={`radio-card ${reviewData[item.verdict_id]?.decision === "Eligible" ? "radio-selected-eligible" : ""}`}>
                      <input type="radio" name={`d-${item.verdict_id}`}
                        onChange={() => setField(item.verdict_id, "decision", "Eligible")} />
                      Eligible
                    </label>
                    <label className={`radio-card ${reviewData[item.verdict_id]?.decision === "Not Eligible" ? "radio-selected-not" : ""}`}>
                      <input type="radio" name={`d-${item.verdict_id}`}
                        onChange={() => setField(item.verdict_id, "decision", "Not Eligible")} />
                      Not Eligible
                    </label>
                  </div>
                  <textarea placeholder="Reason for your decision..."
                    onChange={(e) => setField(item.verdict_id, "reason", e.target.value)} />
                  <input type="text" className="form-input" placeholder="Your name"
                    onChange={(e) => setField(item.verdict_id, "reviewer", e.target.value)} />
                  <button className="btn btn-primary"
                    onClick={() => handleSubmit(item.verdict_id)}
                    disabled={submitting === item.verdict_id || !reviewData[item.verdict_id]?.decision}>
                    {submitting === item.verdict_id ? "Submitting..." : "Submit Review"}
                  </button>
                </div>
              )}

              {submitted.has(item.verdict_id) && (
                <div className="status-bar status-success">Review submitted</div>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
