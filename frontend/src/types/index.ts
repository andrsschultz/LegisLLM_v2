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

export interface ExpenditureEntry {
  title: string;
  description: string;
  cost_category: 'high' | 'low';
  citizens_cost_eur: number;
  business_cost_eur: number;
  administration_cost_eur: number;
  total_cost_eur: number;
  full_text: string;
}

export interface AppState {
  taskDescription: string;
  selectedModel: string;
  availableModels: Model[];
  relevantNorms: NormEntry[] | null;
  amendmentProposals: ProposalEntry[] | null;
  evaluatedProposals: EvaluatedProposal[] | null;
  finalAmendment: string | null;
  expenditure: ExpenditureEntry[] | null;
  currentTab: number;
  multistepReasoning: boolean;
  logs: string[];
}