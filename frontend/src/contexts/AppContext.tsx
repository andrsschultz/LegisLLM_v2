'use client';

import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { AppState, NormEntry, ProposalEntry, EvaluatedProposal, Model, AmendmentEntry } from '@/types';

interface AppAction {
  type: string;
  payload?: any;
}

const initialState: AppState = {
  taskDescription: '',
  selectedModel: '',
  availableModels: [],
  relevantNorms: null,
  amendmentProposals: null,
  evaluatedProposals: null,
  finalAmendment: null,
  currentTab: 0,
  multistepReasoning: false,
  logs: [],
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_TASK_DESCRIPTION':
      return { ...state, taskDescription: action.payload };
    case 'SET_SELECTED_MODEL':
      return { ...state, selectedModel: action.payload };
    case 'SET_AVAILABLE_MODELS':
      return { ...state, availableModels: action.payload };
    case 'SET_RELEVANT_NORMS':
      return { ...state, relevantNorms: action.payload };
    case 'SET_AMENDMENT_PROPOSALS':
      return { ...state, amendmentProposals: action.payload };
    case 'SET_EVALUATED_PROPOSALS':
      return { ...state, evaluatedProposals: action.payload };
    case 'SET_FINAL_AMENDMENT':
      return { ...state, finalAmendment: action.payload };
    case 'SET_CURRENT_TAB':
      return { ...state, currentTab: action.payload };
    case 'SET_MULTISTEP_REASONING':
      return { ...state, multistepReasoning: action.payload };
    case 'ADD_LOG':
      return { 
        ...state, 
        logs: [...state.logs, action.payload].slice(-1000) // Keep last 1000 logs
      };
    case 'CLEAR_LOGS':
      return { ...state, logs: [] };
    case 'RESET_STATE':
      return initialState;
    default:
      return state;
  }
}

interface AppContextType {
  state: AppState;
  setTaskDescription: (description: string) => void;
  setSelectedModel: (model: string) => void;
  setAvailableModels: (models: Model[]) => void;
  setRelevantNorms: (norms: NormEntry[]) => void;
  setAmendmentProposals: (proposals: ProposalEntry[]) => void;
  setEvaluatedProposals: (proposals: EvaluatedProposal[]) => void;
  setFinalAmendment: (amendment: AmendmentEntry[]) => void;
  setCurrentTab: (tab: number) => void;
  setMultistepReasoning: (enabled: boolean) => void;
  addLog: (message: string) => void;
  clearLogs: () => void;
  resetState: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const contextValue: AppContextType = {
    state,
    setTaskDescription: (description: string) => 
      dispatch({ type: 'SET_TASK_DESCRIPTION', payload: description }),
    setSelectedModel: (model: string) => 
      dispatch({ type: 'SET_SELECTED_MODEL', payload: model }),
    setAvailableModels: (models: Model[]) => 
      dispatch({ type: 'SET_AVAILABLE_MODELS', payload: models }),
    setRelevantNorms: (norms: NormEntry[]) => 
      dispatch({ type: 'SET_RELEVANT_NORMS', payload: norms }),
    setAmendmentProposals: (proposals: ProposalEntry[]) => 
      dispatch({ type: 'SET_AMENDMENT_PROPOSALS', payload: proposals }),
    setEvaluatedProposals: (proposals: EvaluatedProposal[]) => 
      dispatch({ type: 'SET_EVALUATED_PROPOSALS', payload: proposals }),
    setFinalAmendment: (amendment: AmendmentEntry[]) => 
      dispatch({ type: 'SET_FINAL_AMENDMENT', payload: amendment }),
    setCurrentTab: (tab: number) => 
      dispatch({ type: 'SET_CURRENT_TAB', payload: tab }),
    setMultistepReasoning: (enabled: boolean) => 
      dispatch({ type: 'SET_MULTISTEP_REASONING', payload: enabled }),
    addLog: (message: string) => 
      dispatch({ type: 'ADD_LOG', payload: message }),
    clearLogs: () => 
      dispatch({ type: 'CLEAR_LOGS' }),
    resetState: () => 
      dispatch({ type: 'RESET_STATE' }),
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}