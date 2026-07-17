import { useEffect, useRef, useState } from "react";
import { getProjectGraph } from "../api/client";

interface Node {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface Edge {
  id: string;
  source: string | Node;
  target: string | Node;
  label: string;
}

const TYPE_COLORS: Record<string, string> = {
  Decision: "#2563eb",
  Project: "#059669",
  Person: "#d97706",
};

function resolveEdgeEndpoints(edges: Edge[], nodeMap: Map<string, Node>): Edge[] {
  return edges
    .map((e) => {
      const src = typeof e.source === "string" ? nodeMap.get(e.source) : e.source;
      const tgt = typeof e.target === "string" ? nodeMap.get(e.target) : e.target;
      return src && tgt ? { ...e, source: src, target: tgt } : null;
    })
    .filter(Boolean) as Edge[];
}

export default function KnowledgeGraphView({ pid }: { pid: string }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ label: string; type: string; x: number; y: number } | null>(null);
  const animRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    getProjectGraph(pid)
      .then((data) => {
        if (cancelled) return;

        if (!data.nodes || data.nodes.length === 0) {
          setLoading(false);
          return;
        }

        const W = containerRef.current?.clientWidth ?? 800;
        const H = containerRef.current?.clientHeight ?? 500;

        const cx = W / 2;
        const cy = H / 2;

        const nodeMap = new Map<string, Node>();
        const nodes: Node[] = data.nodes.map((n) => {
          const angle = Math.random() * 2 * Math.PI;
          const r = 30 + Math.random() * 80;
          const node: Node = {
            id: n.id,
            label: n.label,
            type: n.type,
            x: cx + r * Math.cos(angle),
            y: cy + r * Math.sin(angle),
            vx: 0,
            vy: 0,
          };
          nodeMap.set(n.id, node);
          return node;
        });

        const rawEdges: Edge[] = data.edges.map((e: any) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label,
        }));
        const edges = resolveEdgeEndpoints(rawEdges, nodeMap);
        setLoading(false);
        startSimulation(nodes, edges, W, H);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };

    function startSimulation(nodes: Node[], edges: Edge[], W: number, H: number) {
      const svg = svgRef.current;
      if (!svg) return;

      svg.innerHTML = "";

      // SVG namespace
      const NS = "http://www.w3.org/2000/svg";
      const g = document.createElementNS(NS, "g");
      svg.appendChild(g);

      // Zoom & pan state
      interface ViewState {
        tx: number;
        ty: number;
        scale: number;
      }
      const view: ViewState = { tx: 0, ty: 0, scale: 1 };

      let dragNode: Node | null = null;

      // Edge lines
      const lineEls: SVGLineElement[] = [];
      for (const _e of edges) {
        const line = document.createElementNS(NS, "line");
        line.setAttribute("stroke", "#cbd5e1");
        line.setAttribute("stroke-width", "1.5");
        g.appendChild(line);
        lineEls.push(line);
      }

      // Node groups
      const nodeGroups: SVGGElement[] = [];
      const circleEls: SVGCircleElement[] = [];
      const labelEls: SVGTextElement[] = [];

      for (const node of nodes) {
        const ng = document.createElementNS(NS, "g");
        ng.style.cursor = "pointer";

        const circle = document.createElementNS(NS, "circle");
        circle.setAttribute("r", "6");
        circle.setAttribute("fill", TYPE_COLORS[node.type] || "#6366f1");
        circle.setAttribute("stroke", "#fff");
        circle.setAttribute("stroke-width", "2");
        ng.appendChild(circle);
        circleEls.push(circle);

        const text = document.createElementNS(NS, "text");
        text.setAttribute("dx", "10");
        text.setAttribute("dy", "3");
        text.setAttribute("font-size", "11");
        text.setAttribute("fill", "#334155");
        text.setAttribute("font-family", "system-ui, sans-serif");
        text.textContent = node.label.length > 16 ? node.label.slice(0, 15) + "..." : node.label;
        ng.appendChild(text);
        labelEls.push(text);

        // Hover
        ng.addEventListener("mouseenter", () => {
          circle.setAttribute("r", "9");
          const rect = svg.getBoundingClientRect();
          const sx = (node.x! + view.tx) * view.scale + rect.left;
          const sy = (node.y! + view.ty) * view.scale + rect.top;
          setTooltip({ label: node.label, type: node.type, x: sx, y: sy });
        });
        ng.addEventListener("mouseleave", () => {
          circle.setAttribute("r", "6");
          setTooltip(null);
        });

        // Drag
        ng.addEventListener("mousedown", (ev) => {
          dragNode = node;
          ev.stopPropagation();
        });

        g.appendChild(ng);
        nodeGroups.push(ng);
      }

      // SVG-level pan
      svg.addEventListener("mousedown", (e) => {
        if (dragNode) return;
        const startX = e.clientX - view.tx;
        const startY = e.clientY - view.ty;
        const onMove = (ev: MouseEvent) => {
          view.tx = ev.clientX - startX;
          view.ty = ev.clientY - startY;
        };
        const onUp = () => {
          window.removeEventListener("mousemove", onMove);
          window.removeEventListener("mouseup", onUp);
        };
        window.addEventListener("mousemove", onMove);
        window.addEventListener("mouseup", onUp);
      });

      // Global mouse move for drag
      window.addEventListener("mousemove", (e) => {
        if (!dragNode) return;
        const rect = svg.getBoundingClientRect();
        dragNode.x = (e.clientX - rect.left - view.tx) / view.scale;
        dragNode.y = (e.clientY - rect.top - view.ty) / view.scale;
      });
      window.addEventListener("mouseup", () => {
        dragNode = null;
      });

      // Scroll zoom
      svg.addEventListener("wheel", (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.92 : 1.08;
        view.scale = Math.max(0.2, Math.min(3, view.scale * delta));
      });

      // Physics
      const REPULSION = 800;
      const ATTRACTION = 0.005;
      const DAMPING = 0.85;
      const CENTER_FORCE = 0.002;

      function tick() {
        // Forces
        for (const n of nodes) {
          if (n === dragNode) {
            n.vx = 0;
            n.vy = 0;
            continue;
          }
          // Repulsion between all pairs
          for (const m of nodes) {
            if (n === m) continue;
            let dx = n.x! - m.x!;
            let dy = n.y! - m.y!;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = REPULSION / (dist * dist);
            n.vx! += (dx / dist) * force * 0.5;
            n.vy! += (dy / dist) * force * 0.5;
          }
          // Center pull
          n.vx! += ((W / 2) - n.x!) * CENTER_FORCE;
          n.vy! += ((H / 2) - n.y!) * CENTER_FORCE;
        }

        // Edge attraction
        for (const e of edges) {
          const s = e.source as Node;
          const t = e.target as Node;
          let dx = t.x! - s.x!;
          let dy = t.y! - s.y!;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 70) * ATTRACTION;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          if (s !== dragNode) { s.vx! += fx; s.vy! += fy; }
          if (t !== dragNode) { t.vx! -= fx; t.vy! -= fy; }
        }

        // Apply velocity
        for (const n of nodes) {
          n.vx! *= DAMPING;
          n.vy! *= DAMPING;
          n.x! += n.vx!;
          n.y! += n.vy!;
          n.x = Math.max(20, Math.min(W - 20, n.x!));
          n.y = Math.max(20, Math.min(H - 20, n.y!));
        }

        // Render
        g.setAttribute("transform", `translate(${view.tx},${view.ty}) scale(${view.scale})`);

        for (let i = 0; i < edges.length; i++) {
          const s = edges[i].source as Node;
          const t = edges[i].target as Node;
          lineEls[i].setAttribute("x1", String(s.x));
          lineEls[i].setAttribute("y1", String(s.y));
          lineEls[i].setAttribute("x2", String(t.x));
          lineEls[i].setAttribute("y2", String(t.y));
        }

        for (let i = 0; i < nodes.length; i++) {
          const n = nodes[i];
          circleEls[i].setAttribute("cx", String(n.x));
          circleEls[i].setAttribute("cy", String(n.y));
          nodeGroups[i].setAttribute("transform", `translate(${n.x},${n.y})`);
        }

        animRef.current = requestAnimationFrame(tick);
      }

      animRef.current = requestAnimationFrame(tick);
    }
  }, [pid]);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-ew-gray-text text-[13px]">Loading graph data...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-64 text-red-500 text-[13px]">{error}</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <h3 className="text-[15px] font-medium mb-3">Knowledge Graph</h3>
      <div ref={containerRef} className="flex-1 border rounded-lg bg-white overflow-hidden relative" style={{ minHeight: 400 }}>
        <svg ref={svgRef} className="w-full h-full" />
        {tooltip && (
          <div
            className="absolute pointer-events-none bg-gray-900 text-white text-[12px] px-2 py-1 rounded shadow z-50 whitespace-nowrap"
            style={{ left: tooltip.x + 12, top: tooltip.y - 28 }}
          >
            <span className="font-medium">{tooltip.label}</span>
            <span className="ml-1.5 opacity-60">({tooltip.type})</span>
          </div>
        )}
      </div>
    </div>
  );
}
