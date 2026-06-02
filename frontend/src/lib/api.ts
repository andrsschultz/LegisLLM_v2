import { NormEntry, ProposalEntry, EvaluatedProposal, DeepEvaluation, Model, ApiResponse, AmendmentEntry } from '@/types';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

class ApiClient {
  private abortControllers: Map<string, AbortController> = new Map();

  private getHeaders(apiKey: string): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    };
  }

  cancelRequest(requestId: string): boolean {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
      return true;
    }
    return false;
  }

  private createAbortableRequest(requestId: string): AbortController {
    // Cancel any existing request with the same ID
    this.cancelRequest(requestId);
    
    const controller = new AbortController();
    this.abortControllers.set(requestId, controller);
    return controller;
  }

  private async logApiCall(endpoint: string, statusCode: number, responseLength: number = 0) {
    console.log(`\n==== API CALL ====`);
    console.log(`Endpoint: ${endpoint}`);
    console.log(`Status: ${statusCode}`);
    console.log(`Response length: ${responseLength} characters`);
  }

  async fetchModels(apiKey: string): Promise<{ models: Model[]; default: string | null }> {
    try {
      const response = await fetch(`${BACKEND_URL}/models`, {
        headers: this.getHeaders(apiKey),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return {
        models: data.models || [],
        default: data.default || null,
      };
    } catch (error) {
      console.error('Error fetching models:', error);
      return { models: [], default: null };
    }
  }

  async fetchOrganizedModels(apiKey: string): Promise<{ organized: any; default: string | null }> {
    try {
      const response = await fetch(`${BACKEND_URL}/models/organized`, {
        headers: this.getHeaders(apiKey),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return {
        organized: data.organized || {},
        default: data.default || null,
      };
    } catch (error) {
      console.error('Error fetching organized models:', error);
      return { organized: {}, default: null };
    }
  }

  async fetchLaws(): Promise<{ laws: string[]; count: number; updated_at: string | null }> {
    try {
      const response = await fetch(`${BACKEND_URL}/laws`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching laws:', error);
      return { laws: [], count: 0, updated_at: null };
    }
  }

  async identifyRelevantNorms(
    taskDescription: string,
    apiKey: string,
    model: string,
    multistepReasoning: boolean = false,
    selectedLaws: string[] = []
  ): Promise<NormEntry[]> {
    const requestId = 'identify-norms';
    const controller = this.createAbortableRequest(requestId);
    const endpoint = multistepReasoning
      ? `${BACKEND_URL}/identify_multistep`
      : `${BACKEND_URL}/identify`;

    const body: Record<string, unknown> = { task_description: taskDescription };
    if (selectedLaws.length > 0) {
      body.selected_laws = selectedLaws;
    }

    try {
      const response = await fetch(`${endpoint}?model=${encodeURIComponent(model)}`, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      await this.logApiCall(endpoint, response.status, 0);

      if (!response.ok) {
        if (response.status === 500) {
          throw new Error('SERVER_ERROR');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse<NormEntry> = await response.json();
      await this.logApiCall(endpoint, response.status, JSON.stringify(data).length);
      
      return data.entries || [];
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error('REQUEST_CANCELLED');
      }
      console.error('Error identifying relevant norms:', error);
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  async generateProposals(
    taskDescription: string,
    relevantNorms: NormEntry[],
    apiKey: string,
    model: string
  ): Promise<ProposalEntry[]> {
    const requestId = 'generate-proposals';
    const controller = this.createAbortableRequest(requestId);
    const endpoint = `${BACKEND_URL}/generate_proposals`;
    
    try {
      const response = await fetch(`${endpoint}?model=${encodeURIComponent(model)}`, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify({
          task_description: taskDescription,
          relevant_norms: relevantNorms,
        }),
        signal: controller.signal,
      });

      await this.logApiCall(endpoint, response.status, 0);

      if (!response.ok) {
        if (response.status === 500) {
          throw new Error('SERVER_ERROR');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse<ProposalEntry> = await response.json();
      await this.logApiCall(endpoint, response.status, JSON.stringify(data).length);
      
      return data.entries || [];
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error('REQUEST_CANCELLED');
      }
      console.error('Error generating proposals:', error);
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  async evaluateProposals(
    taskDescription: string,
    relevantNorms: NormEntry[],
    amendmentProposals: ProposalEntry[],
    apiKey: string,
    model: string
  ): Promise<EvaluatedProposal[]> {
    const requestId = 'evaluate-proposals';
    const controller = this.createAbortableRequest(requestId);
    const endpoint = `${BACKEND_URL}/evaluate_proposals`;
    
    try {
      const response = await fetch(`${endpoint}?model=${encodeURIComponent(model)}`, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify({
          task_description: taskDescription,
          relevant_norms: relevantNorms,
          amendment_proposals: amendmentProposals,
        }),
        signal: controller.signal,
      });

      await this.logApiCall(endpoint, response.status, 0);

      if (!response.ok) {
        if (response.status === 500) {
          throw new Error('SERVER_ERROR');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse<EvaluatedProposal> = await response.json();
      await this.logApiCall(endpoint, response.status, JSON.stringify(data).length);
      
      return data.entries || [];
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error('REQUEST_CANCELLED');
      }
      console.error('Error evaluating proposals:', error);
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  async deepEvaluateProposal(
    taskDescription: string,
    relevantNorms: NormEntry[],
    amendmentProposal: ProposalEntry,
    apiKey: string,
    model: string
  ): Promise<DeepEvaluation | null> {
    const requestId = 'deep-evaluate';
    const controller = this.createAbortableRequest(requestId);
    const endpoint = `${BACKEND_URL}/deep_evaluate_proposals`;
    
    try {
      const response = await fetch(`${endpoint}?model=${encodeURIComponent(model)}`, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify({
          task_description: taskDescription,
          relevant_norms: relevantNorms,
          amendment_proposal: amendmentProposal,
        }),
        signal: controller.signal,
      });

      await this.logApiCall(endpoint, response.status, 0);

      if (!response.ok) {
        if (response.status === 500) {
          throw new Error('SERVER_ERROR');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse<DeepEvaluation> = await response.json();
      await this.logApiCall(endpoint, response.status, JSON.stringify(data).length);
      
      return data.entries && data.entries.length > 0 ? data.entries[0] : null;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error('REQUEST_CANCELLED');
      }
      console.error('Error performing deep evaluation:', error);
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  async generateFinalAmendment(
    taskDescription: string,
    selectedProposal: ProposalEntry | EvaluatedProposal,
    relevantNorms: NormEntry[],
    apiKey: string,
    model: string,
    customAdjustments?: string,
    originalProposals?: ProposalEntry[]
  ): Promise<{ originalNorm: NormEntry; amendedNorm: NormEntry }[]> {
    const requestId = 'final-amendment';
    const controller = this.createAbortableRequest(requestId);
    const endpoint = `${BACKEND_URL}/amend`;
    
    // Convert proposal to the expected format
    let description = '';
    if ('description' in selectedProposal) {
      description = selectedProposal.description;
    } else if (originalProposals) {
      // Find the original proposal by title to get the description
      const originalProposal = originalProposals.find(p => p.proposalTitle === selectedProposal.proposalTitle);
      description = originalProposal?.description || '';
    }
    
    const proposalEntry = {
      proposalTitle: selectedProposal.proposalTitle,
      description: description,
      affectedNorms: selectedProposal.affectedNorms,
    };
    
    try {
      const response = await fetch(`${endpoint}?model=${encodeURIComponent(model)}`, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify({
          task_description: taskDescription,
          custom_instructions: customAdjustments,
          relevant_norms: relevantNorms,
          amendment_proposal: proposalEntry,
        }),
        signal: controller.signal,
      });

      await this.logApiCall(endpoint, response.status, 0);

      if (!response.ok) {
        if (response.status === 500) {
          throw new Error('SERVER_ERROR');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse<{ originalNorm: NormEntry; amendedNorm: NormEntry }> = await response.json();
      await this.logApiCall(endpoint, response.status, JSON.stringify(data).length);
      
      return data.entries || [];
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error('REQUEST_CANCELLED');
      }
      console.error('Error generating final amendment:', error);
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  async generateAenderungsbefehle(
    taskDescription: string,
    finalAmendments: { originalNorm: any; amendedNorm: any }[],
    apiKey: string,
    model: string
  ): Promise<{ response: string }> {
    const requestId = 'aenderungsbefehle';
    const controller = this.createAbortableRequest(requestId);
    const endpoint = `${BACKEND_URL}/generate_aenderungsbefehle`;
    
    try {
      const response = await fetch(`${endpoint}?model=${encodeURIComponent(model)}`, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify({
          task_description: taskDescription,
          final_amendments: finalAmendments,
        }),
        signal: controller.signal,
      });

      await this.logApiCall(endpoint, response.status, 0);

      if (!response.ok) {
        if (response.status === 500) {
          throw new Error('SERVER_ERROR');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      await this.logApiCall(endpoint, response.status, JSON.stringify(data).length);
      
      return data;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error('REQUEST_CANCELLED');
      }
      console.error('Error generating Änderungsbefehle:', error);
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  async generateEntwurfContent(
    taskDescription: string,
    aenderungsbefehle: string,
    apiKey: string,
    model: string,
    finalAmendments?: AmendmentEntry[]
  ): Promise<{ response: string }> {
    const requestId = 'entwurf';
    const controller = this.createAbortableRequest(requestId);
    const endpoint = `${BACKEND_URL}/generate_entwurf`;
    
    try {
      const response = await fetch(`${endpoint}?model=${encodeURIComponent(model)}`, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify({
          task_description: taskDescription,
          aenderungsbefehle: aenderungsbefehle,
          final_amendments: finalAmendments || null,
        }),
        signal: controller.signal,
      });

      await this.logApiCall(endpoint, response.status, 0);

      if (!response.ok) {
        if (response.status === 500) {
          throw new Error('SERVER_ERROR');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      await this.logApiCall(endpoint, response.status, JSON.stringify(data).length);
      
      return data;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw new Error('REQUEST_CANCELLED');
      }
      console.error('Error generating Entwurf content:', error);
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }
}

export const apiClient = new ApiClient();