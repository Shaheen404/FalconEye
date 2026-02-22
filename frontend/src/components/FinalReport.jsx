import ReactMarkdown from "react-markdown";
import { motion } from "framer-motion";

export default function FinalReport({ markdown }) {
  return (
    <div className="bg-falcon-surface border border-falcon-border rounded-lg flex flex-col h-full min-h-[400px]">
      {/* Title bar */}
      <div className="px-4 py-2 border-b border-falcon-border flex items-center gap-2">
        <span className="text-falcon-green text-sm">📋</span>
        <span className="text-sm text-falcon-muted">Final Report</span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto terminal-scroll p-4">
        {!markdown ? (
          <p className="text-falcon-muted text-sm">
            No report yet. The final report will appear here after the crew
            finishes its analysis.
          </p>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            className="prose prose-invert prose-sm max-w-none
                       prose-headings:text-falcon-accent prose-a:text-falcon-accent
                       prose-strong:text-gray-100 prose-code:text-falcon-green
                       prose-code:bg-falcon-bg prose-code:px-1 prose-code:py-0.5
                       prose-code:rounded prose-pre:bg-falcon-bg prose-pre:border
                       prose-pre:border-falcon-border"
          >
            <ReactMarkdown>{markdown}</ReactMarkdown>
          </motion.div>
        )}
      </div>
    </div>
  );
}
