/**
 * Small typed client for the LotWise FastAPI backend.
 * Base URL comes from NEXT_PUBLIC_API_URL (default http://localhost:8000).
 */

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface DashboardStats {
  suppliers: number;
  lots: number;
  batches: number;
  shipments: number;
  lab_alerts: number;
  lab_breakdown: { name: string; value: number }[];
  supplier_lots: { name: string; lots: number }[];
}

export interface Source {
  source: string;
  dataset: string;
  record_id: string;
  text: string;
  score: number | null;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  sources: Source[];
}

export interface TraceStep {
  step: string;
  detail: string;
}

export interface TraceResult {
  found: boolean;
  lot_id: string;
  contaminated: boolean;
  lot: Record<string, any>;
  supplier: Record<string, any>;
  ingredient: string;
  batches: Record<string, any>[];
  shipments: Record<string, any>[];
  lab_reports: Record<string, any>[];
  steps: TraceStep[];
  summary: string;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  sublabel: string;
}

export interface GraphData {
  lot_id: string;
  contaminated: boolean;
  nodes: GraphNode[];
  edges: { id: string; source: string; target: string }[];
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  dashboard: () =>
    fetch(`${BASE}/api/dashboard/stats`).then((r) => handle<DashboardStats>(r)),

  chat: (question: string) =>
    fetch(`${BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then((r) => handle<ChatResponse>(r)),

  trace: (lot_id: string) =>
    fetch(`${BASE}/api/trace`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lot_id }),
    }).then((r) => handle<TraceResult>(r)),

  graph: (lot_id: string) =>
    fetch(`${BASE}/api/graph/${lot_id}`).then((r) => handle<GraphData>(r)),

  reportUrl: (lot_id: string) => `${BASE}/api/trace/${lot_id}/report`,

  upload: (datasetType: string, file: File) => {
    const form = new FormData();
    form.append("dataset_type", datasetType);
    form.append("file", file);
    return fetch(`${BASE}/api/upload`, { method: "POST", body: form }).then((r) =>
      handle<{ message: string; rows_loaded: number; documents_indexed: number }>(r)
    );
  },
};
