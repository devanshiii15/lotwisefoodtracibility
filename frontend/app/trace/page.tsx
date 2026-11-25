"use client";

import { useState } from "react";
import {
  Search,
  ArrowDown,
  Download,
  Loader2,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SupplyChainGraph } from "@/components/supply-chain-graph";
import { api, TraceResult, GraphData } from "@/lib/api";

export default function TracePage() {
  const [lotId, setLotId] = useState("L204");
  const [result, setResult] = useState<TraceResult | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);

  async function runTrace() {
    const id = lotId.trim().toUpperCase();
    if (!id) return;
    setLoading(true);
    setResult(null);
    setGraph(null);
    try {
      const [tr, gr] = await Promise.all([api.trace(id), api.graph(id)]);
      setResult(tr);
      setGraph(gr);
      toast.success(`Traced lot ${id}`);
    } catch (e: any) {
      toast.error(e.message || "Trace failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trace Contamination</h1>
        <p className="text-muted-foreground">
          Enter a lot id (e.g. <span className="font-mono">L204</span>) to trace it
          through the supply chain and generate a recall report.
        </p>
      </div>

      <div className="flex gap-2">
        <Input
          value={lotId}
          onChange={(e) => setLotId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runTrace()}
          placeholder="Lot id, e.g. L204"
          className="max-w-xs font-mono"
        />
        <Button onClick={runTrace} disabled={loading}>
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
          Trace
        </Button>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          {/* Status banner */}
          <Card
            className={
              result.contaminated
                ? "border-destructive/40 bg-destructive/5"
                : "border-accent/40 bg-accent/5"
            }
          >
            <CardContent className="flex items-center gap-3 p-4">
              {result.contaminated ? (
                <AlertTriangle className="h-5 w-5 text-destructive" />
              ) : (
                <CheckCircle2 className="h-5 w-5 text-accent" />
              )}
              <span className="font-medium">
                Lot {result.lot_id} —{" "}
                {result.contaminated
                  ? "CONTAMINATED (positive lab report on record)"
                  : "No positive lab report on record"}
              </span>
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Flowchart (text) */}
            <Card>
              <CardHeader>
                <CardTitle>Trace Flow</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {result.steps.map((s, i) => (
                    <div key={i}>
                      <div className="rounded-lg border bg-muted/40 px-4 py-3">
                        <p className="text-xs font-semibold uppercase text-primary">
                          {s.step}
                        </p>
                        <p className="text-sm">{s.detail}</p>
                      </div>
                      {i < result.steps.length - 1 && (
                        <div className="flex justify-center py-1">
                          <ArrowDown className="h-4 w-4 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recall summary */}
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle>Recall Summary</CardTitle>
                <Button
                  variant="accent"
                  size="sm"
                  asChild
                >
                  <a href={api.reportUrl(result.lot_id)} target="_blank" rel="noreferrer">
                    <Download className="h-4 w-4" /> PDF
                  </a>
                </Button>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="whitespace-pre-wrap text-sm">{result.summary}</p>
                <div className="flex flex-wrap gap-2 pt-2">
                  <Badge variant="outline">
                    {result.batches.length} batches
                  </Badge>
                  <Badge variant="outline">
                    {result.shipments.length} shipments
                  </Badge>
                  <Badge variant="secondary">{result.supplier?.name}</Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* React Flow supply chain graph */}
          {graph && (
            <Card>
              <CardHeader>
                <CardTitle>Supply Chain Graph</CardTitle>
              </CardHeader>
              <CardContent>
                <SupplyChainGraph data={graph} />
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
