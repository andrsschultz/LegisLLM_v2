export interface NormEntry {
  jurabk: string;
  enbez: string;
  P?: string;
  wording?: string;
}

export interface ProposalEntry {
  proposalTitle: string;
  description: string;
  affectedNorms: NormEntry[];
}

export interface EvaluatedProposal {
  proposalTitle: string;
  affectedNorms: NormEntry[];
  pro: string[];
  contra: string[];
}

export interface DeepEvaluation {
  juristischeBeurteilung: {
    Bewertung: string;
    PotentielleProbleme: string;
    Querverweise: NormEntry[];
  };
  rechtstechnischeBeurteilung: {
    Klarheit: string;
    Formulierungsvorschlag: string;
    Risikopunkte: string[];
  };
  dogmatischeBeurteilung: {
    Systematik: string;
    Prinzipien: string;
  };
  folgenabschätzung: {
    Verwaltungsaufwand: string;
    FiskalischeAuswirkungen: string;
    Praktikabilität: string;
    Übergangsregelungen: string;
  };
  fazitProContra: {
    Pro: string[];
    Contra: string[];
    OffeneFragen: string[];
  };
}

export interface Model {
  id: string;
  name: string;
  provider: string;
}

export interface ApiResponse<T> {
  entries: T[];
}

export interface AppState {
  taskDescription: string;
  selectedModel: string;
  availableModels: Model[];
  relevantNorms: NormEntry[] | null;
  amendmentProposals: ProposalEntry[] | null;
  evaluatedProposals: EvaluatedProposal[] | null;
  finalAmendment: string | null;
  currentTab: number;
  multistepReasoning: boolean;
  logs: string[];
}