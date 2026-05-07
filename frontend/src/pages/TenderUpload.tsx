import { useState, useEffect } from "react";
import { Trash2 } from "lucide-react";
import FileDropzone from "../components/FileDropzone";
import StatusBadge from "../components/StatusBadge";
import { uploadTender, listTenders, getTender, deleteTender } from "../lib/api";
import { useAppStore } from "../lib/store";

export default function TenderUpload({ onNext }: { onNext: () => void }) {
  const [tenders, setTenders] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const { setActiveTender, activeTenderId, unlockStep, resetProgress } = useAppStore();

  const syncTenderProgress = (status: string) => {
    if (status === "approved") {
      unlockStep(2);
      return;
    }

    if (status !== "uploaded" && status !== "extracting_criteria") {
      unlockStep(1);
      return;
    }

    resetProgress(0);
  };

  const fetchTenders = async () => {
    try {
      const res = await listTenders();
      setTenders(res.data);
    } catch {}
  };

  useEffect(() => {
    fetchTenders();
  }, []);

  const handleUpload = async (files: File[]) => {
    setUploading(true);
    setError("");
    resetProgress(0);
    try {
      const res = await uploadTender(files[0]);
      const tenderId = res.data.id;
      setActiveTender(tenderId);
      setProcessing(true);

      // Poll until criteria are extracted
      const poll = setInterval(async () => {
        try {
          const t = await getTender(tenderId);
          if (t.data.status !== "uploaded" && t.data.status !== "extracting_criteria") {
            clearInterval(poll);
            setProcessing(false);
            syncTenderProgress(t.data.status);
            fetchTenders();
          }
        } catch {}
      }, 2000);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Upload failed");
    }
    setUploading(false);
  };

  const selectTender = (id: number) => {
    setActiveTender(id);
  };

  const handleDeleteTender = async (tender: any) => {
    const confirmed = window.confirm(
      `Delete "${tender.filename}" and all related bidders, criteria, reviews, and reports?`
    );
    if (!confirmed) return;

    setDeletingId(tender.id);
    setError("");
    try {
      await deleteTender(tender.id);
      setTenders((items) => items.filter((item) => item.id !== tender.id));
      if (activeTenderId === tender.id) {
        setActiveTender(null);
        resetProgress(0);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Could not delete tender");
    } finally {
      setDeletingId(null);
    }
  };

  useEffect(() => {
    const activeTender = tenders.find((t) => t.id === activeTenderId);
    if (activeTender) {
      syncTenderProgress(activeTender.status);
    }
  }, [activeTenderId, tenders]);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Upload Tender Document</h2>
        <p className="page-desc">
          Upload a tender PDF to automatically extract eligibility criteria using AI.
        </p>
      </div>

      <div className="card">
        <FileDropzone
          onFiles={handleUpload}
          label="Drop your tender PDF here, or click to browse"
        />
        {uploading && (
          <div className="status-bar status-info">
            <div className="spinner" /> Uploading document...
          </div>
        )}
        {processing && (
          <div className="status-bar status-info">
            <div className="spinner" /> AI is extracting eligibility criteria... This may take a minute.
          </div>
        )}
        {error && <div className="status-bar status-error">{error}</div>}
      </div>

      {tenders.length > 0 && (
        <div className="card">
          <h3>Previous Tenders</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Filename</th>
                <th>Status</th>
                <th>Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {tenders.map((t) => (
                <tr
                  key={t.id}
                  className={activeTenderId === t.id ? "row-active" : ""}
                >
                  <td>{t.id}</td>
                  <td>{t.filename}</td>
                  <td><StatusBadge status={t.status} size="sm" /></td>
                  <td>{new Date(t.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="table-actions">
                      <button
                        className="btn btn-sm"
                        onClick={() => {
                          selectTender(t.id);
                          syncTenderProgress(t.status);
                          if (t.status !== "uploaded" && t.status !== "extracting_criteria") {
                            onNext();
                          }
                        }}
                      >
                        {activeTenderId === t.id ? "Selected" : "Select"}
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        disabled={deletingId === t.id}
                        title="Delete tender"
                        aria-label={`Delete ${t.filename}`}
                        onClick={() => handleDeleteTender(t)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTenderId && !processing && (
        <div className="page-actions">
          <button
            className="btn btn-primary"
            onClick={onNext}
            disabled={!tenders.some((t) => t.id === activeTenderId && t.status !== "uploaded" && t.status !== "extracting_criteria")}
          >
            Continue to Review Criteria
          </button>
        </div>
      )}
    </div>
  );
}
