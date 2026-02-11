import { useNavigate } from 'react-router-dom';
import './Landing.css';

export default function LandingPage() {
  const navigate = useNavigate();
  const onLaunch = () => navigate('/dashboard');

  return (
    <div className="bg-white text-primary font-display antialiased min-h-screen flex flex-col">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 w-full border-b border-primary bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2 select-none">
            <span className="material-symbols-outlined text-3xl font-bold">folder_managed</span>
            <span className="text-xl font-black uppercase tracking-tighter">AuraFS</span>
          </div>
          <div className="flex gap-4">
            <button 
              className="bg-primary px-6 py-2 text-sm font-bold text-white hover:bg-black/90 transition-colors"
              onClick={onLaunch}
            >
              LAUNCH DASHBOARD
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="border-b border-primary py-20 lg:py-32">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
            <div className="flex flex-col gap-8">
              <h1 className="text-5xl font-black leading-[1.1] tracking-tighter md:text-7xl">
                YOUR FILES, ORGANIZED BY INTELLIGENCE.
              </h1>
              <p className="max-w-md text-lg font-medium leading-relaxed opacity-80">
                An AI-powered file system that understands your documents — using local embeddings, intelligent clustering, and real-time organization.
              </p>
              <div className="flex flex-wrap gap-4">
                <button 
                  onClick={onLaunch}
                  className="bg-primary border-2 border-primary px-8 py-4 text-base font-black text-white hover:bg-white hover:text-primary transition-colors"
                >
                  LAUNCH DASHBOARD
                </button>
                <button 
                  onClick={() => window.open('https://github.com', '_blank')}
                  className="border-2 border-primary px-8 py-4 text-base font-black hover:bg-primary hover:text-white transition-colors"
                >
                  VIEW SOURCE
                </button>
              </div>
            </div>
            
            {/* Hero Image */}
            <div className="relative aspect-square border-2 border-primary bg-background-light p-4 shadow-[12px_12px_0px_0px_rgba(20,20,20,1)] hover:shadow-[16px_16px_0px_0px_rgba(20,20,20,1)] transition-shadow duration-300">
              <div className="h-full w-full bg-black flex items-center justify-center border border-primary/20 overflow-hidden relative group">
                <img 
                  src="aurafs_hero_1770833324766.png" 
                  alt="AuraFS Neural Network Visualization" 
                  className="w-full h-full object-cover opacity-90 hover:opacity-100 transition-opacity duration-700 hover:scale-105 transform"
                />
                
                {/* Floating Elements overlay */}
                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute top-10 left-10 p-2 border border-white/20 bg-black/50 backdrop-blur-sm text-white shadow-lg text-xs font-mono">
                    /AURAFS_Clusters
                  </div>
                  <div className="absolute bottom-20 right-10 p-2 border border-white/20 bg-black/50 backdrop-blur-sm text-white shadow-lg text-xs font-mono">
                    Model: Llama 3.3 70B
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

     {/* Features Grid */}
<section className="border-b border-primary">
  <div className="grid grid-cols-1 md:grid-cols-3">
    
    {/* Feature 1 */}
    <div className="border-b border-primary p-12 md:border-b-0 md:border-r hover:bg-slate-50 transition-colors">
      <span className="material-symbols-outlined mb-6 text-4xl">memory</span>
      <h3 className="mb-4 text-2xl font-black tracking-tight">
        PRIVACY-FIRST AI ORGANIZATION
      </h3>
      <p className="font-medium leading-relaxed opacity-70">
        AuraFS keeps your files local. Semantic embeddings run on-device so your 
        data stays private while still enabling intelligent file understanding.
      </p>
    </div>

    {/* Feature 2 */}
    <div className="border-b border-primary p-12 md:border-b-0 md:border-r hover:bg-slate-50 transition-colors">
      <span className="material-symbols-outlined mb-6 text-4xl">psychology</span>
      <h3 className="mb-4 text-2xl font-black tracking-tight">
        REAL-TIME INTELLIGENT CLUSTERING
      </h3>
      <p className="font-medium leading-relaxed opacity-70">
        Files are grouped instantly by meaning — not filenames. High-speed AI 
        inference continuously keeps your workspace organized as new files arrive.
      </p>
    </div>

    {/* Feature 3 */}
    <div className="p-12 hover:bg-slate-50 transition-colors">
      <span className="material-symbols-outlined mb-6 text-4xl">folder_data</span>
      <h3 className="mb-4 text-2xl font-black tracking-tight">
        ADAPTIVE FOLDER INTELLIGENCE
      </h3>
      <p className="font-medium leading-relaxed opacity-70">
        AuraFS dynamically creates structured folders and subfolders that evolve 
        with your data — no manual sorting required.
      </p>
    </div>

  </div>
</section>


      {/* How AuraFS Works */}
<section className="bg-background-light py-20 lg:py-32 overflow-hidden border-b border-primary">
  <div className="mx-auto max-w-7xl px-6">
    <div className="mb-16 text-center">
      <h2 className="text-4xl font-black tracking-tighter uppercase md:text-5xl">
        How AuraFS Works
      </h2>
      <p className="mt-4 text-lg font-medium opacity-60">
        From file drop to intelligent organization — fully automatic.
      </p>
    </div>

    {/* Node Canvas */}
    <div className="relative flex flex-col items-center gap-12 lg:flex-row lg:justify-between lg:gap-4 p-8 border-2 border-primary bg-white shadow-sm">

      {/* Node 1 */}
      <div className="relative z-10 w-full max-w-[200px] border-2 border-primary bg-white p-4 text-center hover:translate-y-[-4px] transition-transform shadow-md">
        <div className="mb-2 text-[10px] font-bold uppercase tracking-widest opacity-50">
          Detection
        </div>
        <div className="font-black text-sm uppercase">File Monitoring</div>
        <div className="text-[10px] mt-1 opacity-60">
          Real-time folder watcher
        </div>
        <div className="workflow-dot -right-1.5 top-1/2 -translate-y-1/2"></div>
      </div>

      <div className="connector-line hidden lg:block"></div>

      {/* Node 2 */}
      <div className="relative z-10 w-full max-w-[200px] border-2 border-primary bg-white p-4 text-center hover:translate-y-[-4px] transition-transform shadow-md">
        <div className="mb-2 text-[10px] font-bold uppercase tracking-widest opacity-50">
          Understanding
        </div>
        <div className="font-black text-sm uppercase">Content Analysis</div>
        <div className="text-[10px] mt-1 opacity-60">
          PDF/Text extraction
        </div>
        <div className="workflow-dot -left-1.5 top-1/2 -translate-y-1/2"></div>
        <div className="workflow-dot -right-1.5 top-1/2 -translate-y-1/2"></div>
      </div>

      <div className="connector-line hidden lg:block"></div>

      {/* Node 3 */}
      <div className="relative z-10 w-full max-w-[200px] border-2 border-primary bg-white p-4 text-center hover:translate-y-[-4px] transition-transform shadow-md">
        <div className="mb-2 text-[10px] font-bold uppercase tracking-widest opacity-50">
          Intelligence
        </div>
        <div className="font-black text-sm uppercase">Semantic Embedding</div>
        <div className="text-[10px] mt-1 opacity-60">
          Local AI vectors
        </div>
        <div className="workflow-dot -left-1.5 top-1/2 -translate-y-1/2"></div>
        <div className="workflow-dot -right-1.5 top-1/2 -translate-y-1/2"></div>
      </div>

      <div className="connector-line hidden lg:block"></div>

      {/* Node 4 */}
      <div className="relative z-10 w-full max-w-[200px] border-2 border-primary bg-primary p-4 text-center text-white hover:translate-y-[-4px] transition-transform shadow-md">
        <div className="mb-2 text-[10px] font-bold uppercase tracking-widest opacity-50 text-white/70">
          AI Core
        </div>
        <div className="font-black text-sm uppercase">Smart Clustering</div>
        <div className="text-[10px] mt-1 opacity-70">
          Context-aware grouping
        </div>
        <div className="workflow-dot -left-1.5 top-1/2 -translate-y-1/2 !bg-white"></div>
        <div className="workflow-dot -right-1.5 top-1/2 -translate-y-1/2 !bg-white"></div>
      </div>

      <div className="connector-line hidden lg:block"></div>

      {/* Node 5 */}
      <div className="relative z-10 w-full max-w-[200px] border-2 border-primary bg-white p-4 text-center hover:translate-y-[-4px] transition-transform shadow-md">
        <div className="mb-2 text-[10px] font-bold uppercase tracking-widest opacity-50">
          Output
        </div>
        <div className="font-black text-sm uppercase">Auto Folder Sync</div>
        <div className="text-[10px] mt-1 opacity-60">
          OS-level organization
        </div>
        <div className="workflow-dot -left-1.5 top-1/2 -translate-y-1/2"></div>
      </div>
    </div>
  </div>
</section>

{/* Technical Impact Stats */}
<section className="border-b border-primary py-20 lg:py-32 bg-primary text-white">
  <div className="mx-auto max-w-7xl px-6">
    <div className="grid grid-cols-1 gap-12 md:grid-cols-3 text-center">

      <div className="flex flex-col gap-2">
        <span className="text-7xl font-black tracking-tighter">Local AI</span>
        <span className="text-sm font-bold uppercase tracking-widest opacity-60">
          Privacy-first processing
        </span>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-7xl font-black tracking-tighter">Real-Time</span>
        <span className="text-sm font-bold uppercase tracking-widest opacity-60">
          Continuous file organization
        </span>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-7xl font-black tracking-tighter">Zero Effort</span>
        <span className="text-sm font-bold uppercase tracking-widest opacity-60">
          No manual sorting required
        </span>
      </div>

    </div>
  </div>
</section>

     {/* Final CTA */}
<section className="py-20 lg:py-40">
  <div className="mx-auto max-w-4xl px-6 text-center">
    <h2 className="mb-8 text-5xl font-black tracking-tighter uppercase md:text-7xl">
      LET YOUR FILES ORGANIZE THEMSELVES
    </h2>
    <p className="mx-auto mb-12 max-w-lg text-xl font-medium opacity-70">
      AuraFS uses AI to automatically understand, cluster, and organize your files —
      so you never deal with messy folders again.
    </p>

    <div className="flex flex-col items-center justify-center gap-6 sm:flex-row">
      <button 
        onClick={onLaunch}
        className="w-full bg-primary border-2 border-primary px-10 py-5 text-lg font-black text-white hover:bg-white hover:text-primary transition-all sm:w-auto"
      >
        LAUNCH AURAFS
      </button>
    </div>
  </div>
</section>


{/* Footer */}
<footer className="border-t-4 border-primary bg-white py-12 mt-auto">
  <div className="mx-auto max-w-7xl px-6">
    <div className="flex flex-col md:flex-row justify-between items-center gap-6">

      <div className="flex items-center gap-2">
        <span className="material-symbols-outlined text-3xl font-bold">
          folder_managed
        </span>
        <span className="text-xl font-black uppercase tracking-tighter">
          AuraFS
        </span>
      </div>

      <div className="text-center md:text-right">
        <p className="text-sm font-semibold opacity-60">
          AI-Powered Semantic File Organization • Hackathon 2026 Prototype
        </p>
      </div>

    </div>
  </div>
</footer>

    </div>
  );
}
