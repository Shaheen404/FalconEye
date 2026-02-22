import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import SearchForm from "./components/SearchForm";
import LogTerminal from "./components/LogTerminal";
import FinalReport from "./components/FinalReport";

const API_URL = "/api";

export default function App() {
  const [logs, setLogs] = useState([]);
  const [report, setReport] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  const handleLaunch = async (target, pineconeIndex) => {
    setLogs([]);
    setReport(null);
    setError(null);
    setRunning(true);

    try {
      const res = await fetch(`${API_URL}/crew/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target,
          pinecone_index: pineconeIndex || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const payload = JSON.parse(line.slice(6));

            if (payload.type === "log" || payload.type === "start") {
              setLogs((prev) => [
                ...prev,
                {
                  id: Date.now() + Math.random(),
                  type: payload.type,
                  message: payload.message,
                },
              ]);
            } else if (payload.type === "result") {
              setReport(payload.message);
            } else if (payload.type === "error") {
              setError(payload.message);
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-falcon-border px-6 py-4 flex items-center gap-3">
        <span className="text-2xl">🦅</span>
        <h1 className="text-xl font-bold tracking-wide text-falcon-accent">
          FalconEye
        </h1>
        <span className="text-falcon-muted text-sm ml-2">
          OSINT Command Center
        </span>
      </header>

      {/* Main */}
      <main className="flex-1 flex flex-col lg:flex-row gap-4 p-4 max-w-[1600px] mx-auto w-full">
        {/* Left panel – Search + Terminal */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <SearchForm onLaunch={handleLaunch} disabled={running} />

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="bg-red-900/30 border border-falcon-red rounded-lg px-4 py-3 text-falcon-red text-sm"
              >
                ⚠ {error}
              </motion.div>
            )}
          </AnimatePresence>

          <LogTerminal logs={logs} running={running} />
        </div>

        {/* Right panel – Report */}
        <div className="lg:w-[500px] flex-shrink-0">
          <FinalReport markdown={report} />
        </div>
      </main>
    </div>
  );
}
