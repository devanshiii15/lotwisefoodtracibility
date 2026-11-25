"use client";

import { useState } from "react";
import { Send, Bot, User, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, Source } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  intent?: string;
  sources?: Source[];
}

const EXAMPLES = [
  "Where did Batch B180 originate?",
  "Which supplier provided Lot L205?",
  "What ingredient is inside Lot L204?",
  "Show the contamination history for L204",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send(question: string) {
    if (!question.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chat(question);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.answer,
          intent: res.intent,
          sources: res.sources,
        },
      ]);
    } catch (e: any) {
      toast.error("Chat failed: " + e.message);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry, something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Chat</h1>
        <p className="text-muted-foreground">
          Grounded answers from your records. Every reply shows its sources.
        </p>
      </div>

      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => send(ex)}
              className="rounded-full border bg-card px-3 py-1.5 text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      <div className="space-y-4">
        {messages.map((m, i) => (
          <div key={i} className="animate-fade-in">
            <div className="flex items-start gap-3">
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  m.role === "user" ? "bg-primary text-white" : "bg-accent text-white"
                }`}
              >
                {m.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>
              <div className="flex-1">
                <Card>
                  <CardContent className="p-4">
                    <p className="whitespace-pre-wrap text-sm">{m.content}</p>
                    {m.intent && (
                      <Badge variant="secondary" className="mt-2">
                        intent: {m.intent}
                      </Badge>
                    )}
                  </CardContent>
                </Card>

                {m.sources && m.sources.length > 0 && (
                  <div className="mt-2 space-y-1.5">
                    <p className="text-xs font-medium text-muted-foreground">
                      Sources
                    </p>
                    {m.sources.map((s, si) => (
                      <div
                        key={si}
                        className="flex items-start gap-2 rounded-md border bg-muted/40 px-3 py-2 text-xs"
                      >
                        <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                        <div>
                          <span className="font-mono font-medium text-primary">
                            {s.source}
                          </span>
                          {s.score != null && (
                            <span className="ml-2 text-muted-foreground">
                              score {s.score}
                            </span>
                          )}
                          <p className="text-muted-foreground">{s.text}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Thinking…
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="sticky bottom-4 flex gap-2"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a batch, lot, supplier, or contamination…"
          disabled={loading}
        />
        <Button type="submit" disabled={loading || !input.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
