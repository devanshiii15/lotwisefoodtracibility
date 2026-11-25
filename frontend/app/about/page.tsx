import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Database, Brain, Workflow, Layers } from "lucide-react";

const stack = [
  "Next.js", "TypeScript", "Tailwind CSS", "shadcn/ui", "React Flow",
  "FastAPI", "SQLite", "Ollama Qwen3", "sentence-transformers/all-MiniLM-L6-v2",
  "ChromaDB", "LlamaIndex", "LangGraph",
];

const concepts = [
  {
    icon: Brain,
    title: "RAG Pipeline",
    body: "CSV records become natural-language documents, chunked and embedded with all-MiniLM-L6-v2, stored in ChromaDB. A retriever fetches the top matches and Qwen3 answers using only that context — every reply shows its sources.",
  },
  {
    icon: Workflow,
    title: "LangGraph Agents",
    body: "A supervisor node classifies intent, then routes to an Origin, Trace, or Report agent. All RAG agents share one retriever, so the whole graph reads from a single vector index.",
  },
  {
    icon: Database,
    title: "Structured Trace",
    body: "Contamination tracing is a deterministic SQLite traversal: Lot → Supplier → Ingredient → Batches → Shipments → Recall Summary. Reliable relationships, no hallucination.",
  },
  {
    icon: Layers,
    title: "Clean Separation",
    body: "SQLite handles exact structured queries; the RAG layer handles open-ended natural-language questions. Each is used where it is strongest.",
  },
];

export default function AboutPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">About LotWise</h1>
        <p className="text-muted-foreground max-w-2xl">
          LotWise is an AI food traceability assistant. It answers questions about
          food batches and traces contaminated lots using supplier records, batch
          records, and laboratory reports.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {concepts.map((c) => {
          const Icon = c.icon;
          return (
            <Card key={c.title}>
              <CardHeader className="flex-row items-center gap-3 space-y-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle>{c.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{c.body}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tech Stack</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {stack.map((s) => (
            <Badge key={s} variant="secondary">
              {s}
            </Badge>
          ))}
        </CardContent>
      </Card>

      <p className="text-sm text-muted-foreground">
        Built as a college demonstration project to showcase LLMs, RAG,
        LangGraph, agentic AI, FastAPI, and Next.js.
      </p>
    </div>
  );
}
