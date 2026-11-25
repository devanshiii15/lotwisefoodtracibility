"use client";

import { useRef, useState } from "react";
import { UploadCloud, Loader2, FileCheck2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

const TYPES = [
  { value: "suppliers", label: "Suppliers" },
  { value: "lots", label: "Lots" },
  { value: "batches", label: "Batches" },
  { value: "shipments", label: "Shipments" },
  { value: "lab_reports", label: "Lab Reports" },
];

export default function UploadPage() {
  const [type, setType] = useState("suppliers");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleUpload() {
    if (!file) {
      toast.error("Choose a CSV file first.");
      return;
    }
    setLoading(true);
    try {
      const res = await api.upload(type, file);
      toast.success(
        `${res.rows_loaded} rows loaded · ${res.documents_indexed} documents indexed`
      );
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (e: any) {
      toast.error("Upload failed: " + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload CSV</h1>
        <p className="text-muted-foreground">
          Upload a dataset. It is loaded into SQLite and automatically indexed
          into ChromaDB for retrieval.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Import a dataset</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium">Dataset type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">CSV file</label>
            <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-input bg-muted/30 px-6 py-10 text-center hover:border-primary transition-colors">
              {file ? (
                <>
                  <FileCheck2 className="h-8 w-8 text-accent" />
                  <span className="text-sm font-medium">{file.name}</span>
                </>
              ) : (
                <>
                  <UploadCloud className="h-8 w-8 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Click to select a .csv file
                  </span>
                </>
              )}
              <input
                ref={inputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
          </div>

          <Button onClick={handleUpload} disabled={loading} className="w-full">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Uploading & indexing…
              </>
            ) : (
              <>
                <UploadCloud className="h-4 w-4" /> Upload & Index
              </>
            )}
          </Button>

          <p className="text-xs text-muted-foreground">
            Column headers must match the sample files in <code>/data</code>.
            Uploading replaces that dataset and rebuilds the vector index.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
