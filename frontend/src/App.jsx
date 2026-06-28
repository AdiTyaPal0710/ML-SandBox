import { useState, useEffect, useRef } from "react";
import { Play, Terminal, Code2, Activity, CheckCircle2, XCircle } from 'lucide-react';

function App() {

  const [goal, setGoal] = useState("Calculate the square root of 144 without crashing.");
  const [code, setCode] = useState("import math\n\nprint('Starting calculation...')\nresult = 10 / 0  # Bug!\nprint('Done.')");
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('idle');

  const ws = useRef(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);


  const triggerAgent = () => {

    setLogs([]);
    setStatus('running')

    ws.current = new WebSocket("ws://localhost:8000/ws/agent");


    ws.current.onopen = () => {

      //Send payload
      ws.current.send(JSON.stringify({ goal, code }));
    }

    ws.current.onmessage = (event) => {

      const payload = JSON.parse(event.data);

      if (payload.node === 'system' && payload.message.includes('finished')) {
        setStatus('success');
      } else if (payload.node === 'error') {
        setStatus('error');
      }

      setLogs(prev => [...prev, payload]);
    }

    ws.current.onerror = (error) => {
      setLogs((prev) => [...prev, { node: 'error', message: 'WebSocket Connection Failed. Is the Python server running?' }]);
      setStatus('error');
    };
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-300 font-sans">

      {/* ================= LEFT PANEL: CODE EDITOR ================= */}
      <div className="w-1/2 flex flex-col border-r border-slate-800 bg-slate-900">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-950">
          <div className="flex items-center gap-2 text-slate-100 font-semibold">
            <Code2 size={20} className="text-blue-500" />
            Agent Workspace
          </div>
          <button
            onClick={triggerAgent}
            disabled={status === 'running'}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
          >
            {status === 'running' ? <Activity size={18} className="animate-spin" /> : <Play size={18} />}
            {status === 'running' ? 'Agent Running...' : 'Deploy Agent'}
          </button>
        </div>

        {/* Inputs */}
        <div className="p-6 flex-1 flex flex-col gap-4 overflow-y-auto">

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-400">Agent Objective (Goal)</label>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded p-3 text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex flex-col gap-2 flex-1">
            <label className="text-sm font-semibold text-slate-400">Starting Python Sandbox Code</label>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full flex-1 bg-slate-950 border border-slate-700 rounded p-4 text-slate-200 font-mono text-sm focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>

        </div>
      </div>

      {/* ================= RIGHT PANEL: TERMINAL & LOGS ================= */}
      <div className="w-1/2 flex flex-col bg-slate-950">

        {/* Header */}
        <div className="flex items-center gap-2 p-4 border-b border-slate-800 text-slate-100 font-semibold">
          <Terminal size={20} className="text-emerald-500" />
          Live Telemetry & Logs

          {/* Status Indicator */}
          <div className="ml-auto flex items-center gap-2 text-sm">
            {status === 'running' && <span className="text-blue-400 flex items-center gap-1"><Activity size={14} className="animate-spin" /> Active</span>}
            {status === 'success' && <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 size={14} /> Completed</span>}
            {status === 'error' && <span className="text-red-400 flex items-center gap-1"><XCircle size={14} /> Error</span>}
          </div>
        </div>

        {/* Terminal Output */}
        <div className="flex-1 p-6 overflow-y-auto font-mono text-sm">
          {logs.length === 0 ? (
            <div className="text-slate-600 flex items-center justify-center h-full">
              Waiting for agent deployment...
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {logs.map((log, index) => (
                <div key={index} className="flex flex-col gap-1 border-b border-slate-800 pb-3">
                  <span className={`font-bold uppercase tracking-wider text-xs ${log.node === 'error' ? 'text-red-500' :
                    log.node === 'system' ? 'text-emerald-500' : 'text-blue-400'
                    }`}>
                    [{log.node}]
                  </span>

                  {/* If the data is a complex object (like from LangGraph), format it nicely */}
                  {typeof log.data === 'object' ? (
                    <pre className="whitespace-pre-wrap text-slate-400 pl-2 border-l-2 border-slate-700">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  ) : (
                    <span className="text-slate-300">{log.message || JSON.stringify(log.data)}</span>
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