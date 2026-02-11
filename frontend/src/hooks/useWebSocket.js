import { useState, useEffect, useRef } from 'react';

export function useWebSocket(url) {
  const [graphData, setGraphData] = useState({ nodes: [], files: [], clusters: [], clusters_map: {}, total_files: 0 });
  const [logs, setLogs] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;

    function connect() {
      if (!isMounted.current) return;

      // Clean up any existing connection completely
      if (wsRef.current) {
        try {
          wsRef.current.onopen = null;
          wsRef.current.onmessage = null;
          wsRef.current.onclose = null;
          wsRef.current.onerror = null;
          wsRef.current.close();
        } catch (_) {}
        wsRef.current = null;
      }

      let ws;
      try {
        ws = new WebSocket(url);
      } catch (err) {
        scheduleReconnect();
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMounted.current) { ws.close(); return; }
        setConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        if (!isMounted.current) return;
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'graph_update') {
            setGraphData({
              nodes: data.nodes || [],
              files: data.files || data.nodes || [],
              clusters: data.clusters || [],
              clusters_map: data.clusters_map || {},
              total_files: data.total_files || 0,
            });
          } else if (data.type === 'activity_log') {
            setLogs(data.logs || []);
          } else if (data.type === 'activity_log_entry') {
            setLogs(prev => [...prev.slice(-49), data.entry]);
          }
        } catch (_) {}
      };

      ws.onclose = () => {
        if (!isMounted.current) return;
        setConnected(false);
        scheduleReconnect();
      };

      ws.onerror = () => {
        // onclose fires after onerror — let it handle reconnect
      };
    }

    function scheduleReconnect() {
      if (!isMounted.current) return;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);

      // Exponential backoff: 2s → 4s → 8s → 16s → 30s max
      const attempt = reconnectAttempts.current;
      const delay = Math.min(30000, 2000 * Math.pow(2, attempt));
      reconnectAttempts.current = attempt + 1;

      reconnectTimer.current = setTimeout(() => {
        if (isMounted.current) connect();
      }, delay);
    }

    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      if (wsRef.current) {
        try {
          wsRef.current.onopen = null;
          wsRef.current.onmessage = null;
          wsRef.current.onclose = null;
          wsRef.current.onerror = null;
          wsRef.current.close();
        } catch (_) {}
        wsRef.current = null;
      }
    };
  }, [url]);

  return { graphData, logs, connected };
}
