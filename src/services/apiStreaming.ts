/**
 * API Streaming Service - Gestion des conversations en streaming
 * 
 * Ce service gère la connexion à l'API de streaming pour les conversations.
 * Il envoie les requêtes au serveur et traite les événements SSE en temps réel.
 */

export interface StreamEvent {
  id: string;
  type: 'connection' | 'log' | 'message' | 'final_response';
  timestamp: string;
  display?: string;
  data: any;
  full_content?: string;
}

export interface StreamingOptions {
  prompt: string;
  model: string;
  max_turns: number;
}

export class APIStreamingService {
  private readonly baseUrl = 'https://20.246.67.213:8000/api/v1/query/stream';
  private currentController: AbortController | null = null;

  async streamQuery(
    options: StreamingOptions,
    onEvent: (event: StreamEvent) => void,
    onComplete: (finalResponse?: string) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    // Annuler la requête précédente si elle existe
    if (this.currentController) {
      this.currentController.abort();
    }

    this.currentController = new AbortController();

    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
        signal: this.currentController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No response body received');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let finalResponse = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim() === '') continue;

            if (line.startsWith('event:')) {
              // On attend la ligne de données suivante
              continue;
            }

            if (line.startsWith('data:')) {
              try {
                const dataContent = line.slice(5).trim();
                if (dataContent === '') continue;

                const eventData = JSON.parse(dataContent);
                
                const streamEvent: StreamEvent = {
                  id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
                  type: this.determineEventType(eventData),
                  timestamp: new Date().toISOString(),
                  display: eventData.display || this.formatEventDisplay(eventData),
                  data: eventData,
                  full_content: eventData.full_content
                };

                // Capturer la réponse finale
                if (eventData.full_content && streamEvent.type === 'message') {
                  finalResponse = eventData.full_content;
                }

                onEvent(streamEvent);
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', parseError, line);
              }
            }
          }
        }

        onComplete(finalResponse);
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request was aborted');
        return;
      }
      onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    } finally {
      this.currentController = null;
    }
  }

  private determineEventType(data: any): StreamEvent['type'] {
    if (data.status === 'connected') {
      return 'connection';
    }
    if (data.type) {
      if (data.type === 'assistant_message' && data.full_content) {
        return 'message';
      }
      return 'log';
    }
    if (data.full_content) {
      return 'final_response';
    }
    return 'log';
  }

  private formatEventDisplay(data: any): string {
    if (data.status === 'connected') {
      return `🔗 Connexion établie (ID: ${data.client_id?.slice(0, 8)}...)`;
    }
    if (data.display) {
      return data.display;
    }
    if (data.type) {
      return `📝 ${data.type}: ${JSON.stringify(data.details || {}).slice(0, 50)}...`;
    }
    return `📋 Événement: ${JSON.stringify(data).slice(0, 100)}...`;
  }

  abort(): void {
    if (this.currentController) {
      this.currentController.abort();
      this.currentController = null;
    }
  }
}

export const apiStreamingService = new APIStreamingService();