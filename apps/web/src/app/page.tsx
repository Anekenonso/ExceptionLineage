"use client";

import { useEffect, useState } from "react";

interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

type ConnectionStatus = "checking" | "connected" | "error";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("checking");
  const [environment, setEnvironment] = useState<string>("development");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    setEnvironment(process.env.NODE_ENV || "development");

    async function checkHealth() {
      try {
        const response = await fetch(`${apiUrl}/health`);
        if (response.ok) {
          const data: HealthResponse = await response.json();
          setHealth(data);
          setConnectionStatus("connected");
        } else {
          setConnectionStatus("error");
        }
      } catch {
        setConnectionStatus("error");
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="flex-1 flex items-center justify-center p-8">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-foreground mb-3">
            ExceptionLineage
          </h1>
          <p className="text-lg text-foreground/60">
            Evidence-backed investigation
            <br />
            for enterprise transaction exceptions.
          </p>
        </div>

        {/* Status Card */}
        <div className="rounded-xl border border-foreground/10 bg-foreground/[0.02] p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground/40 mb-5">
            System Status
          </h2>

          <div className="space-y-4">
            {/* API Connection */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-foreground/70">API Connection</span>
              <StatusIndicator status={connectionStatus} />
            </div>

            {/* Environment */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-foreground/70">Environment</span>
              <span className="text-sm font-mono text-foreground/50">
                {environment}
              </span>
            </div>

            {/* Version */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-foreground/70">Version</span>
              <span className="text-sm font-mono text-foreground/50">
                {health?.version ?? "—"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function StatusIndicator({ status }: { status: ConnectionStatus }) {
  const config = {
    checking: { color: "bg-yellow-400", label: "Checking…" },
    connected: { color: "bg-emerald-400", label: "Connected" },
    error: { color: "bg-red-400", label: "Unavailable" },
  };

  const { color, label } = config[status];

  return (
    <span className="inline-flex items-center gap-2 text-sm text-foreground/50">
      <span
        className={`inline-block h-2 w-2 rounded-full ${color} ${
          status === "checking" ? "animate-pulse" : ""
        }`}
      />
      {label}
    </span>
  );
}
