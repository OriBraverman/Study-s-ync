import React, { useState, useEffect } from 'react';

// Pre-defined graph: 6 nodes (A-F)
const GRAPH = {
  A: ['B', 'C'],
  B: ['D', 'E'],
  C: ['F'],
  D: [],
  E: ['F'],
  F: [],
};

const NODE_POSITIONS = {
  A: { x: 200, y: 50 },
  B: { x: 100, y: 150 },
  C: { x: 300, y: 150 },
  D: { x: 50, y: 250 },
  E: { x: 150, y: 250 },
  F: { x: 300, y: 250 },
};

const ALGORITHMS = {
  BFS: {
    name: 'Breadth-First Search (BFS)',
    structure: 'Queue',
    add: (arr, item) => [...arr, item], // enqueue (push back)
    remove: (arr) => {
      const [first, ...rest] = arr;
      return { item: first, rest };
    },
  },
  DFS: {
    name: 'Depth-First Search (DFS)',
    structure: 'Stack',
    add: (arr, item) => [item, ...arr], // push (to front)
    remove: (arr) => {
      const [first, ...rest] = arr;
      return { item: first, rest };
    },
  },
};

export default function GraphVisualizer() {
  const [algorithm, setAlgorithm] = useState('BFS');
  const [visited, setVisited] = useState([]);
  const [frontier, setFrontier] = useState([]);
  const [currentNode, setCurrentNode] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [log, setLog] = useState([]);

  const reset = () => {
    setVisited([]);
    setFrontier([]);
    setCurrentNode(null);
    setIsComplete(false);
    setLog(['Click "Next Step" to start.']);
  };

  const nextStep = () => {
    const algo = ALGORITHMS[algorithm];

    // Initialization step
    if (visited.length === 0 && frontier.length === 0 && !isComplete) {
      const start = 'A';
      setFrontier([start]);
      setLog((prev) => [...prev, `Initialized ${algo.structure} with start node '${start}'.`]);
      return;
    }

    if (isComplete || frontier.length === 0) {
      setIsComplete(true);
      if (!isComplete) setLog((prev) => [...prev, 'Traversal complete!']);
      return;
    }

    // Remove from frontier
    const { item: node, rest: newFrontier } = algo.remove(frontier);

    if (visited.includes(node)) {
      setFrontier(newFrontier);
      setLog((prev) => [...prev, `Node '${node}' already visited. Skipping.`]);
      return;
    }

    const newVisited = [...visited, node];
    setCurrentNode(node);
    setVisited(newVisited);

    // Add unvisited neighbors to frontier
    const neighbors = GRAPH[node] || [];
    let updatedFrontier = newFrontier;
    const added = [];
    neighbors.forEach((n) => {
      if (!newVisited.includes(n) && !updatedFrontier.includes(n)) {
        updatedFrontier = algo.add(updatedFrontier, n);
        added.push(n);
      }
    });

    setFrontier(updatedFrontier);

    const logMsg = added.length > 0
      ? `Visited '${node}'. Added neighbors [${added.join(', ')}] to ${algo.structure}.`
      : `Visited '${node}'. No new neighbors to add.`;

    setLog((prev) => [...prev, logMsg]);

    if (updatedFrontier.length === 0) {
      setIsComplete(true);
      setLog((prev) => [...prev, 'Traversal complete!']);
    }
  };

  useEffect(() => {
    reset();
  }, [algorithm]);

  const getNodeColor = (node) => {
    if (currentNode === node) return 'bg-yellow-400 border-yellow-600 scale-110';
    if (visited.includes(node)) return 'bg-blue-500 border-blue-700';
    if (frontier.includes(node)) return 'bg-green-400 border-green-600 animate-pulse';
    return 'bg-gray-300 border-gray-500';
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-800 mb-2">Study[S]ync Graph Visualizer</h1>
        <p className="text-slate-600 mb-6">Interactive BFS / DFS Traversal Demo</p>

        {/* Algorithm Selector */}
        <div className="flex gap-4 mb-6">
          {Object.keys(ALGORITHMS).map((key) => (
            <button
              key={key}
              onClick={() => setAlgorithm(key)}
              className={`px-5 py-2 rounded-lg font-semibold transition-all ${
                algorithm === key
                  ? 'bg-indigo-600 text-white shadow-lg'
                  : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-100'
              }`}
            >
              {ALGORITHMS[key].name}
            </button>
          ))}
        </div>

        {/* Controls */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={nextStep}
            disabled={isComplete}
            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-400 text-white rounded-lg font-semibold shadow transition-colors"
          >
            {visited.length === 0 ? 'Start Traversal' : 'Next Step'}
          </button>
          <button
            onClick={reset}
            className="px-6 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-lg font-semibold transition-colors"
          >
            Reset
          </button>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Graph Canvas */}
          <div className="relative bg-white rounded-xl shadow-lg border border-slate-200" style={{ width: 400, height: 320 }}>
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {Object.entries(GRAPH).map(([node, neighbors]) =>
                neighbors.map((n) => (
                  <line
                    key={`${node}-${n}`}
                    x1={NODE_POSITIONS[node].x + 20}
                    y1={NODE_POSITIONS[node].y + 20}
                    x2={NODE_POSITIONS[n].x + 20}
                    y2={NODE_POSITIONS[n].y + 20}
                    stroke="#94a3b8"
                    strokeWidth="2"
                  />
                ))
              )}
            </svg>
            {Object.entries(NODE_POSITIONS).map(([node, pos]) => (
              <div
                key={node}
                className={`absolute w-10 h-10 flex items-center justify-center rounded-full border-2 font-bold text-white transition-all duration-500 shadow-md ${getNodeColor(node)}`}
                style={{ left: pos.x, top: pos.y }}
              >
                {node}
              </div>
            ))}
          </div>

          {/* Sidebar Info */}
          <div className="flex-1 space-y-4">
            {/* Frontier / Stack or Queue */}
            <div className="bg-white rounded-xl shadow border border-slate-200 p-5">
              <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500 mb-2">
                Current {ALGORITHMS[algorithm].structure}
              </h3>
              <div className="flex gap-2">
                {frontier.length === 0 ? (
                  <span className="text-slate-400 italic">Empty</span>
                ) : (
                  frontier.map((item, idx) => (
                    <div
                      key={idx}
                      className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-md font-mono font-semibold border border-indigo-200"
                    >
                      {item}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Visited Nodes */}
            <div className="bg-white rounded-xl shadow border border-slate-200 p-5">
              <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500 mb-2">
                Visited Nodes
              </h3>
              <div className="flex gap-2 flex-wrap">
                {visited.length === 0 ? (
                  <span className="text-slate-400 italic">None</span>
                ) : (
                  visited.map((node) => (
                    <span key={node} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm font-semibold">
                      {node}
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Log */}
            <div className="bg-slate-900 rounded-xl shadow p-5 h-48 overflow-y-auto font-mono text-sm">
              <h3 className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2">Execution Log</h3>
              {log.map((entry, idx) => (
                <div key={idx} className="text-green-400 mb-1">
                  <span className="text-slate-500 mr-2">{idx + 1}.</span>
                  {entry}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
