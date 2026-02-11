import { useState, useRef, useCallback, useEffect } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import Graph2D from "./components/Graph2D";
import { useNavigate } from "react-router-dom";
import "./App.css"; // We keep this for fonts mostly, but override styles with Tailwind

export default function Dashboard() {
  const { graphData, logs, connected } = useWebSocket("ws://localhost:8000/ws");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [showGraph, setShowGraph] = useState(false);
  const logEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  // Auto-scroll activity log
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollTop = logEndRef.current.scrollHeight;
    }
  }, [logs]);

  // Drag-and-drop handlers
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;
    await uploadFiles(files);
  }, []);

  const handleFileSelect = useCallback(async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    await uploadFiles(files);
    e.target.value = "";
  }, []);

  const uploadFiles = async (files) => {
    setUploadStatus(`Uploading ${files.length} file(s)...`);
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setUploadStatus(`✅ Uploaded ${data.count} file(s)`);
      setTimeout(() => setUploadStatus(null), 3000);
    } catch (err) {
      setUploadStatus("❌ Upload failed");
      setTimeout(() => setUploadStatus(null), 3000);
    }
  };

  // Helper for stats
  const totalWords = graphData.nodes
    .reduce((sum, n) => sum + (n.word_count || 0), 0);

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  };

  return (
    <div
      className="min-h-screen bg-white text-primary font-display antialiased flex flex-col"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag Overlay */}
      {isDragging && (
        <div className="fixed inset-0 z-[100] bg-white/95 backdrop-blur-md flex flex-col items-center justify-center border-4 border-primary m-4">
          <span className="material-symbols-outlined text-9xl text-primary animate-bounce">
            upload_file
          </span>
          <h2 className="mt-8 text-4xl font-black uppercase tracking-tighter">
            Drop Files to Analyze
          </h2>
          <p className="mt-4 text-lg font-medium opacity-60">
            .pdf and .txt files supported
          </p>
        </div>
      )}

      {/* Graph Overlay */}
      {showGraph && (
        <div className="fixed inset-0 z-[60] bg-white/95 backdrop-blur-md flex flex-col p-6 animate-in fade-in duration-200">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-4">
              <span className="material-symbols-outlined text-4xl">hub</span>
              <h2 className="text-4xl font-black uppercase tracking-tighter">
                System Node Map
              </h2>
            </div>
            <button 
              onClick={() => setShowGraph(false)}
              className="bg-primary hover:bg-white text-white hover:text-primary border-2 border-primary px-6 py-3 font-black uppercase tracking-wider transition-all"
            >
              Close Visualization
            </button>
          </div>
          <div className="flex-1 border-2 border-primary relative bg-white shadow-[8px_8px_0px_0px_rgba(20,20,20,1)]">
            <Graph2D graphState={{ files: graphData.files || graphData.nodes, clusters: graphData.clusters_map || {} }} />
            <div className="absolute bottom-6 left-6 bg-white border-2 border-primary p-4 shadow-md max-w-sm">
              <h4 className="font-bold uppercase text-xs mb-2 opacity-50">Graph Controls</h4>
              <p className="text-xs font-medium">
                • Scroll to Zoom<br/>
                • Drag to Pan<br/>
                • Click Clusters to Focus<br/>
                • Click Nodes to Open File
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b-2 border-primary bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-[1920px] items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/')}>
            <div className="bg-primary text-white p-2 group-hover:scale-110 transition-transform">
               <span className="material-symbols-outlined text-2xl font-bold block">folder_managed</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-black uppercase tracking-tighter leading-none">AuraFS</span>
              <span className="text-[10px] font-bold uppercase tracking-widest opacity-50 leading-none mt-0.5">Semantic Organization Engine</span>
            </div>
          </div>

          <div className="flex items-center gap-6">
             {/* 2D Vis Button */}
            <button 
              onClick={() => setShowGraph(true)}
              className="hidden md:flex items-center gap-2 px-5 py-2.5 bg-white text-primary border-2 border-primary text-xs font-black uppercase tracking-widest hover:bg-primary hover:text-white transition-all shadow-[4px_4px_0px_0px_rgba(20,20,20,1)] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]"
            >
              <span className="material-symbols-outlined text-lg">hub</span>
              Cluster Visualization
            </button>

            <div className="h-8 w-[2px] bg-primary/10"></div>

            <div className={`flex items-center gap-2 px-3 py-1.5 border-2 ${connected ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}>
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-600 animate-pulse' : 'bg-red-600'}`}></div>
              <span className={`text-[10px] font-bold uppercase tracking-wider ${connected ? 'text-green-800' : 'text-red-800'}`}>
                {connected ? 'System Online' : 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-[1920px] mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Stats & Pipeline */}
        <div className="lg:col-span-8 flex flex-col gap-8">
            
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-primary p-6 hover:bg-primary hover:text-white transition-all cursor-pointer group relative overflow-hidden"
                >
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                         <span className="material-symbols-outlined text-8xl">upload_file</span>
                    </div>
                    <div className="relative z-10">
                        <div className="text-xs font-bold uppercase tracking-widest opacity-60 mb-2 group-hover:text-white/70">Files Tracked</div>
                        <div className="text-5xl font-black tracking-tighter mb-4">{graphData.nodes.length}</div>
                        <div className="flex items-center gap-2 text-xs font-bold uppercase border-t-2 border-primary/10 pt-4 mt-2 group-hover:border-white/20">
                            <span className="material-symbols-outlined text-sm">add</span>
                            Add Files to Organize
                        </div>
                    </div>
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        multiple
                        accept=".pdf,.txt"
                        className="hidden"
                    />
                </div>

                <div className="border-2 border-primary p-6 hover:bg-slate-50 transition-colors">
                    <div className="text-xs font-bold uppercase tracking-widest opacity-60 mb-2">Semantic Clusters</div>
                    <div className="text-5xl font-black tracking-tighter mb-4">{graphData.clusters.length}</div>
                    <div className="w-full bg-gray-100 h-2 mt-4 relative">
                        <div className="absolute left-0 top-0 h-full bg-primary" style={{width: `${Math.min(100, graphData.clusters.length * 10)}%`}}></div>
                    </div>
                </div>

                <div className="border-2 border-primary p-6 hover:bg-slate-50 transition-colors">
                    <div className="text-xs font-bold uppercase tracking-widest opacity-60 mb-2">Total Words</div>
                    <div className="text-5xl font-black tracking-tighter mb-4">{formatNumber(totalWords)}</div>
                    <div className="text-[10px] font-mono opacity-50 mt-4 text-right">
                        AVG: {graphData.nodes.length > 0 ? (totalWords / graphData.nodes.length).toFixed(0) : 0} / FILE
                    </div>
                </div>
            </div>

            {/* Pipeline Visualization */}
            <div className="border-2 border-primary bg-slate-50 p-8 overflow-hidden relative">
                <div className="absolute top-0 left-0 bg-primary text-white text-[10px] font-bold uppercase px-3 py-1">
                    System Pipeline
                </div>
                <div className="flex items-center justify-between mt-4 relative z-10">
                    {/* Step 1 */}
                    <div className="flex flex-col items-center gap-3 group">
                        <div className={`w-16 h-16 border-2 border-primary flex items-center justify-center bg-white shadow-[4px_4px_0px_0px_rgba(20,20,20,1)] ${uploadStatus ? 'animate-bounce' : ''}`}>
                             <span className="material-symbols-outlined">upload_file</span>
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest">Ingest</span>
                    </div>
                    {/* Connector */}
                    <div className="flex-1 h-[2px] bg-primary/20 mx-4 relative">
                         <div className="absolute top-1/2 left-0 -translate-y-1/2 w-full h-[2px] bg-primary scale-x-0 origin-left transition-transform duration-500"></div>
                    </div>
                     {/* Step 2 */}
                    <div className="flex flex-col items-center gap-3">
                         <div className="w-16 h-16 border-2 border-primary flex items-center justify-center bg-white group-hover:scale-110 transition-transform">
                             <span className="material-symbols-outlined">description</span>
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest">Extract</span>
                    </div>
                     {/* Connector */}
                    <div className="flex-1 h-[2px] bg-primary/20 mx-4"></div>
                     {/* Step 3 */}
                    <div className="flex flex-col items-center gap-3">
                         <div className="w-16 h-16 border-2 border-primary flex items-center justify-center bg-white">
                             <span className="material-symbols-outlined">psychology</span>
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest">Embed</span>
                    </div>
                     {/* Connector */}
                    <div className="flex-1 h-[2px] bg-primary/20 mx-4"></div>
                     {/* Step 4 */}
                    <div className="flex flex-col items-center gap-3">
                         <div className="w-16 h-16 border-2 border-primary flex items-center justify-center bg-white">
                             <span className="material-symbols-outlined">account_tree</span>
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest">Cluster</span>
                    </div>
                    {/* Connector */}
                    <div className="flex-1 h-[2px] border-t-2 border-dashed border-primary/30 mx-4"></div>
                     {/* Step 5 */}
                    <div className="flex flex-col items-center gap-3 opacity-50">
                         <div className="w-16 h-16 border-2 border-dashed border-primary flex items-center justify-center bg-transparent">
                             <span className="material-symbols-outlined">folder</span>
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest">OS Sync</span>
                    </div>
                </div>
            </div>

            {/* Cluster List / File Browser */}
            <div className="border-2 border-primary bg-white min-h-[400px] flex flex-col">
                <div className="border-b-2 border-primary p-4 flex justify-between items-center bg-slate-50">
                    <h3 className="text-sm font-black uppercase tracking-widest">Semantic Clusters</h3>
                    <div className="text-[10px] font-bold uppercase opacity-50">{graphData.clusters.length} Groups Active</div>
                </div>
                
                <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {graphData.clusters.length === 0 ? (
                        <div className="col-span-full py-12 text-center border-2 border-dashed border-primary/20 bg-slate-50">
                            <span className="material-symbols-outlined text-4xl opacity-20 mb-2">bubble_chart</span>
                            <p className="text-sm font-bold uppercase opacity-40">No clusters formed yet</p>
                            <p className="text-xs opacity-30 mt-1">Upload 4+ files to start clustering</p>
                        </div>
                    ) : (
                        graphData.clusters.map(cluster => (
                            <div key={cluster.id} className="border-2 border-primary p-4 hover:shadow-[4px_4px_0px_0px_rgba(20,20,20,1)] transition-shadow bg-white group cursor-pointer relative">
                                <div className="absolute top-2 right-2 w-3 h-3 rounded-full border border-primary" style={{backgroundColor: cluster.color}}></div>
                                <h4 className="font-bold uppercase text-sm mb-1 pr-6 truncate">{cluster.name}</h4>
                                <div className="text-[10px] font-mono opacity-60 mb-3">{cluster.file_count} FILES</div>
                                
                                <div className="space-y-1">
                                    {/* Preview firs t3 files */}
                                    {graphData.nodes
                                        .filter(n => n.cluster_id === cluster.id)
                                        .slice(0, 3)
                                        .map(file => (
                                            <div 
                                                key={file.id} 
                                                className="text-[10px] truncate border-l-2 border-transparent pl-2 hover:border-primary hover:bg-slate-50 py-0.5 cursor-pointer"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    fetch(`http://localhost:8000/open?path=${encodeURIComponent(file.id)}`);
                                                }}
                                            >
                                                {file.name}
                                            </div>
                                        ))
                                    }
                                    {cluster.file_count > 3 && (
                                        <div className="text-[10px] font-bold opacity-40 pl-2">+{cluster.file_count - 3} more...</div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>

        {/* Right Column: Logs */}
        <div className="lg:col-span-4 flex flex-col h-[calc(100vh-140px)] sticky top-24">
            <div className="border-2 border-primary bg-primary text-white flex flex-col h-full shadow-[8px_8px_0px_0px_rgba(0,0,0,0.2)]">
                <div className="p-4 border-b border-white/20 flex justify-between items-center">
                    <h3 className="text-sm font-black uppercase tracking-widest">System Log</h3>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.8)]"></div>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-xs custom-scrollbar" ref={logEndRef}>
                    {logs.length === 0 ? (
                        <div className="text-white/30 text-center mt-10 italic">System ready... waiting for input</div>
                    ) : (
                        logs.map((log, i) => (
                            <div key={i} className="flex gap-3 group">
                                <div className="shrink-0 w-[1px] bg-white/20 relative mt-1">
                                    <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full ${
                                        log.type === 'error' ? 'bg-red-500' : 
                                        log.type === 'success' ? 'bg-green-500' : 'bg-blue-400'
                                    }`}></div>
                                </div>
                                <div className="pb-2">
                                    <div className="text-[10px] opacity-40 mb-0.5">{log.time_str}</div>
                                    <div className="leading-relaxed text-white/90 group-hover:text-white transition-colors">
                                        {log.message}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                <div className="p-3 border-t border-white/20">
                     <div className="flex items-center gap-2 bg-white/10 px-3 py-2 border border-white/10">
                        <span className="text-white/50 text-[10px]">{'>'}</span>
                        <input 
                            type="text" 
                            disabled 
                            placeholder="Terminal Active" 
                            className="bg-transparent border-none text-white text-xs w-full focus:ring-0 placeholder:text-white/30 font-mono p-0"
                        />
                     </div>
                </div>
            </div>
        </div>

      </main>
    </div>
  );
}
