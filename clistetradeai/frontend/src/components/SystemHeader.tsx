import { Cpu, Database, ShieldCheck } from "lucide-react";
import type React from "react";
import type { MarketRequest } from "../types/market";

interface SystemHeaderProps {
  activeStage: string | null;
  request: MarketRequest;
}

export function SystemHeader({ activeStage, request }: SystemHeaderProps) {
  return (
    <header className="system-header">
      <div>
        <p className="eyebrow">Institutional Multi-Agent Terminal</p>
        <h1>{request.ticker} Financial Intelligence Workflow</h1>
      </div>
      <div className="system-status">
        <StatusPill icon={<Database size={15} />} label="Tool pipelines" value="5 connected" />
        <StatusPill icon={<Cpu size={15} />} label="Active stage" value={activeStage ? activeStage.replace(/_/g, " ") : "idle"} />
        <StatusPill icon={<ShieldCheck size={15} />} label="Risk profile" value={request.riskTolerance} />
      </div>
    </header>
  );
}

function StatusPill({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="status-pill">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
