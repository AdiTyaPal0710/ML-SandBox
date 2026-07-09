import { useState, useEffect, useRef } from "react";
import { Play, Terminal, Code2, Activity, CheckCircle2, XCircle, FileBox, RotateCcw, Sparkles, Upload } from 'lucide-react';

function App() {
  const [code, setCode] = useState("");
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('idle');
  const [requirements, setRequirements] = useState("");
  const [requirementsUploaded, setRequirementsUploaded] = useState(false);
  const [datasetUploaded, setDatasetUploaded] = useState(false);
  const [baseGoal, setBaseGoal] = useState("");
  const [datasetFilename, setDatasetFilename] = useState(null);
  const fullGoal = datasetFilename
    ? `${baseGoal}\n\nUse the dataset at /data/${datasetFilename}`
    : baseGoal;

  const ws = useRef(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const triggerAgent = () => {
    if (!baseGoal.trim()) {
      alert("Please enter an objective for the agent.");
      return;
    }
    if (!code.trim()) {
      alert("Please provide some baseline code or upload a Python script.");
      return;
    }

    ws.current?.close();
    setLogs([]);
    setStatus('running');

    ws.current = new WebSocket("ws://localhost:8000/ws/agent");

    ws.current.onopen = () => {
      ws.current.send(JSON.stringify({ goal: fullGoal, code, requirements }));
    };

    ws.current.onmessage = (event) => {
      const payload = JSON.parse(event.data);

      if (payload.node === 'system' && payload.message.includes('finished')) {
        setStatus('success');
      } else if (payload.node === 'error') {
        setStatus('error');
      }

      if (payload.data?.current_code) {
        setCode(payload.data.current_code);
      }
      setLogs(prev => [...prev, payload]);
    };

    ws.current.onerror = () => {
      setLogs((prev) => [...prev, { node: 'error', message: 'WebSocket Connection Failed. Is the Python server running?' }]);
      setStatus('error');
    };
  };

  const handleReset = () => {
    ws.current?.close();
    setCode("");
    setBaseGoal("");
    setRequirements("");
    setRequirementsUploaded(false);
    setLogs([]);
    setStatus('idle');
    setDatasetUploaded(false);
    setDatasetFilename(null);
  };

  const handleCodeUpload = (e) => {
    const file = e.target.files[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      setCode(event.target.result);
    };
    reader.readAsText(file);
  };

  const handleRequirementsUpload = async (e) => {

    const file = e.target.files[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      setRequirements(event.target.result);
      setRequirementsUploaded(true);
    };
    reader.readAsText(file);
  }

  const handleDatasetUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Client-side size check (50MB)
    const MAX_SIZE = 50 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      alert(`File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Maximum is 50MB.`);
      e.target.value = "";
      return;
    }

    // Client-side extension check
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['csv', 'json'].includes(ext)) {
      alert(`File type '.${ext}' is not allowed. Only .csv and .json files are accepted.`);
      e.target.value = "";
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        alert(err.detail || "Upload rejected by server.");
        e.target.value = "";
        return;
      }

      const data = await response.json();
      setDatasetFilename(data.filename);
      setDatasetUploaded(true);
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload dataset. Is FastAPI running?");
    }
  };

  const getNodeColor = (node) => {
    const colors = {
      error: 'text-red-400',
      system: 'text-emerald-400',
      execute_code: 'text-amber-400',
      evaluate_code: 'text-violet-400',
      modify_code: 'text-sky-400',
      ingest_state: 'text-teal-400',
    };
    return colors[node] || 'text-blue-400';
  };

  const getNodeBadgeBg = (node) => {
    const colors = {
      error: 'bg-red-500/10 border-red-500/30',
      system: 'bg-emerald-500/10 border-emerald-500/30',
      execute_code: 'bg-amber-500/10 border-amber-500/30',
      evaluate_code: 'bg-violet-500/10 border-violet-500/30',
      modify_code: 'bg-sky-500/10 border-sky-500/30',
      ingest_state: 'bg-teal-500/10 border-teal-500/30',
    };
    return colors[node] || 'bg-blue-500/10 border-blue-500/30';
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-300 font-sans">
      {/* ================= LEFT PANEL: CODE EDITOR ================= */}
      <div className="w-1/2 flex flex-col border-r border-slate-800/50">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800/50 bg-gradient-to-r from-slate-900 to-slate-950">
          <div className="flex items-center gap-2.5 text-slate-100 font-semibold tracking-tight">
            <div className="p-1.5 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <Code2 size={18} className="text-blue-400" />
            </div>
            Agent Workspace
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 px-3 py-2 rounded-lg text-sm transition-all duration-200 border border-slate-700/50"
              title="Reset workspace"
            >
              <RotateCcw size={14} />
              Reset
            </button>
            <button
              onClick={triggerAgent}
              disabled={status === 'running'}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 text-white px-5 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg shadow-blue-500/20 disabled:shadow-none"
            >
              {status === 'running' ? <Activity size={16} className="animate-spin" /> : <Sparkles size={16} />}
              {status === 'running' ? 'Agent Running...' : 'Deploy Agent'}
            </button>
          </div>
        </div>

        {/* Inputs */}
        <div className="p-5 flex-1 flex flex-col gap-4 overflow-y-auto bg-slate-900/50">

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Agent Objective</label>
            <textarea
              value={baseGoal}
              onChange={(e) => setBaseGoal(e.target.value)}
              rows={3}
              className="w-full bg-slate-950/80 border border-slate-700/50 rounded-lg p-3 text-slate-200 text-sm leading-relaxed focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 resize-none placeholder-slate-600 transition-all duration-200"
              placeholder="Describe what you want the AI agent to achieve, e.g. 'Train a classifier on the uploaded dataset and achieve > 85% accuracy'"
            />
            {datasetFilename && (
              <div className="flex items-center gap-1.5 text-xs text-emerald-400/80 mt-0.5">
                <FileBox size={12} />
                <span>Dataset attached: <span className="font-medium text-emerald-300">{datasetFilename}</span></span>
              </div>
            )}
          </div>

          {/* File Upload Row */}
          <div className="flex gap-3">
            {/* Python Script Upload */}
            <div className="relative flex-1">
              <input
                type="file"
                accept=".py"
                onChange={handleCodeUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div className="flex items-center justify-center gap-2 bg-slate-800/50 hover:bg-slate-800 text-slate-400 p-3 rounded-lg border border-slate-700/40 border-dashed transition-all duration-200 pointer-events-none text-sm">
                <Upload size={16} />
                <span>Upload Script (.py)</span>
              </div>
            </div>

            {/* Dataset Upload */}
            <div className="relative flex-1">
              <input
                type="file"
                accept=".csv,.json"
                onChange={handleDatasetUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div className={`flex items-center justify-center gap-2 ${datasetUploaded
                ? 'bg-emerald-950/50 border-emerald-500/30 text-emerald-300'
                : 'bg-slate-800/50 hover:bg-slate-800 text-slate-400 border-slate-700/40 border-dashed'
                } p-3 rounded-lg border transition-all duration-200 pointer-events-none text-sm`}>
                {datasetUploaded ? <CheckCircle2 size={16} /> : <FileBox size={16} />}
                <span>{datasetUploaded ? 'Dataset Ready!' : 'Upload Dataset'}</span>
              </div>
            </div>

            {/* Requirements Upload */}
            <div className="relative flex-1">
              <input
                type="file"
                accept=".txt"
                onChange={handleRequirementsUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
              <div className={`flex items-center justify-center gap-2 ${requirementsUploaded
                ? 'bg-emerald-950/50 border-emerald-500/30 text-emerald-300'
                : 'bg-slate-800/50 hover:bg-slate-800 text-slate-400 border-slate-700/40 border-dashed'
                } p-3 rounded-lg border transition-all duration-200 pointer-events-none text-sm`}>
                {requirementsUploaded ? <CheckCircle2 size={16} /> : <FileBox size={16} />}
                <span>{requirementsUploaded ? 'Requirements Ready!' : 'Upload Requirements'}</span>
              </div>
            </div>


          </div>

          <div className="flex flex-col gap-1.5 flex-1">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Baseline Code</label>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full flex-1 bg-slate-950/80 border border-slate-700/50 rounded-lg p-4 text-slate-200 font-mono text-sm leading-relaxed focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 resize-none placeholder-slate-600 transition-all duration-200"
              placeholder={"# Paste or type your Python code here\n# Or upload a .py file using the button above\n\nimport pandas as pd\n\n# Your ML pipeline code..."}
            />
          </div>

        </div>
      </div>

      {/* ================= RIGHT PANEL: TERMINAL & LOGS ================= */}
      <div className="w-1/2 flex flex-col bg-slate-950">

        {/* Header */}
        <div className="flex items-center gap-2.5 p-4 border-b border-slate-800/50 bg-gradient-to-r from-slate-950 to-slate-900">
          <div className="p-1.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
            <Terminal size={18} className="text-emerald-400" />
          </div>
          <span className="text-slate-100 font-semibold tracking-tight">Live Telemetry</span>

          {/* Status Indicator */}
          <div className="ml-auto flex items-center gap-2 text-sm">
            {status === 'idle' && <span className="text-slate-600 text-xs">Idle</span>}
            {status === 'running' && (
              <span className="text-blue-400 flex items-center gap-1.5 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20 text-xs font-medium">
                <Activity size={12} className="animate-spin" /> Processing
              </span>
            )}
            {status === 'success' && (
              <span className="text-emerald-400 flex items-center gap-1.5 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 text-xs font-medium">
                <CheckCircle2 size={12} /> Completed
              </span>
            )}
            {status === 'error' && (
              <span className="text-red-400 flex items-center gap-1.5 bg-red-500/10 px-3 py-1 rounded-full border border-red-500/20 text-xs font-medium">
                <XCircle size={12} /> Error
              </span>
            )}
          </div>
        </div>

        {/* Terminal Output */}
        <div className="flex-1 p-5 overflow-y-auto font-mono text-sm">
          {logs.length === 0 ? (
            <div className="text-slate-700 flex flex-col items-center justify-center h-full gap-3 select-none">
              <Terminal size={40} className="text-slate-800" />
              <span className="text-sm">Waiting for agent deployment...</span>
              <span className="text-xs text-slate-800">Set an objective and deploy the agent to begin</span>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {logs.map((log, index) => (
                <div key={index} className="flex flex-col gap-1.5 border-b border-slate-800/40 pb-3">
                  <span className={`inline-flex items-center gap-1 w-fit px-2 py-0.5 rounded-md border text-[10px] font-semibold uppercase tracking-widest ${getNodeColor(log.node)} ${getNodeBadgeBg(log.node)}`}>
                    {log.node}
                  </span>

                  {/* If the data is a complex object (like from LangGraph), format it nicely */}
                  {typeof log.data === 'object' ? (
                    log.node === 'modify_code' && log.data.current_code ? (
                      <div className="flex flex-col gap-2 pl-3 border-l-2 border-sky-500/20 mt-1">
                        <span className="text-xs text-slate-500">Iteration {log.data.iteration_count} — Rewritten Code:</span>
                        <pre className="whitespace-pre-wrap text-emerald-300/90 bg-slate-900/80 p-3 rounded-lg text-xs border border-slate-800/50 leading-relaxed overflow-x-auto">
                          {log.data.current_code}
                        </pre>
                      </div>
                    ) : log.node === 'execute_code' ? (
                      <div className="flex flex-col gap-1 pl-3 border-l-2 border-amber-500/20 mt-1">
                        {log.data.exit_code !== undefined && (
                          <span className={`text-xs font-medium ${log.data.exit_code === 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            Exit Code: {log.data.exit_code}
                          </span>
                        )}
                        {log.data.execution_logs && (
                          <pre className="whitespace-pre-wrap text-slate-400 bg-slate-900/60 p-3 rounded-lg text-xs border border-slate-800/50 mt-1 leading-relaxed overflow-x-auto">
                            {typeof log.data.execution_logs === 'string' ? log.data.execution_logs : JSON.stringify(log.data.execution_logs, null, 2)}
                          </pre>
                        )}
                      </div>
                    ) : log.node === 'evaluate_code' ? (
                      <div className="flex flex-col gap-1 pl-3 border-l-2 border-violet-500/20 mt-1">
                        {log.data.status && (
                          <span className={`text-xs font-semibold ${log.data.status === 'success' ? 'text-emerald-400' : log.data.status === 'needs_debugging' ? 'text-red-400' : 'text-amber-400'}`}>
                            Verdict: {log.data.status.replace(/_/g, ' ')}
                          </span>
                        )}
                      </div>
                    ) : (
                      <pre className="whitespace-pre-wrap text-slate-500 pl-3 border-l-2 border-slate-700/30 mt-1 text-xs leading-relaxed">
                        {JSON.stringify(log.data, null, 2)}
                      </pre>
                    )
                  ) : (
                    <span className="text-slate-400 text-xs pl-3">{log.message || JSON.stringify(log.data)}</span>
                  )}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;