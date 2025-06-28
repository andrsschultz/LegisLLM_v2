'use client';

import React, { useState } from 'react';
import { useApp } from '@/contexts/AppContext';

export default function LogViewer() {
  const { state, clearLogs } = useApp();
  const [isExpanded, setIsExpanded] = useState(false);

  const downloadLogs = () => {
    const logsText = state.logs.join('\n');
    const element = document.createElement('a');
    const file = new Blob([logsText], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = 'legisllm_logs.txt';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 text-left focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <div className="flex items-center justify-between">
          <span className="text-lg font-semibold text-gray-900">📋 Logs anzeigen</span>
          <span className="text-gray-500">
            {isExpanded ? '▼' : '▶'}
          </span>
        </div>
      </button>
      
      {isExpanded && (
        <div className="px-6 pb-6">
          <div className="flex space-x-3 mb-4">
            <button
              onClick={() => setIsExpanded(true)} // Force refresh
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Logs aktualisieren
            </button>
            <button
              onClick={clearLogs}
              className="px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors"
            >
              Logs löschen
            </button>
            <button
              onClick={downloadLogs}
              className="px-4 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
            >
              Logs herunterladen
            </button>
          </div>
          
          <div className="bg-gray-100 rounded-lg p-4 h-80 overflow-y-auto">
            <pre className="text-xs text-gray-800 font-mono whitespace-pre-wrap">
              {state.logs.length > 0 ? state.logs.join('\n') : 'Keine Logs verfügbar.'}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}