interface Props {
  status: string;
  size?: "sm" | "md";
}

const colorMap: Record<string, string> = {
  Eligible: "badge-eligible",
  "Not Eligible": "badge-not-eligible",
  "Needs Manual Review": "badge-review",
  uploaded: "badge-info",
  extracting_criteria: "badge-info",
  criteria_extracted: "badge-success",
  approved: "badge-success",
  extracting_evidence: "badge-info",
  evidence_extracted: "badge-success",
  computing_verdicts: "badge-info",
  verdicts_computed: "badge-success",
  evaluating: "badge-info",
  completed: "badge-success",
};

export default function StatusBadge({ status, size = "md" }: Props) {
  const cls = colorMap[status] || "badge-info";
  return (
    <span className={`badge ${cls} ${size === "sm" ? "badge-sm" : ""}`}>
      {status}
    </span>
  );
}
