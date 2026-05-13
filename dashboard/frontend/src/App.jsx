import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000";

const STEPS = [
  { id: 1, label: "Clone", key: "STEP 1" },
  { id: 2, label: "Research", key: "STEP 2" },
  { id: 3, label: "Patch", key: "STEP 3" },
  { id: 4, label: "QA", key: "STEP 4" },
  { id: 5, label: "PR", key: "STEP 5" },
];

function classifyLog(msg) {
  const m = msg.toUpperCase();
  if (m.includes("ERROR") || m.includes("REJECTED") || m.includes("FAILED"))
    return "error";
  if (m.includes("APPROVED") || m.includes("DONE") || m.includes("✓") || m.includes("CREATED"))
    return "success";
  if (m.includes("STEP 1") || m.includes("STEP 2") || m.includes("STEP 3") || m.includes("STEP 4") || m.includes("STEP 5"))
    return "step";
  if (m.includes("WARNING") || m.includes("RETRY") || m.includes("ATTEMPT"))
    return "warn";
  if (m.includes("RESEARCHER") || m.includes("CODER") || m.includes("QA TESTER") || m.includes("AGENT"))
    return "agent";
  return "info";
}

function getActiveStep(logs) {
  let active = 0;
  for (const log of logs) {
    const m = log.toUpperCase();
    for (const step of STEPS) {
      if (m.includes(step.key)) active = step.id;
    }
  }
  return active;
}

const LOG_COLORS = {
  error: "#ff4444",
  success: "#00ff88",
  step: "#e8251a",
  warn: "#ffaa00",
  agent: "#a78bfa",
  info: "#9ca3af",
};

const LOG_PREFIXES = {
  error: "✗",
  success: "✓",
  step: "▶",
  warn: "⚠",
  agent: "◆",
  info: "·",
};

