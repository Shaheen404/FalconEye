import { useState } from "react";
import { motion } from "framer-motion";

export default function SearchForm({ onLaunch, disabled }) {
  const [target, setTarget] = useState("");
  const [pineconeIndex, setPineconeIndex] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!target.trim()) return;
    onLaunch(target.trim(), pineconeIndex.trim());
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-falcon-surface border border-falcon-border rounded-lg p-4"
    >
      <label className="block text-sm text-falcon-muted mb-1">Target</label>
      <input
        type="text"
        value={target}
        onChange={(e) => setTarget(e.target.value)}
        placeholder="e.g. acme-corp.com or John Doe"
        disabled={disabled}
        className="w-full bg-falcon-bg border border-falcon-border rounded px-3 py-2 text-sm
                   text-gray-100 placeholder-falcon-muted focus:outline-none focus:border-falcon-accent
                   disabled:opacity-50 mb-3"
      />

      <label className="block text-sm text-falcon-muted mb-1">
        Pinecone Index <span className="text-falcon-muted/60">(optional)</span>
      </label>
      <input
        type="text"
        value={pineconeIndex}
        onChange={(e) => setPineconeIndex(e.target.value)}
        placeholder="falconeye"
        disabled={disabled}
        className="w-full bg-falcon-bg border border-falcon-border rounded px-3 py-2 text-sm
                   text-gray-100 placeholder-falcon-muted focus:outline-none focus:border-falcon-accent
                   disabled:opacity-50 mb-4"
      />

      <button
        type="submit"
        disabled={disabled || !target.trim()}
        className="w-full bg-falcon-accent/20 border border-falcon-accent text-falcon-accent
                   rounded px-4 py-2 text-sm font-semibold hover:bg-falcon-accent/30
                   transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {disabled ? "⏳ Running…" : "🚀 Launch Crew"}
      </button>
    </motion.form>
  );
}
