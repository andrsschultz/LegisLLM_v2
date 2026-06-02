'use client';

import React, { useState, useEffect, useRef } from 'react';

export interface ThinkingStep {
  label: string;
  status: 'pending' | 'active' | 'completed';
  startedAt?: number;
  completedAt?: number;
}

interface ThinkingIndicatorProps {
  steps: ThinkingStep[];
  isActive: boolean;
  startedAt: number | null;
  thinkingText?: string;
}

function formatElapsed(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return `${minutes}m ${remaining.toString().padStart(2, '0')}s`;
}

export default function ThinkingIndicator({ steps, isActive, startedAt, thinkingText }: ThinkingIndicatorProps) {
  const [expanded, setExpanded] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const thinkingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isActive || !startedAt) return;
    setElapsed(Date.now() - startedAt);
    const interval = setInterval(() => setElapsed(Date.now() - startedAt), 1000);
    return () => clearInterval(interval);
  }, [isActive, startedAt]);

  useEffect(() => {
    if (expanded && thinkingRef.current) {
      thinkingRef.current.scrollTop = thinkingRef.current.scrollHeight;
    }
  }, [thinkingText, expanded]);

  if (!isActive && steps.every(s => s.status === 'pending') && !thinkingText) return null;

  const activeStep = steps.find(s => s.status === 'active');
  const allDone = !isActive && steps.length > 0 && steps.every(s => s.status === 'completed');
  const hasThinking = thinkingText && thinkingText.length > 0;

  const statusLabel = isActive && activeStep
    ? activeStep.label
    : allDone
    ? 'Abgeschlossen'
    : 'Verarbeitung';

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          {isActive ? (
            <div className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
          ) : allDone ? (
            <div className="w-2 h-2 rounded-full bg-green-500" />
          ) : (
            <div className="w-2 h-2 rounded-full bg-gray-300" />
          )}
          <span className="text-sm text-gray-600">{statusLabel}</span>
        </div>
        <div className="flex items-center gap-3">
          {(isActive || elapsed > 0) && (
            <span className="text-xs font-mono text-gray-400 tabular-nums">
              {formatElapsed(elapsed)}
            </span>
          )}
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-3 space-y-3">
          {hasThinking && (
            <div
              ref={thinkingRef}
              className="max-h-60 overflow-y-auto bg-white rounded-lg border border-gray-200 p-3 scrollbar-thin scrollbar-thumb-gray-300"
            >
              <pre className="text-xs text-gray-500 font-mono whitespace-pre-wrap break-words leading-relaxed">
                {thinkingText}
              </pre>
            </div>
          )}

          {steps.length > 1 && (
            <div className="space-y-1">
              {steps.map((step, index) => (
                <div key={index} className="flex items-center gap-2 py-0.5">
                  {step.status === 'completed' ? (
                    <svg className="w-3.5 h-3.5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  ) : step.status === 'active' ? (
                    <div className="w-2 h-2 rounded-full bg-orange-400 animate-pulse flex-shrink-0 ml-[3px]" />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-gray-300 flex-shrink-0 ml-[3px]" />
                  )}
                  <span className={`text-sm ${
                    step.status === 'completed' ? 'text-gray-400' : step.status === 'active' ? 'text-gray-600' : 'text-gray-400'
                  }`}>
                    {step.label}
                  </span>
                  {step.status === 'completed' && step.startedAt && step.completedAt && (
                    <span className="text-xs font-mono text-gray-400 tabular-nums">
                      {formatElapsed(step.completedAt - step.startedAt)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
