import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Background, Controls, Handle, MarkerType, MiniMap, Position, ReactFlow, applyNodeChanges } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Bot, ShieldCheck, UserCheck } from 'lucide-react';

// Dikey akış: bağımlılık derinliği satır, aynı derinlikteki (paralel) adımlar yan yana
const COL = 270;
const ROW = 150;
const TONE = { BACKLOG: 'neutral', READY: 'info', IN_PROGRESS: 'info', WAITING_APPROVAL: 'warning', REVISION: 'danger',
  QUARANTINED: 'danger', DONE: 'success', CANCELLED: 'neutral' };

/** Bağımlılık derinliğine göre satır, satır içi sırayla sütun: dar alanda da okunaklı varsayılan yerleşim. */
export function autoLayout(steps) {
  const byKey = Object.fromEntries(steps.map((s) => [s.key, s]));
  const depth = {};
  const visit = (k, seen = new Set()) => {
    if (depth[k] !== undefined) return depth[k];
    if (seen.has(k)) return 0;
    seen.add(k);
    const deps = (byKey[k]?.depends_on || []).filter((d) => byKey[d]);
    depth[k] = deps.length ? Math.max(...deps.map((d) => visit(d, seen))) + 1 : 0;
    return depth[k];
  };
  steps.forEach((s) => visit(s.key));
  const rows = {};
  return Object.fromEntries(steps.map((s) => {
    const d = depth[s.key];
    rows[d] = (rows[d] || 0) + 1;
    return [s.key, { x: (rows[d] - 1) * COL, y: d * ROW }];
  }));
}

/** Döngü kontrolü: target, source'a (dolaylı) bağlıysa source > target bağlantısı döngü yaratır. */
export function createsCycle(steps, source, target) {
  if (source === target) return true;
  const byKey = Object.fromEntries(steps.map((s) => [s.key, s]));
  const stack = [source];
  const seen = new Set();
  while (stack.length) {
    const k = stack.pop();
    if (k === target) return true;
    if (seen.has(k)) continue;
    seen.add(k);
    (byKey[k]?.depends_on || []).forEach((d) => stack.push(d));
  }
  return false;
}

function StepNode({ data, selected }) {
  const { step, info } = data;
  return (
    <div className={`pj-flow-node ${selected ? 'selected' : ''} ${info.status ? `st-${TONE[info.status] || 'neutral'}` : ''}`}>
      <Handle type="target" position={Position.Top} />
      <div className="pj-flow-node-head">
        <span className="pj-flow-key">{step.label || step.key}</span>
        {info.statusLabel && <span className={`ui-badge ui-badge-${TONE[info.status] || 'neutral'}`}>{info.statusLabel}</span>}
      </div>
      <strong title={step.title}>{step.title || 'Adsız adım'}</strong>
      <span><Bot size={12} /> {info.agent || 'Personel atanmadı'}</span>
      {info.reviewer && <span><ShieldCheck size={12} /> Kontrol: {info.reviewer}</span>}
      <span><UserCheck size={12} /> {step.requires_approval === false ? 'Onay gerekmez' : `Onay: ${info.approver || 'Proje yöneticisi'}`}
        {step.requires_approval !== false && ` · ret sınırı ${step.max_rejections || 3}`}</span>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
const nodeTypes = { step: StepNode };

/**
 * Akış şeması (ADIM 7.4). steps: [{key, title, depends_on, pos, requires_approval, max_rejections, ...}]
 * describe(step) -> {agent, reviewer, approver, status, statusLabel}
 * editable ise: sürükle (konum), bağla (bağımlılık), bağlantı sil, seçim (onSelect).
 */
export default function FlowCanvas({ steps, describe, editable = false, selectedKey, onSelect, onChange, height = 520 }) {
  const theme = typeof document !== 'undefined' ? document.documentElement.getAttribute('data-theme') : 'dark';
  const layout = useMemo(() => autoLayout(steps), [steps]);
  const build = useCallback(() => steps.map((s) => ({
    id: s.key, type: 'step', position: s.pos || layout[s.key], selected: s.key === selectedKey,
    data: { step: s, info: describe(s) }, draggable: editable,
  })), [steps, layout, describe, editable, selectedKey]);
  const [nodes, setNodes] = useState(build);
  useEffect(() => { setNodes(build()); }, [build]);

  const edges = useMemo(() => steps.flatMap((s) => (s.depends_on || []).filter((d) => steps.some((o) => o.key === d)).map((d) => {
    const working = ['IN_PROGRESS', 'REVISION'].includes(describe(s).status);
    return { id: `${d}->${s.key}`, source: d, target: s.key, animated: working, deletable: editable,
      markerEnd: { type: MarkerType.ArrowClosed }, style: { strokeWidth: 2 } };
  })), [steps, describe, editable]);

  const onNodesChange = useCallback((changes) => {
    setNodes((nds) => applyNodeChanges(changes, nds));
    const moved = changes.filter((c) => c.type === 'position' && c.dragging === false && c.position);
    if (editable && moved.length) {
      onChange?.(steps.map((s) => {
        const m = moved.find((c) => c.id === s.key);
        return m ? { ...s, pos: { x: Math.round(m.position.x), y: Math.round(m.position.y) } } : s;
      }));
    }
  }, [editable, onChange, steps]);

  const onConnect = useCallback(({ source, target }) => {
    if (!editable) return;
    if (createsCycle(steps, source, target)) {
      onChange?.(steps, 'Bu bağlantı döngü oluşturur: bir adım kendisine dolaylı olarak bağlı olamaz.');
      return;
    }
    onChange?.(steps.map((s) => (s.key === target ? { ...s, depends_on: [...new Set([...(s.depends_on || []), source])] } : s)));
  }, [editable, onChange, steps]);

  const onEdgesDelete = useCallback((deleted) => {
    if (!editable) return;
    onChange?.(steps.map((s) => {
      const drop = deleted.filter((e) => e.target === s.key).map((e) => e.source);
      return drop.length ? { ...s, depends_on: (s.depends_on || []).filter((d) => !drop.includes(d)) } : s;
    }));
  }, [editable, onChange, steps]);

  return (
    <div className="pj-flow" style={{ height }}>
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodesChange={onNodesChange} onConnect={onConnect}
        onEdgesDelete={onEdgesDelete} onNodeClick={(_, n) => onSelect?.(n.id)} onPaneClick={() => onSelect?.(null)}
        nodesConnectable={editable} elementsSelectable fitView fitViewOptions={{ padding: 0.15, maxZoom: 1 }} minZoom={0.3} maxZoom={1.5}
        colorMode={theme === 'light' ? 'light' : 'dark'} proOptions={{ hideAttribution: true }} deleteKeyCode={editable ? ['Backspace', 'Delete'] : null}>
        <Background gap={20} />
        <Controls showInteractive={false} />
        {steps.length > 6 && <MiniMap pannable zoomable />}
      </ReactFlow>
    </div>
  );
}
