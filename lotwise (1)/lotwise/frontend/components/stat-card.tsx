import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  tone?: "blue" | "green" | "red";
}

const tones = {
  blue: "bg-primary/10 text-primary",
  green: "bg-accent/10 text-accent",
  red: "bg-destructive/10 text-destructive",
};

export function StatCard({ label, value, icon: Icon, tone = "blue" }: StatCardProps) {
  return (
    <Card className="animate-fade-in">
      <CardContent className="flex items-center gap-4 p-6">
        <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl", tones[tone])}>
          <Icon className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}
