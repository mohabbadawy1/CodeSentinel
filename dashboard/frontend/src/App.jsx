import { useState, useEffect, useRef } from "react";

const API = "http://localhost:8000";

export default function App() {
  const [logs, setLogs] = useState([]);
  const [repoUrl, setRepoUrl] = useState("");
  const [running, setRunning] = useState(false);
  const [prUrl, setPrUrl] = useState(null);
  const wsRef = useRef(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    connectWS();
    return () => wsRef.current?.close();
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  function connectWS() {
    wsRef.current = new WebSocket(`ws://localhost:8000/ws`);
    wsRef.current.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "log") {
        setLogs((prev) => [...prev, data.message]);
        if (data.message.includes("PR:") && data.message.includes("http")) {
          const url = data.message.match(/https:\/\/github\.com\/[^\s]+/)?.[0];
          if (url) setPrUrl(url);
        }
        if (data.message.includes("[DONE]")) setRunning(false);
      }
    };
    wsRef.current.onclose = () => setTimeout(connectWS, 2000);
  }

  async function startPipeline() {
    if (!repoUrl.trim()) return;
    setRunning(true);
    setLogs([]);
    setPrUrl(null);
    await fetch(`${API}/run?repo_url=${encodeURIComponent(repoUrl)}`, { method: "POST" });
  }

  function getLogColor(log) {
    if (log.includes("ERROR") || log.includes("REJECTED")) return "#e8251a";
    if (log.includes("APPROVED") || log.includes("PASSED") || log.includes("Done")) return "#2ecc71";
    if (log.includes("[STEP")) return "#f59e0b";
    if (log.includes("[PIPELINE]") || log.includes("[DONE]")) return "#3b82f6";
    return "#cccccc";
  }

  return (
    <div style={{ background: "#0a0a0a", minHeight: "100vh", padding: "32px 40px", fontFamily: "monospace" }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 36, margin: 0, color: "#fff" }}>
          Code<span style={{ color: "#e8251a" }}>Sentinel</span>
        </h1>
        <p style={{ color: "#666", margin: "6px 0 0", fontSize: 13 }}>
          Autonomous Code Enhancement Pipeline — GDG EUI x Duckurity 2026
        </p>
      </div>

      {/* Input */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <input
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !running && startPipeline()}
          placeholder="https://github.com/owner/repository"
          style={{
            flex: 1, padding: "10px 16px",
            background: "#1a1a1a", border: "1px solid #333",
            color: "#fff", borderRadius: 4, fontSize: 14,
            outline: "none"
          }}
        />
        <button
          onClick={startPipeline}
          disabled={running || !repoUrl.trim()}
          style={{
            padding: "10px 28px",
            background: running ? "#444" : "#e8251a",
            color: "#fff", border: "none", borderRadius: 4,
            fontSize: 14, cursor: running ? "not-allowed" : "pointer",
            fontFamily: "monospace", fontWeight: "bold"
          }}
        >
          {running ? "Running..." : "Run Pipeline"}
        </button>
      </div>

      {/* Status bar */}
      <div style={{ display: "flex", gap: 24, marginBottom: 16 }}>
        <div style={{ fontSize: 12, color: "#555" }}>
          Status:{" "}
          <span style={{ color: running ? "#f59e0b" : "#2ecc71" }}>
            {running ? "● RUNNING" : "● IDLE"}
          </span>
        </div>
        {prUrl && (
          <div style={{ fontSize: 12 }}>
            Pull Request:{" "}
            <a href={prUrl} target="_blank" rel="noreferrer" style={{ color: "#3b82f6" }}>
              {prUrl}
            </a>
          </div>
        )}
      </div>

      {/* Agent pipeline visual */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {["Researcher", "Coder", "QA Tester", "PR Agent"].map((agent, i) => {
          const hasLog = logs.some((l) => l.toLowerCase().includes(agent.toLowerCase().split(" ")[0]));
          return (
            <div key={i} style={{
              padding: "6px 16px",
              background: hasLog ? "#1a1a1a" : "#111",
              border: `1px solid ${hasLog ? "#e8251a" : "#222"}`,
              borderRadius: 4, fontSize: 11,
              color: hasLog ? "#fff" : "#444"
            }}>
              {agent}
            </div>
          );
        })}
      </div>

      {/* Log window */}
      <div style={{
        background: "#111", border: "1px solid #222",
        borderRadius: 6, padding: "20px 24px",
        height: 380, overflowY: "auto"
      }}>
        {logs.length === 0 && (
          <span style={{ color: "#333", fontSize: 13 }}>
            Paste a GitHub repository URL above and click Run Pipeline...
          </span>
        )}
        {logs.map((log, i) => (
          <div key={i} style={{
            color: getLogColor(log),
            fontSize: 12, lineHeight: "1.7",
            borderBottom: "1px solid #161616",
            paddingBottom: 2, marginBottom: 2
          }}>
            {log}
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>

      <div style={{ marginTop: 12, fontSize: 11, color: "#333" }}>
        {logs.length} log entries
      </div>
    </div>
  );
}
