import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000/api" });

// ── Tenders ────────────────────────────────────────────────────
export const uploadTender = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/tenders/upload", form);
};
export const listTenders = () => api.get("/tenders/");
export const getTender = (id: number) => api.get(`/tenders/${id}`);
export const deleteTender = (id: number) => api.delete(`/tenders/${id}`);
export const listCriteria = (tenderId: number) =>
  api.get(`/tenders/${tenderId}/criteria`);
export const addCriterion = (tenderId: number, data: any) =>
  api.post(`/tenders/${tenderId}/criteria`, data);
export const updateCriterion = (id: number, data: any) =>
  api.put(`/tenders/criteria/${id}`, data);
export const deleteCriterion = (id: number) =>
  api.delete(`/tenders/criteria/${id}`);
export const approveCriteria = (tenderId: number) =>
  api.post(`/tenders/${tenderId}/approve-criteria`);

// ── Bidders ────────────────────────────────────────────────────
export const uploadBidder = (tenderId: number, name: string, files: File[]) => {
  const form = new FormData();
  form.append("name", name);
  files.forEach((f) => form.append("files", f));
  return api.post(`/tenders/${tenderId}/bidders/upload`, form);
};
export const listBidders = (tenderId: number) =>
  api.get(`/tenders/${tenderId}/bidders`);
export const getBidder = (id: number) => api.get(`/bidders/${id}`);
export const deleteBidder = (id: number) => api.delete(`/bidders/${id}`);

// ── Evidence & Verdicts ────────────────────────────────────────
export const getEvidence = (bidderId: number) =>
  api.get(`/bidders/${bidderId}/evidence`);
export const getVerdicts = (bidderId: number) =>
  api.get(`/bidders/${bidderId}/verdicts`);

// ── Review ─────────────────────────────────────────────────────
export const getReviewQueue = (tenderId: number) =>
  api.get(`/tenders/${tenderId}/review-queue`);
export const submitReview = (verdictId: number, data: any) =>
  api.post(`/verdicts/${verdictId}/review`, data);

// ── Report ─────────────────────────────────────────────────────
export const generateReport = (tenderId: number) =>
  api.post(`/tenders/${tenderId}/report`);
export const downloadReportUrl = (tenderId: number) =>
  `http://localhost:8000/api/tenders/${tenderId}/report/download`;

export default api;
