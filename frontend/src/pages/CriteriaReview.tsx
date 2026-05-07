import { useState, useEffect } from "react";
import {
  listCriteria,
  updateCriterion,
  deleteCriterion,
  addCriterion,
  approveCriteria,
} from "../lib/api";
import { useAppStore } from "../lib/store";
import StatusBadge from "../components/StatusBadge";

export default function CriteriaReview({ onNext }: { onNext: () => void }) {
  const { activeTenderId, unlockStep } = useAppStore();
  const [criteria, setCriteria] = useState<any[]>([]);
  const [editing, setEditing] = useState<number | null>(null);
  const [editData, setEditData] = useState<any>({});
  const [showAdd, setShowAdd] = useState(false);
  const [newCrit, setNewCrit] = useState({ text: "", type: "Technical", is_mandatory: true, threshold: "" });
  const [loading, setLoading] = useState(true);

  const fetchCriteria = async () => {
    if (!activeTenderId) return;
    setLoading(true);
    try {
      const res = await listCriteria(activeTenderId);
      setCriteria(res.data);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchCriteria(); }, [activeTenderId]);

  const handleEdit = (c: any) => {
    setEditing(c.id);
    setEditData({ text: c.text, type: c.type, is_mandatory: c.is_mandatory, threshold: c.threshold });
  };

  const handleSave = async (id: number) => {
    await updateCriterion(id, editData);
    setEditing(null);
    fetchCriteria();
  };

  const handleDelete = async (id: number) => {
    if (confirm("Delete this criterion?")) {
      await deleteCriterion(id);
      fetchCriteria();
    }
  };

  const handleAdd = async () => {
    if (!activeTenderId || !newCrit.text.trim()) return;
    await addCriterion(activeTenderId, newCrit);
    setNewCrit({ text: "", type: "Technical", is_mandatory: true, threshold: "" });
    setShowAdd(false);
    fetchCriteria();
  };

  const handleApprove = async () => {
    if (!activeTenderId) return;
    await approveCriteria(activeTenderId);
    unlockStep(2);
    onNext();
  };

  const getConfClass = (c: number) =>
    c >= 0.85 ? "conf-high" : c >= 0.6 ? "conf-med" : "conf-low";

  if (!activeTenderId)
    return <div className="page"><div className="card"><p>Please select a tender first.</p></div></div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Review Extracted Criteria</h2>
        <p className="page-desc">
          Review the AI-extracted eligibility criteria. Edit, add, or remove criteria before approving.
        </p>
      </div>

      {loading ? (
        <div className="card"><div className="status-bar status-info"><div className="spinner" /> Loading criteria...</div></div>
      ) : (
        <>
          <div className="card">
            <div className="card-header">
              <h3>{criteria.length} Criteria Found</h3>
              <button className="btn btn-sm" onClick={() => setShowAdd(!showAdd)}>
                {showAdd ? "Cancel" : "+ Add Criterion"}
              </button>
            </div>

            {showAdd && (
              <div className="add-form">
                <textarea
                  placeholder="Criterion text..."
                  value={newCrit.text}
                  onChange={(e) => setNewCrit({ ...newCrit, text: e.target.value })}
                />
                <div className="add-form-row">
                  <select value={newCrit.type} onChange={(e) => setNewCrit({ ...newCrit, type: e.target.value })}>
                    <option>Technical</option>
                    <option>Financial</option>
                    <option>Compliance</option>
                  </select>
                  <label className="toggle-label">
                    <input type="checkbox" checked={newCrit.is_mandatory}
                      onChange={(e) => setNewCrit({ ...newCrit, is_mandatory: e.target.checked })} />
                    Mandatory
                  </label>
                  <input placeholder="Threshold" value={newCrit.threshold}
                    onChange={(e) => setNewCrit({ ...newCrit, threshold: e.target.value })} />
                  <button className="btn btn-primary btn-sm" onClick={handleAdd}>Add</button>
                </div>
              </div>
            )}

            <table className="data-table">
              <thead>
                <tr>
                  <th style={{width: "40%"}}>Criterion</th>
                  <th>Type</th>
                  <th>Mandatory</th>
                  <th>Threshold</th>
                  <th>Confidence</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {criteria.map((c) => (
                  <tr key={c.id} className={c.confidence < 0.6 ? "row-warning" : ""}>
                    {editing === c.id ? (
                      <>
                        <td>
                          <textarea className="inline-edit" value={editData.text}
                            onChange={(e) => setEditData({ ...editData, text: e.target.value })} />
                        </td>
                        <td>
                          <select className="inline-edit" value={editData.type}
                            onChange={(e) => setEditData({ ...editData, type: e.target.value })}>
                            <option>Technical</option><option>Financial</option><option>Compliance</option>
                          </select>
                        </td>
                        <td>
                          <input type="checkbox" checked={editData.is_mandatory}
                            onChange={(e) => setEditData({ ...editData, is_mandatory: e.target.checked })} />
                        </td>
                        <td>
                          <input className="inline-edit" value={editData.threshold}
                            onChange={(e) => setEditData({ ...editData, threshold: e.target.value })} />
                        </td>
                        <td>-</td>
                        <td>
                          <div className="table-actions">
                          <button className="btn btn-sm btn-primary" onClick={() => handleSave(c.id)}>Save</button>
                          <button className="btn btn-sm" onClick={() => setEditing(null)}>Cancel</button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td>{c.text}</td>
                        <td><StatusBadge status={c.type} size="sm" /></td>
                        <td>{c.is_mandatory ? "Mandatory" : "Optional"}</td>
                        <td>{c.threshold || "-"}</td>
                        <td><span className={`conf ${getConfClass(c.confidence)}`}>{(c.confidence * 100).toFixed(0)}%</span></td>
                        <td>
                          <div className="table-actions">
                          <button className="btn btn-sm" onClick={() => handleEdit(c)}>Edit</button>
                          <button className="btn btn-sm btn-danger" onClick={() => handleDelete(c.id)}>Delete</button>
                          </div>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="page-actions">
            <button className="btn btn-primary btn-lg" onClick={handleApprove}>
              Approve Criteria &amp; Proceed
            </button>
          </div>
        </>
      )}
    </div>
  );
}
