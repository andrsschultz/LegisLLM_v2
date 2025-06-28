'use client';

import React from 'react';
import { useApp } from '@/contexts/AppContext';

const suggestions = [
  "Einführung einer Freigrenze für Einnahmen aus Vermietung und Verpachtung",
  "Die Pendlerpauschale wird zum 01.01.2026 auf 38 Cent ab dem ersten Kilometer dauerhaft erhöht",
  "Der Gewerbesteuer-Mindesthebesatz wird von 200 auf 280 Prozent erhöht",
  "Steuerfreistellung von Überstundenzuschlägen, die über die tariflich vereinbarte beziehungsweise an Tarifverträgen orientierte Vollzeitarbeit hinausgehen",
  "Ausnahme gemeinnütziger Organisationen mit Einnahmen bis 100.000 Euro vom Erfordernis einer zeitnahen Mittelverwendung"
];

export default function TaskDescriptionTab() {
  const { state, setTaskDescription, setCurrentTab } = useApp();

  const handleSuggestionClick = (suggestion: string) => {
    setTaskDescription(suggestion);
  };

  const handleNext = () => {
    setCurrentTab(1);
  };

  return (
    <div className="space-y-8">
      <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-xl p-6 shadow-sm">
        <h2 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
          <span className="text-2xl">📝</span>
          1. Legistische Aufgabenstellung
        </h2>
        <p className="text-slate-600 mt-2">Definieren Sie die rechtliche Änderung, die Sie vornehmen möchten.</p>
      </div>
      
      <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-xl p-6 shadow-sm">
        <label className="block text-lg font-semibold text-slate-700 mb-4">
          Beschreiben Sie die legistische Aufgabenstellung
        </label>
        <textarea
          value={state.taskDescription}
          onChange={(e) => setTaskDescription(e.target.value)}
          rows={6}
          className="block w-full px-4 py-3 border border-slate-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 bg-white/90 backdrop-blur-sm transition-all duration-200 resize-none"
          placeholder="Geben Sie hier die Aufgabenstellung für die Gesetzesänderung ein..."
        />
        <p className="mt-3 text-sm text-slate-500">
          Beschreiben Sie präzise, welche rechtliche Änderung Sie vornehmen möchten.
        </p>
      </div>

      {/* Suggestions */}
      <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-xl p-6 shadow-sm">
        <p className="text-lg font-semibold text-slate-700 mb-4 flex items-center gap-2">
          <span>💡</span> Beispiele für Aufgabenstellungen:
        </p>
        <div className="space-y-3">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              className="block w-full text-left px-4 py-3 text-sm bg-slate-50/80 hover:bg-slate-100/80 rounded-xl border border-slate-200/60 transition-all duration-200 hover:shadow-md backdrop-blur-sm"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-end pt-4">
        <button
          onClick={handleNext}
          disabled={!state.taskDescription?.trim()}
          className="px-8 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Weiter →
        </button>
      </div>
    </div>
  );
}