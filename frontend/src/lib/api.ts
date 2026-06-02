import { NormEntry, ProposalEntry, EvaluatedProposal, DeepEvaluation, Model, ApiResponse, AmendmentEntry } from '@/types';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export interface StreamCallbacks {
  onThinking?: (token: string) => void;
  onStep?: (stepIndex: number, message: string) => void;
}

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

  /**
   * Generic SSE consumer. Parses thinking, step, result, and error events.
   * Returns the result data from the "result" event.
   */
  private async consumeSSE<T>(
    response: Response,
    callbacks?: StreamCallbacks,
  ): Promise<T> {
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';
    let result: T | null = null;
    let errorMessage: string | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = '';
      let currentData = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          currentData = line.slice(6);
        } else if (line === '' && currentEvent && currentData) {
          try {
            const parsed = JSON.parse(currentData);
            if (currentEvent === 'thinking' && callbacks?.onThinking) {
              callbacks.onThinking(parsed.token);
            } else if (currentEvent === 'step' && callbacks?.onStep) {
              callbacks.onStep(parsed.step, parsed.message);
            } else if (currentEvent === 'result') {
              result = (parsed.entries ?? parsed.response ?? parsed) as T;
            } else if (currentEvent === 'error') {
              errorMessage = parsed.message;
            }
          } catch (e) {
            console.error('Error parsing SSE event:', e);
          }
          currentEvent = '';
          currentData = '';
        }
      }
    }

    if (errorMessage) throw new Error(errorMessage);
    if (result === null) throw new Error('No result received from stream');
    return result;
  }

  /**
   * Execute a streaming POST request and consume SSE events.
   */
  private async streamRequest<T>(
    requestId: string,
    streamEndpoint: string,
    body: Record<string, unknown>,
    apiKey: string,
    model: string,
    callbacks?: StreamCallbacks,
  ): Promise<T> {
    const controller = this.createAbortableRequest(requestId);
    const url = `${BACKEND_URL}/stream/${streamEndpoint}?model=${encodeURIComponent(model)}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        if (response.status === 500) throw new Error('SERVER_ERROR');
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await this.consumeSSE<T>(response, callbacks);
    } catch (error: any) {
      if (error.name === 'AbortError') throw new Error('REQUEST_CANCELLED');
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  /**
   * Execute a standard (non-streaming) POST request.
   */
  private async standardRequest<T>(
    requestId: string,
    endpoint: string,
    body: Record<string, unknown>,
    apiKey: string,
    model: string,
  ): Promise<T> {
    const controller = this.createAbortableRequest(requestId);
    const url = `${BACKEND_URL}/${endpoint}?model=${encodeURIComponent(model)}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: this.getHeaders(apiKey),
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        if (response.status === 500) throw new Error('SERVER_ERROR');
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === 'AbortError') throw new Error('REQUEST_CANCELLED');
      throw error;
    } finally {
      this.abortControllers.delete(requestId);
    }
  }

  async fetchModels(apiKey: string): Promise<{ models: Model[]; default: string | null }> {
    try {
      const response = await fetch(`${BACKEND_URL}/models`, {
        headers: this.getHeaders(apiKey),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { models: data.models || [], default: data.default || null };
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
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { organized: data.organized || {}, default: data.default || null };
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
    selectedLaws: string[] = [],
    callbacks?: StreamCallbacks,
  ): Promise<NormEntry[]> {
    const body: Record<string, unknown> = { task_description: taskDescription };
    if (selectedLaws.length > 0) body.selected_laws = selectedLaws;

    if (callbacks?.onThinking) {
      const endpoint = multistepReasoning ? 'identify_multistep' : 'identify';
      return this.streamRequest<NormEntry[]>('identify-norms', endpoint, body, apiKey, model, callbacks);
    }

    const endpoint = multistepReasoning ? 'identify_multistep' : 'identify';
    const data = await this.standardRequest<ApiResponse<NormEntry>>('identify-norms', endpoint, body, apiKey, model);
    return data.entries || [];
  }

  async generateProposals(
    taskDescription: string,
    relevantNorms: NormEntry[],
    apiKey: string,
    model: string,
    callbacks?: StreamCallbacks,
  ): Promise<ProposalEntry[]> {
    const body = { task_description: taskDescription, relevant_norms: relevantNorms };

    if (callbacks?.onThinking) {
      return this.streamRequest<ProposalEntry[]>('generate-proposals', 'generate_proposals', body, apiKey, model, callbacks);
    }

    const data = await this.standardRequest<ApiResponse<ProposalEntry>>('generate-proposals', 'generate_proposals', body, apiKey, model);
    return data.entries || [];
  }

  async evaluateProposals(
    taskDescription: string,
    relevantNorms: NormEntry[],
    amendmentProposals: ProposalEntry[],
    apiKey: string,
    model: string,
    callbacks?: StreamCallbacks,
  ): Promise<EvaluatedProposal[]> {
    const body = {
      task_description: taskDescription,
      relevant_norms: relevantNorms,
      amendment_proposals: amendmentProposals,
    };

    if (callbacks?.onThinking) {
      return this.streamRequest<EvaluatedProposal[]>('evaluate-proposals', 'evaluate_proposals', body, apiKey, model, callbacks);
    }

    const data = await this.standardRequest<ApiResponse<EvaluatedProposal>>('evaluate-proposals', 'evaluate_proposals', body, apiKey, model);
    return data.entries || [];
  }

  async deepEvaluateProposal(
    taskDescription: string,
    relevantNorms: NormEntry[],
    amendmentProposal: ProposalEntry,
    apiKey: string,
    model: string,
    callbacks?: StreamCallbacks,
  ): Promise<DeepEvaluation | null> {
    const body = {
      task_description: taskDescription,
      relevant_norms: relevantNorms,
      amendment_proposal: amendmentProposal,
    };

    if (callbacks?.onThinking) {
      const entries = await this.streamRequest<DeepEvaluation[]>('deep-evaluate', 'deep_evaluate_proposals', body, apiKey, model, callbacks);
      return entries && entries.length > 0 ? entries[0] : null;
    }

    const data = await this.standardRequest<ApiResponse<DeepEvaluation>>('deep-evaluate', 'deep_evaluate_proposals', body, apiKey, model);
    return data.entries && data.entries.length > 0 ? data.entries[0] : null;
  }

  async generateFinalAmendment(
    taskDescription: string,
    selectedProposal: ProposalEntry | EvaluatedProposal,
    relevantNorms: NormEntry[],
    apiKey: string,
    model: string,
    customAdjustments?: string,
    originalProposals?: ProposalEntry[],
    callbacks?: StreamCallbacks,
  ): Promise<{ originalNorm: NormEntry; amendedNorm: NormEntry }[]> {
    let description = '';
    if ('description' in selectedProposal) {
      description = selectedProposal.description;
    } else if (originalProposals) {
      const originalProposal = originalProposals.find(p => p.proposalTitle === selectedProposal.proposalTitle);
      description = originalProposal?.description || '';
    }

    const body = {
      task_description: taskDescription,
      custom_instructions: customAdjustments,
      relevant_norms: relevantNorms,
      amendment_proposal: {
        proposalTitle: selectedProposal.proposalTitle,
        description,
        affectedNorms: selectedProposal.affectedNorms,
      },
    };

    if (callbacks?.onThinking) {
      return this.streamRequest<{ originalNorm: NormEntry; amendedNorm: NormEntry }[]>('final-amendment', 'amend', body, apiKey, model, callbacks);
    }

    const data = await this.standardRequest<ApiResponse<{ originalNorm: NormEntry; amendedNorm: NormEntry }>>('final-amendment', 'amend', body, apiKey, model);
    return data.entries || [];
  }

  async generateAenderungsbefehle(
    taskDescription: string,
    finalAmendments: { originalNorm: any; amendedNorm: any }[],
    apiKey: string,
    model: string,
    callbacks?: StreamCallbacks,
  ): Promise<{ response: string }> {
    const body = { task_description: taskDescription, final_amendments: finalAmendments };

    if (callbacks?.onThinking) {
      const response = await this.streamRequest<string>('aenderungsbefehle', 'generate_aenderungsbefehle', body, apiKey, model, callbacks);
      return { response };
    }

    return this.standardRequest<{ response: string }>('aenderungsbefehle', 'generate_aenderungsbefehle', body, apiKey, model);
  }

  async generateEntwurfContent(
    taskDescription: string,
    aenderungsbefehle: string,
    apiKey: string,
    model: string,
    finalAmendments?: AmendmentEntry[],
    callbacks?: StreamCallbacks,
  ): Promise<{ response: string }> {
    const body = {
      task_description: taskDescription,
      aenderungsbefehle,
      final_amendments: finalAmendments || null,
    };

    if (callbacks?.onThinking) {
      const response = await this.streamRequest<string>('entwurf', 'generate_entwurf', body, apiKey, model, callbacks);
      return { response };
    }

    return this.standardRequest<{ response: string }>('entwurf', 'generate_entwurf', body, apiKey, model);
  }
}

export const apiClient = new ApiClient();
