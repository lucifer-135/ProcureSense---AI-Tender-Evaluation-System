import { useState, useEffect } from "react";
import { Trash2 } from "lucide-react";
import FileDropzone from "../components/FileDropzone";
import StatusBadge from "../components/StatusBadge";
import { uploadBidder, listBidders, getBidder, deleteBidder } from "../lib/api";
import { useAppStore } from "../lib/store";

export default function BidderUpload({ onNext }: { onNext: () => void }) {
  const { activeTenderId, activeBidderId, setActiveBidder, unlockStep } = useAppStore();
  const [bidders, setBidders] = useState<any[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const fetchBidders = async () => {
    if (!activeTenderId) return;
    try {
      const res = await listBidders(activeTenderId);
      setBidders(res.data);
    } catch {}
  };

  useEffect(() => { fetchBidders(); }, [activeTenderId]);

  const handleUpload = async () => {
    if (!activeTenderId || files.length === 0) {
      setError("Please select at least one PDF file.");
      return;
    }
    setUploading(true);
    setError("");
    try {
      const selectedFiles = [...files];
      const createdBidderIds: number[] = [];

      for (const file of selectedFiles) {
        const res = await uploadBidder(activeTenderId, "Extracting Name...", [file]);
        createdBidderIds.push(res.data.id);
      }

      if (createdBidderIds.length > 0) {
        setActiveBidder(createdBidderIds[createdBidderIds.length - 1]);
      }

      setProcessing(true);
      setFiles([]);
      fetchBidders();

      await Promise.all(
        createdBidderIds.map(
          (bidderId) =>
            new Promise<void>((resolve) => {
              const poll = setInterval(async () => {
                try {
                  const b = await getBidder(bidderId);
                  fetchBidders(); // Refresh to show detected names and statuses
                  if (b.data.status === "verdicts_computed") {
                    clearInterval(poll);
                    resolve();
                  }
                } catch {
                  clearInterval(poll);
                  resolve();
                }
              }, 3000);
            })
        )
      );

      setProcessing(false);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Upload failed");
      setProcessing(false);
    }
    setUploading(false);
  };

  const handleDeleteBidder = async (bidder: any) => {
    const confirmed = window.confirm(
      `Delete "${bidder.name}" and all related documents, evidence, verdicts, and reviews?`
    );
    if (!confirmed) return;

    setDeletingId(bidder.id);
    setError("");
    try {
      await deleteBidder(bidder.id);
      setBidders((items) => items.filter((item) => item.id !== bidder.id));
      if (activeBidderId === bidder.id) {
        setActiveBidder(null);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Could not delete bidder");
    } finally {
      setDeletingId(null);
    }
  };

  if (!activeTenderId)
    return <div className="page"><div className="card"><p>Please select and approve a tender first.</p></div></div>;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Upload Bidder Documents</h2>
        <p className="page-desc">
          Upload bidder submission files. Each selected file is processed as a separate bidder, and AI will compute verdicts automatically.
        </p>
      </div>

      <div className="card">
        <FileDropzone
          onFiles={(f) => setFiles((prev) => [...prev, ...f])}
          multiple
          label="Drop bidder documents (PDFs) here, or click to browse"
        />
        {files.length > 0 && (
          <div className="file-list">
            {files.map((f, i) => (
              <div key={i} className="file-item">
                <span>{f.name}</span>
                <button className="btn btn-sm btn-danger" onClick={() => setFiles(files.filter((_, j) => j !== i))}>Remove</button>
              </div>
            ))}
          </div>
        )}
        <button className="btn btn-primary" onClick={handleUpload} disabled={uploading || processing}
          style={{ marginTop: "1rem" }}>
          {uploading ? "Uploading..." : "Upload & Process"}
        </button>
        {processing && (
          <div className="status-bar status-info">
            <div className="spinner" /> AI is extracting evidence and computing verdicts... This may take a few minutes.
          </div>
        )}
        {error && <div className="status-bar status-error">{error}</div>}
      </div>

      {bidders.length > 0 && (
        <div className="card">
          <h3>Uploaded Bidders</h3>
          <table className="data-table">
            <thead>
              <tr><th>Name</th><th>Status</th><th>Overall Verdict</th><th>Action</th></tr>
            </thead>
            <tbody>
              {bidders.map((b) => (
                <tr key={b.id} className={activeBidderId === b.id ? "row-active" : ""}>
                  <td>{b.name}</td>
                  <td><StatusBadge status={b.status} size="sm" /></td>
                  <td>{b.overall_verdict ? <StatusBadge status={b.overall_verdict} size="sm" /> : "-"}</td>
                  <td>
                    <div className="table-actions">
                      <button className="btn btn-sm" onClick={() => { setActiveBidder(b.id); unlockStep(3); onNext(); }}
                        disabled={b.status !== "verdicts_computed"}>
                        View Results
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        disabled={deletingId === b.id}
                        title="Delete bidder"
                        aria-label={`Delete ${b.name}`}
                        onClick={() => handleDeleteBidder(b)}
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

      {bidders.some((b) => b.status === "verdicts_computed") && (
        <div className="page-actions">
          <button
            className="btn btn-primary"
            onClick={() => {
              const selectedBidder =
                bidders.find((b) => b.id === activeBidderId && b.status === "verdicts_computed") ||
                bidders.find((b) => b.status === "verdicts_computed");

              if (!selectedBidder) {
                return;
              }

              setActiveBidder(selectedBidder.id);
              unlockStep(3);
              onNext();
            }}
          >
            Continue to Evaluation Results
          </button>
        </div>
      )}
    </div>
  );
}
