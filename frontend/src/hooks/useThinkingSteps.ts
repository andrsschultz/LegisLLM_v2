import { useState, useCallback, useRef } from 'react';
import { ThinkingStep } from '@/components/ThinkingIndicator';

export interface StepDefinition {
  label: string;
}

interface UseThinkingStepsReturn {
  steps: ThinkingStep[];
  isActive: boolean;
  startedAt: number | null;
  startThinking: (stepDefs: StepDefinition[]) => void;
  advanceStep: () => void;
  setActiveStep: (index: number) => void;
  completeAll: () => void;
  reset: () => void;
}

export function useThinkingSteps(): UseThinkingStepsReturn {
  const [steps, setSteps] = useState<ThinkingStep[]>([]);
  const [isActive, setIsActive] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const currentStepRef = useRef(0);

  const startThinking = useCallback((stepDefs: StepDefinition[]) => {
    const now = Date.now();
    setStartedAt(now);
    setIsActive(true);
    currentStepRef.current = 0;
    setSteps(
      stepDefs.map((def, i) => ({
        label: def.label,
        status: i === 0 ? 'active' : 'pending',
        startedAt: i === 0 ? now : undefined,
      }))
    );
  }, []);

  const advanceStep = useCallback(() => {
    const now = Date.now();
    setSteps(prev => {
      const next = [...prev];
      const currentIdx = currentStepRef.current;
      if (currentIdx < next.length) {
        next[currentIdx] = { ...next[currentIdx], status: 'completed', completedAt: now };
      }
      const nextIdx = currentIdx + 1;
      if (nextIdx < next.length) {
        next[nextIdx] = { ...next[nextIdx], status: 'active', startedAt: now };
        currentStepRef.current = nextIdx;
      }
      return next;
    });
  }, []);

  const setActiveStep = useCallback((index: number) => {
    const now = Date.now();
    setSteps(prev => {
      const next = [...prev];
      for (let i = 0; i < next.length; i++) {
        if (i < index) {
          if (next[i].status !== 'completed') {
            next[i] = { ...next[i], status: 'completed', completedAt: now };
          }
        } else if (i === index) {
          next[i] = { ...next[i], status: 'active', startedAt: now };
        } else {
          next[i] = { ...next[i], status: 'pending' };
        }
      }
      currentStepRef.current = index;
      return next;
    });
  }, []);

  const completeAll = useCallback(() => {
    const now = Date.now();
    setIsActive(false);
    setSteps(prev =>
      prev.map(step =>
        step.status !== 'completed'
          ? { ...step, status: 'completed', completedAt: now }
          : step
      )
    );
  }, []);

  const reset = useCallback(() => {
    setSteps([]);
    setIsActive(false);
    setStartedAt(null);
    currentStepRef.current = 0;
  }, []);

  return {
    steps,
    isActive,
    startedAt,
    startThinking,
    advanceStep,
    setActiveStep,
    completeAll,
    reset,
  };
}

// Predefined step configurations for each endpoint
export const THINKING_STEPS = {
  identifyNorms: [
    { label: 'Identifiziere relevante Normen...' },
  ],
  identifyNormsMultistep: [
    { label: 'Identifiziere betroffene Gesetze...' },
    { label: 'Bestimme relevante Paragraphen...' },
    { label: 'Lade Normtexte...' },
    { label: 'Identifiziere relevante Absätze...' },
    { label: 'Finalisiere Ergebnisse...' },
  ],
  generateProposals: [
    { label: 'Entwickle Regelungsalternativen...' },
  ],
  evaluateProposals: [
    { label: 'Evaluiere Regelungsalternativen...' },
  ],
  deepEvaluate: [
    { label: 'Führe vertiefte Analyse durch...' },
  ],
  finalAmendment: [
    { label: 'Generiere Änderungswortlaut...' },
  ],
  aenderungsbefehle: [
    { label: 'Generiere Änderungsbefehle...' },
  ],
  entwurf: [
    { label: 'Erstelle Gesetzesentwurf...' },
  ],
};