export default function App() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/mohabbadawy1/click");
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState({ running: false, pr_url: null });
  const [connected, setConnected] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [scanlines, setScanlines] = useState(true);
  const logsEndRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    setActiveStep(getActiveStep(logs));
  }, [logs]);

  function connect() {
    const ws = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      setTimeout(connect, 3000);
    };
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "log") {
        setLogs((prev) => [...prev, data.message]);
      }
    };
  }

  const runPipeline = async () => {
    if (status.running) return;
    setLogs([]);
    setActiveStep(0);
    try {
      await axios.post(`${API_URL}/run?repo_url=${encodeURIComponent(repoUrl)}`);
      const interval = setInterval(async () => {
        const res = await axios.get(`${API_URL}/status`);
        setStatus(res.data);
        if (!res.data.running) clearInterval(interval);
      }, 1000);
    } catch (e) {
      setLogs((prev) => [...prev, `[ERROR] Could not connect to API: ${e.message}`]);
    }
  };

  const totalFindings = logs.some(l => l.includes("findings")) 
    ? logs.find(l => l.match(/\d+ findings/))?.match(/(\d+) findings/)?.[1] 
    : null;

  return (
    <div style={{
      background: "#080808",
      minHeight: "100vh",
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
      color: "#c9d1d9",
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Scanline overlay */}
      {scanlines && (
        <div style={{
          position: "fixed", inset: 0, pointerEvents: "none", zIndex: 100,
          backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
        }} />
      )}

      {/* Red grid background */}
      <div style={{
        position: "fixed", inset: 0, pointerEvents: "none",
        backgroundImage: `
          linear-gradient(rgba(232,37,26,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(232,37,26,0.03) 1px, transparent 1px)
        `,
        backgroundSize: "40px 40px",
      }} />

      {/* Top bar */}
      <div style={{
        borderBottom: "1px solid #1a1a1a",
        padding: "0 32px",
        height: "52px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(10,10,10,0.95)",
        position: "sticky", top: 0, zIndex: 50,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ display: "flex", gap: "6px" }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff5f57" }} />
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#ffbd2e" }} />
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#28c840" }} />
          </div>
          <span style={{ color: "#333", fontSize: "11px", letterSpacing: "0.1em" }}>CODESENTINEL v1.0 — AGENTIC CODE ENHANCER</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "20px", fontSize: "11px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%",
              background: connected ? "#00ff88" : "#ff4444",
              boxShadow: connected ? "0 0 6px #00ff88" : "0 0 6px #ff4444",
              animation: connected ? "pulse 2s infinite" : "none",
            }} />
            <span style={{ color: connected ? "#00ff88" : "#ff4444" }}>
              {connected ? "CONNECTED" : "DISCONNECTED"}
            </span>
          </div>
          <span style={{ color: "#333" }}>GDG EUI × DUCKURITY</span>
        </div>
      </div>

      <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "32px 32px" }}>

        {/* Header */}
        <div style={{ marginBottom: "36px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: "2px", marginBottom: "4px" }}>
            <h1 style={{
              margin: 0,
              fontSize: "36px",
              fontWeight: 800,
              letterSpacing: "-0.02em",
              color: "#e8251a",
            }}>Code</h1>
            <h1 style={{
              margin: 0,
              fontSize: "36px",
              fontWeight: 800,
              letterSpacing: "-0.02em",
              color: "#ffffff",
            }}>Sentinel</h1>
          </div>
          <p style={{ margin: 0, color: "#444", fontSize: "12px", letterSpacing: "0.15em" }}>
            AUTONOMOUS MULTI-AGENT SECURITY PIPELINE — CHALLENGE 4
          </p>
        </div>

        {/* Step progress */}
        <div style={{
          display: "flex",
          alignItems: "center",
          marginBottom: "28px",
          background: "#0d0d0d",
          border: "1px solid #1a1a1a",
          borderRadius: "4px",
          padding: "16px 24px",
          gap: "0",
        }}>
          {STEPS.map((step, i) => {
            const done = activeStep > step.id;
            const active = activeStep === step.id;
            return (
              <div key={step.id} style={{ display: "flex", alignItems: "center", flex: 1 }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
                  <div style={{
                    width: 32, height: 32,
                    borderRadius: "50%",
                    border: `2px solid ${done ? "#00ff88" : active ? "#e8251a" : "#222"}`,
                    background: done ? "#00ff8820" : active ? "#e8251a20" : "transparent",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "12px", fontWeight: 700,
                    color: done ? "#00ff88" : active ? "#e8251a" : "#333",
                    boxShadow: active ? "0 0 12px #e8251a66" : done ? "0 0 8px #00ff8844" : "none",
                    transition: "all 0.3s",
                  }}>
                    {done ? "✓" : step.id}
                  </div>
                  <span style={{
                    fontSize: "10px",
                    letterSpacing: "0.1em",
                    color: done ? "#00ff88" : active ? "#e8251a" : "#333",
                    fontWeight: active ? 700 : 400,
                  }}>{step.label.toUpperCase()}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div style={{
                    flex: 1,
                    height: "1px",
                    background: done ? "#00ff8844" : "#1a1a1a",
                    margin: "0 8px",
                    marginBottom: "20px",
                    transition: "background 0.3s",
                  }} />
                )}
              </div>
            );
          })}
        </div>

        {/* Input row */}
        <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
          <div style={{ flex: 1, position: "relative" }}>
            <span style={{
              position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)",
              color: "#e8251a", fontSize: "12px", fontWeight: 700,
            }}>$</span>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              style={{
                width: "100%",
                padding: "12px 14px 12px 28px",
                background: "#0d0d0d",
                color: "#c9d1d9",
                border: "1px solid #222",
                borderRadius: "4px",
                fontSize: "13px",
                fontFamily: "inherit",
                outline: "none",
                boxSizing: "border-box",
                transition: "border-color 0.2s",
              }}
              onFocus={e => e.target.style.borderColor = "#e8251a"}
              onBlur={e => e.target.style.borderColor = "#222"}
            />
          </div>
          <button
            onClick={runPipeline}
            disabled={status.running || !connected}
            style={{
              padding: "12px 28px",
              background: status.running ? "#1a0a0a" : "#e8251a",
              color: status.running ? "#e8251a" : "#fff",
              border: `1px solid ${status.running ? "#e8251a44" : "#e8251a"}`,
              borderRadius: "4px",
              fontSize: "12px",
              fontFamily: "inherit",
              fontWeight: 700,
              letterSpacing: "0.1em",
              cursor: status.running ? "not-allowed" : "pointer",
              whiteSpace: "nowrap",
              transition: "all 0.2s",
              boxShadow: status.running ? "none" : "0 0 20px #e8251a44",
            }}
          >
            {status.running ? (
              <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>⟳</span>
                RUNNING...
              </span>
            ) : "▶ RUN PIPELINE"}
          </button>
          {logs.length > 0 && (
            <button
              onClick={() => { setLogs([]); setActiveStep(0); setStatus({ running: false, pr_url: null }); }}
              style={{
                padding: "12px 16px",
                background: "transparent",
                color: "#444",
                border: "1px solid #1a1a1a",
                borderRadius: "4px",
                fontSize: "12px",
                fontFamily: "inherit",
                cursor: "pointer",
                letterSpacing: "0.1em",
              }}
            >CLEAR</button>
          )}
        </div>

        {/* Stats bar — shows when pipeline has run */}
        {logs.length > 0 && (
          <div style={{
            display: "flex", gap: "1px", marginBottom: "12px",
          }}>
            {[
              { label: "LOGS", value: logs.length },
              { label: "ERRORS", value: logs.filter(l => classifyLog(l) === "error").length, color: "#ff4444" },
              { label: "WARNINGS", value: logs.filter(l => classifyLog(l) === "warn").length, color: "#ffaa00" },
              { label: "STATUS", value: status.running ? "RUNNING" : activeStep === 5 ? "COMPLETE" : activeStep > 0 ? `STEP ${activeStep}/5` : "IDLE", color: status.running ? "#e8251a" : "#00ff88" },
            ].map((stat, i) => (
              <div key={i} style={{
                flex: 1,
                background: "#0d0d0d",
                border: "1px solid #1a1a1a",
                padding: "8px 16px",
                borderRadius: i === 0 ? "4px 0 0 4px" : i === 3 ? "0 4px 4px 0" : "0",
              }}>
                <div style={{ fontSize: "10px", color: "#333", letterSpacing: "0.1em", marginBottom: "2px" }}>{stat.label}</div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: stat.color || "#c9d1d9" }}>{stat.value}</div>
              </div>
            ))}
          </div>
        )}

        {/* PR success banner */}
        {status.pr_url && (
          <div style={{
            background: "#001a0d",
            border: "1px solid #00ff8844",
            borderRadius: "4px",
            padding: "16px 20px",
            marginBottom: "16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            boxShadow: "0 0 24px #00ff8820",
          }}>
            <div>
              <div style={{ color: "#00ff88", fontSize: "11px", letterSpacing: "0.15em", marginBottom: "4px", fontWeight: 700 }}>
                ✓ PULL REQUEST CREATED AUTONOMOUSLY
              </div>
              <a href={status.pr_url} target="_blank" rel="noreferrer" style={{
                color: "#58a6ff", fontSize: "13px", textDecoration: "none",
              }}>{status.pr_url}</a>
            </div>
            <a href={status.pr_url} target="_blank" rel="noreferrer" style={{
              padding: "8px 16px",
              background: "#00ff8820",
              color: "#00ff88",
              border: "1px solid #00ff8844",
              borderRadius: "4px",
              fontSize: "11px",
              fontWeight: 700,
              textDecoration: "none",
              letterSpacing: "0.1em",
            }}>VIEW PR →</a>
          </div>
        )}

        {/* Terminal log window */}
        <div style={{
          background: "#0a0a0a",
          border: "1px solid #1a1a1a",
          borderRadius: "4px",
          overflow: "hidden",
        }}>
          {/* Terminal header */}
          <div style={{
            background: "#0d0d0d",
            borderBottom: "1px solid #1a1a1a",
            padding: "10px 16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <span style={{ fontSize: "11px", color: "#333", letterSpacing: "0.1em" }}>AGENT OUTPUT — LIVE STREAM</span>
            <span style={{ fontSize: "11px", color: "#222" }}>{new Date().toLocaleTimeString()}</span>
          </div>

          {/* Log body */}
          <div style={{
            height: "480px",
            overflowY: "auto",
            padding: "16px",
            scrollbarWidth: "thin",
            scrollbarColor: "#1a1a1a #080808",
          }}>
            {logs.length === 0 ? (
              <div style={{ color: "#222", fontSize: "12px", paddingTop: "8px" }}>
                <span style={{ color: "#e8251a" }}>$</span> awaiting pipeline execution...<span style={{ animation: "blink 1s step-end infinite" }}>_</span>
              </div>
            ) : (
              logs.map((log, i) => {
                const type = classifyLog(log);
                const color = LOG_COLORS[type];
                const prefix = LOG_PREFIXES[type];
                const isStep = type === "step";
                return (
                  <div key={i} style={{
                    display: "flex",
                    gap: "10px",
                    marginBottom: isStep ? "8px" : "2px",
                    marginTop: isStep ? "12px" : "0",
                    padding: isStep ? "6px 8px" : "1px 0",
                    background: isStep ? "#0f0707" : "transparent",
                    borderLeft: isStep ? "2px solid #e8251a" : "none",
                    paddingLeft: isStep ? "10px" : "0",
                    borderRadius: isStep ? "0 2px 2px 0" : "0",
                  }}>
                    <span style={{ color, flexShrink: 0, fontSize: "11px", marginTop: "1px" }}>{prefix}</span>
                    <span style={{
                      color: type === "info" ? "#555" : color,
                      fontSize: "12px",
                      lineHeight: "1.6",
                      fontWeight: isStep ? 700 : 400,
                      wordBreak: "break-all",
                    }}>{log}</span>
                  </div>
                );
              })
            )}
            <div ref={logsEndRef} />
          </div>
        </div>

        {/* Footer */}
        <div style={{
          marginTop: "20px",
          display: "flex",
          justifyContent: "space-between",
          fontSize: "10px",
          color: "#222",
          letterSpacing: "0.1em",
        }}>
          <span>CODESENTINEL — GDG EUI × DUCKURITY HACKATHON 2026</span>
          <span>CHALLENGE 4: AGENTIC CODE ENHANCER</span>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #080808; }
        ::-webkit-scrollbar-thumb { background: #1a1a1a; border-radius: 2px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        input::placeholder { color: #333; }
      `}</style>
    </div>
  );
}