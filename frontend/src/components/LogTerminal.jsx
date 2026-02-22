import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function LogTerminal({ logs, running }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="flex-1 bg-falcon-surface border border-falcon-border rounded-lg flex flex-col min-h-[400px]">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-falcon-border">
        <span className="w-3 h-3 rounded-full bg-falcon-red" />
        <span className="w-3 h-3 rounded-full bg-yellow-500" />
        <span className="w-3 h-3 rounded-full bg-falcon-green" />
        <span className="ml-3 text-xs text-falcon-muted">agent-logs</span>
      </div>

      {/* Log content */}
      <div className="flex-1 overflow-y-auto terminal-scroll p-4 text-xs leading-relaxed">
        {logs.length === 0 && !running && (
          <p className="text-falcon-muted">
            Waiting for input… Launch a crew to see live agent logs here.
          </p>
        )}

        <AnimatePresence initial={false}>
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.15 }}
              className="mb-1"
            >
              <span className="text-falcon-accent mr-2">▸</span>
              <span className="text-gray-300">{log.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>

        {running && (
          <span className="inline-block w-2 h-4 bg-falcon-accent cursor-blink ml-1" />
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
