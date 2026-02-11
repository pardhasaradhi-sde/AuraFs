import React, { useMemo, useRef, useCallback, useState, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

const CLUSTER_COLORS = [
  '#6366f1', '#f59e42', '#10b981', '#f43f5e',
  '#3b82f6', '#a855f7', '#eab308', '#14b8a6',
  '#e11d48', '#8b5cf6', '#22d3ee', '#f97316',
];

function getColor(idx) {
  return CLUSTER_COLORS[Math.abs(idx) % CLUSTER_COLORS.length];
}

export default function Graph2D({ graphState }) {
  const fgRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  /* ── Responsive sizing ─────────────────────────────────── */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) setDimensions({ width, height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  /* ── Track mouse position relative to container ────────── */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onMove = (e) => {
      const rect = el.getBoundingClientRect();
      setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    };
    el.addEventListener('mousemove', onMove);
    return () => el.removeEventListener('mousemove', onMove);
  }, []);

  /* ── Build graph data ──────────────────────────────────── */
  const graphData = useMemo(() => {
    if (!graphState?.files || graphState.files.length === 0)
      return { nodes: [], links: [] };

    const files = graphState.files;
    const clusters = graphState.clusters || {};

    // File nodes
    const nodes = files.map((f) => ({
      id: f.path || f.id,
      name: f.name,
      cluster: f.cluster ?? f.cluster_id ?? -1,
      color: getColor(f.cluster ?? f.cluster_id ?? 0),
      type: 'file',
      words: f.words ?? f.word_count ?? 0,
      keywords: f.keywords ?? [],
      snippet: f.snippet ?? '',
      clusterName: f.cluster_name ?? '',
    }));

    // Cluster center nodes
    Object.entries(clusters).forEach(([cid, info]) => {
      const id = Number(cid);
      nodes.push({
        id: `cluster-${id}`,
        name: info.name || `Cluster ${id}`,
        cluster: id,
        color: getColor(id),
        type: 'cluster',
        fileCount: info.file_count || files.filter((f) => (f.cluster ?? f.cluster_id) === id).length,
      });
    });

    // Links – file→cluster-center
    const links = [];
    files.forEach((f) => {
      const cid = f.cluster ?? f.cluster_id ?? -1;
      if (clusters[cid] !== undefined) {
        links.push({
          source: f.path || f.id,
          target: `cluster-${cid}`,
          color: getColor(cid),
        });
      }
    });

    return { nodes, links };
  }, [graphState]);

  /* ── Initial zoom-to-fit ───────────────────────────────── */
  useEffect(() => {
    const fg = fgRef.current;
    if (fg && graphData.nodes.length > 0) {
      setTimeout(() => fg.zoomToFit(400, 60), 500);
    }
  }, [graphData]);

  /* ── Node canvas draw ──────────────────────────────────── */
  const paintNode = useCallback(
    (node, ctx, globalScale) => {
      const nx = node.x;
      const ny = node.y;
      if (!Number.isFinite(nx) || !Number.isFinite(ny)) return;

      const isHovered = hoveredNode?.id === node.id;

      if (node.type === 'cluster') {
        const radius = 28 + (node.fileCount || 1) * 4;
        const grad = ctx.createRadialGradient(nx, ny, radius * 0.3, nx, ny, radius);
        grad.addColorStop(0, node.color + '22');
        grad.addColorStop(0.7, node.color + '11');
        grad.addColorStop(1, node.color + '00');
        ctx.beginPath();
        ctx.arc(nx, ny, radius, 0, 2 * Math.PI);
        ctx.fillStyle = grad;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(nx, ny, radius, 0, 2 * Math.PI);
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = node.color + '55';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.setLineDash([]);

        const label = node.name;
        const fontSize = Math.max(11 / globalScale, 3);
        ctx.font = `600 ${fontSize}px Inter, system-ui, sans-serif`;
        const tw = ctx.measureText(label).width;
        const pillW = tw + fontSize * 1.6;
        const pillH = fontSize * 1.8;
        const pillY = ny + radius * 0.15;
        const r = pillH / 2;

        ctx.beginPath();
        ctx.moveTo(nx - pillW / 2 + r, pillY - pillH / 2);
        ctx.lineTo(nx + pillW / 2 - r, pillY - pillH / 2);
        ctx.quadraticCurveTo(nx + pillW / 2, pillY - pillH / 2, nx + pillW / 2, pillY);
        ctx.quadraticCurveTo(nx + pillW / 2, pillY + pillH / 2, nx + pillW / 2 - r, pillY + pillH / 2);
        ctx.lineTo(nx - pillW / 2 + r, pillY + pillH / 2);
        ctx.quadraticCurveTo(nx - pillW / 2, pillY + pillH / 2, nx - pillW / 2, pillY);
        ctx.quadraticCurveTo(nx - pillW / 2, pillY - pillH / 2, nx - pillW / 2 + r, pillY - pillH / 2);
        ctx.closePath();
        ctx.fillStyle = isHovered ? node.color : node.color + 'dd';
        ctx.fill();

        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#fff';
        ctx.fillText(label, nx, pillY);

        const badge = `${node.fileCount} file${node.fileCount > 1 ? 's' : ''}`;
        const badgeSize = Math.max(9 / globalScale, 2.5);
        ctx.font = `500 ${badgeSize}px Inter, system-ui, sans-serif`;
        ctx.fillStyle = node.color + '99';
        ctx.fillText(badge, nx, pillY + pillH * 0.9);
        return;
      }

      // ── File node ──
      const baseR = isHovered ? 6 : 3.5;
      const r = baseR / Math.sqrt(globalScale);

      if (isHovered) {
        ctx.beginPath();
        ctx.arc(nx, ny, r * 2.5, 0, 2 * Math.PI);
        ctx.fillStyle = node.color + '33';
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(nx, ny, r, 0, 2 * Math.PI);
      ctx.fillStyle = node.color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 0.8 / globalScale;
      ctx.stroke();

      const fontSize = Math.max(9 / globalScale, 2.5);
      ctx.font = `400 ${fontSize}px Inter, system-ui, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isHovered ? '#fff' : '#cbd5e1';
      ctx.fillText(node.name, nx, ny + r + 2 / globalScale);
    },
    [hoveredNode]
  );

  /* ── Link canvas draw ──────────────────────────────────── */
  const paintLink = useCallback((link, ctx) => {
    const src = link.source;
    const tgt = link.target;
    if (!Number.isFinite(src?.x) || !Number.isFinite(src?.y) ||
        !Number.isFinite(tgt?.x) || !Number.isFinite(tgt?.y)) return;
    ctx.beginPath();
    ctx.moveTo(src.x, src.y);
    ctx.lineTo(tgt.x, tgt.y);
    ctx.strokeStyle = (link.color || '#6366f1') + '25';
    ctx.lineWidth = 0.8;
    ctx.stroke();
  }, []);

  /* ── Hit area for hover/click detection ──────────────── */
  const paintHitArea = useCallback((node, color, ctx) => {
    const nx = node.x;
    const ny = node.y;
    if (!Number.isFinite(nx) || !Number.isFinite(ny)) return;
    ctx.fillStyle = color;
    ctx.beginPath();
    // Cluster hit area = small pill region only (not the full glow circle),
    // so file nodes inside the cluster circle can still be hovered.
    const r = node.type === 'cluster' ? 14 : 10;
    ctx.arc(nx, ny, r, 0, 2 * Math.PI);
    ctx.fill();
  }, []);

  /* ── Hover handler ─────────────────────────────────────── */
  const handleNodeHover = useCallback((node) => {
    setHoveredNode(node || null);
    // Change cursor
    const el = containerRef.current;
    if (el) el.style.cursor = node ? 'pointer' : 'default';
  }, []);

  /* ── Click handler ─────────────────────────────────────── */
  const handleNodeClick = useCallback((node) => {
    if (!node) return;
    if (node.type === 'cluster') {
      const fg = fgRef.current;
      if (fg) fg.zoomToFit(400, 80, (n) => n.cluster === node.cluster);
    } else if (node.type === 'file') {
      fetch(`http://localhost:8000/open?path=${encodeURIComponent(node.id)}`)
        .catch(() => {});
    }
  }, []);

  /* ── Open file helper ──────────────────────────────────── */
  const openFile = useCallback((filePath) => {
    fetch(`http://localhost:8000/open?path=${encodeURIComponent(filePath)}`)
      .catch(() => {});
  }, []);

  /* ── Empty state ───────────────────────────────────────── */
  if (!graphState?.files?.length) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <svg className="mx-auto mb-3 w-12 h-12 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <p className="text-sm font-medium">No files yet</p>
          <p className="text-xs opacity-60 mt-1">Drop files into the watched folder to begin</p>
        </div>
      </div>
    );
  }

  /* ── Tooltip ───────────────────────────────────────────── */
  const tooltipNode = hoveredNode?.type === 'file' ? hoveredNode : null;

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[400px]">
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={paintHitArea}
        linkCanvasObject={paintLink}
        nodeRelSize={0}
        onNodeHover={handleNodeHover}
        onNodeClick={handleNodeClick}
        enableNodeDrag={true}
        cooldownTicks={80}
        d3AlphaDecay={0.04}
        d3VelocityDecay={0.3}
        backgroundColor="transparent"
        linkDirectionalParticles={0}
      />

      {/* Tooltip — rendered as a portal-style overlay inside container */}
      {tooltipNode && (
        <div
          style={{
            position: 'absolute',
            left: Math.min(mousePos.x + 16, dimensions.width - 260),
            top: Math.max(mousePos.y - 20, 8),
            zIndex: 999,
            pointerEvents: 'auto',
            maxWidth: 280,
          }}
        >
          <div style={{
            background: 'rgba(15, 15, 25, 0.96)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: 12,
            padding: '14px 16px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            color: '#fff',
            fontFamily: 'Inter, system-ui, sans-serif',
          }}>
            {/* File name */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span style={{
                width: 10, height: 10, borderRadius: '50%',
                background: tooltipNode.color, flexShrink: 0,
              }} />
              <span style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {tooltipNode.name}
              </span>
            </div>

            {/* Metadata row */}
            <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {tooltipNode.words > 0 && <span>📝 {tooltipNode.words.toLocaleString()} words</span>}
              {tooltipNode.clusterName && <span>📁 {tooltipNode.clusterName}</span>}
            </div>

            {/* Keywords */}
            {tooltipNode.keywords?.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
                {tooltipNode.keywords.slice(0, 5).map((kw, i) => (
                  <span key={i} style={{
                    fontSize: 10, padding: '2px 8px', borderRadius: 99,
                    background: 'rgba(255,255,255,0.1)', color: '#d1d5db',
                  }}>{kw}</span>
                ))}
              </div>
            )}

            {/* Snippet */}
            {tooltipNode.snippet && (
              <p style={{
                fontSize: 11, color: '#6b7280', lineHeight: 1.5,
                marginBottom: 10, overflow: 'hidden',
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
              }}>{tooltipNode.snippet}</p>
            )}

            {/* Open button */}
            <button
              onClick={(e) => { e.stopPropagation(); openFile(tooltipNode.id); }}
              onMouseDown={(e) => e.stopPropagation()}
              style={{
                width: '100%', padding: '6px 0', border: 'none', borderRadius: 8,
                background: 'rgba(255,255,255,0.12)', color: '#fff',
                fontSize: 11, fontWeight: 500, cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                transition: 'background 0.15s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.22)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.12)'}
            >
              📂 Open File
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
