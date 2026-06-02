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
    if (!isActive || !startedAt) {
      return;
    }
    setElapsed(Date.now() - startedAt);
    const interval = setInterval(() => {
      setElapsed(Date.now() - startedAt);
    }, 100);
    return () => clearInterval(interval);
  }, [isActive, startedAt]);

  // Auto-scroll thinking text to bottom
  useEffect(() => {
    if (expanded && thinkingRef.current) {
      thinkingRef.current.scrollTop = thinkingRef.current.scrollHeight;
    }
  }, [thinkingText, expanded]);

  if (!isActive && steps.every(s => s.status === 'pending') && !thinkingText) return null;

  const activeStep = steps.find(s => s.status === 'active');
  const completedCount = steps.filter(s => s.status === 'completed').length;
  const allDone = !isActive && completedCount === steps.length;
  const hasThinking = thinkingText && thinkingText.length > 0;

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50/50 overflow-hidden transition-all duration-200">
      {/* Header - always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2 flex items-center gap-2.5 text-left hover:bg-gray-100/50 transition-colors"
      >
        {/* Status dot */}
        <div className="flex-shrink-0">
          {isActive ? (
            <div className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
          ) : allDone ? (
            <div className="w-2 h-2 rounded-full bg-green-500" />
          ) : (
            <div className="w-2 h-2 rounded-full bg-gray-400" />
          )}
        </div>

        {/* Status text */}
        <div className="flex-1 min-w-0">
          {isActive && activeStep ? (
            <span className="text-xs text-gray-500">
              {activeStep.label}
            </span>
          ) : allDone ? (
            <span className="text-xs text-gray-500">
              Abgeschlossen
            </span>
          ) : (
            <span className="text-xs text-gray-500">
              Verarbeitung
            </span>
          )}
        </div>

        {/* Timer */}
        {(isActive || elapsed > 0) && (
          <span className="flex-shrink-0 text-[10px] font-mono text-gray-400 tabular-nums">
            {formatElapsed(elapsed)}
          </span>
        )}

        {/* Expand/collapse chevron */}
        <svg
          className={`w-3 h-3 text-gray-400 transition-transform duration-200 flex-shrink-0 ${expanded ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {/* Expandable content */}
      {expanded && (
        <div className="px-3 pb-2.5 space-y-2">
          {/* Live thinking text - shown first */}
          {hasThinking && (
            <div>
              <div
                ref={thinkingRef}
                className="max-h-64 overflow-y-auto rounded bg-white border border-gray-200 px-2.5 py-2 scrollbar-thin scrollbar-thumb-gray-300"
              >
                <pre className="text-[11px] text-gray-500 font-mono whitespace-pre-wrap leading-relaxed break-words">
                  {thinkingText}
                  {isActive && (
                    <span className="inline-block w-1 h-3 bg-gray-400 animate-pulse ml-0.5 align-text-bottom rounded-sm" />
                  )}
                </pre>
              </div>
            </div>
          )}

          {/* Step list - only show when multiple steps */}
          {steps.length > 1 && (
          <div className="space-y-0">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center gap-2 py-0.5">
                <div className="flex-shrink-0">
                  {step.status === 'completed' ? (
                    <svg className="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  ) : step.status === 'active' ? (
                    <div className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse ml-[3px]" />
                  ) : (
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-300 ml-[3px]" />
                  )}
                </div>
                <span
                  className={`text-[11px] leading-none ${
                    step.status === 'completed'
                      ? 'text-gray-400'
                      : step.status === 'active'
                      ? 'text-gray-600'
                      : 'text-gray-300'
                  }`}
                >
                  {step.label}
                </span>
                {step.status === 'completed' && step.startedAt && step.completedAt && (
                  <span className="text-[9px] font-mono text-gray-300 tabular-nums">
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
