/**
 * API Streaming Service - Gestion des conversations en streaming
 * 
 * Ce service gère la connexion à l'API de streaming pour les conversations.
 * Il envoie les requêtes au serveur et traite les événements SSE en temps réel.
 */

export interface StreamEventData {
  status?: string;
  client_id?: string;
  type?: string;
  details?: Record<string, unknown>;
  display?: string;
  full_content?: string;
  user_message?: string;
  error?: string;
  session_id?: string;
  response?: string;
  // Fichiers et pièces jointes renvoyés dans l'événement "response"
  attachments?: Array<{
    path: string;
    absolute_path?: string;
    size?: number;
    modified?: string;
    is_new?: boolean;
    is_updated?: boolean;
  }>;
  new_files?: string[];
  updated_files?: string[];
  file_changes_summary?: {
    total_files?: number;
    new_count?: number;
    updated_count?: number;
  };
  [key: string]: unknown;
}

export interface StreamEvent {
  id: string;
  type: "connection" | "log" | "message" | "final_response";
  timestamp: string;
  display?: string;
  data: StreamEventData;
  full_content?: string;
}

export interface StreamingOptions {
  prompt: string;
  model: string;
  max_turns: number;
  session_id?: string;
}

export class APIStreamingService {
  private readonly baseUrl = `${
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"
  }/query/stream`;
  private currentController: AbortController | null = null;
  private currentSessionId: string | null = null;

  getCurrentSessionId(): string | null {
    return this.currentSessionId;
  }

  async streamQuery(
    options: StreamingOptions,
    onEvent: (event: StreamEvent) => void,
    onComplete: (finalResponse?: string, sessionId?: string) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    // Annuler la requête précédente si elle existe
    if (this.currentController) {
      this.currentController.abort();
    }

    this.currentController = new AbortController();

    try {
      const response = await fetch(this.baseUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(options),
        signal: this.currentController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("No response body received");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalResponse = "";
      let capturedSessionId: string | null = null;

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.trim() === "") continue;

            if (line.startsWith("event:")) {
              // On attend la ligne de données suivante
              continue;
            }

            if (line.startsWith("data:")) {
              try {
                const dataContent = line.slice(5).trim();
                if (dataContent === "") continue;

                const eventData = JSON.parse(dataContent);

                const streamEvent: StreamEvent = {
                  id:
                    Date.now().toString() +
                    Math.random().toString(36).substr(2, 9),
                  type: this.determineEventType(eventData),
                  timestamp: new Date().toISOString(),
                  display:
                    eventData.display || this.formatEventDisplay(eventData),
                  data: eventData,
                  full_content: eventData.full_content,
                };

                // Capturer la réponse finale et le session_id
                if (eventData.full_content && streamEvent.type === "message") {
                  finalResponse = eventData.full_content;
                }

                // Capturer le session_id quand il est présent dans la réponse
                if (eventData.session_id) {
                  capturedSessionId = eventData.session_id;
                  this.currentSessionId = capturedSessionId;
                  console.log("Session ID capturé:", capturedSessionId);
                }

                // Capturer aussi depuis le champ response si c'est la réponse finale
                if (eventData.response && eventData.session_id) {
                  finalResponse = eventData.response;
                  capturedSessionId = eventData.session_id;
                  this.currentSessionId = capturedSessionId;
                  console.log(
                    "Réponse finale avec Session ID:",
                    capturedSessionId
                  );
                }

                onEvent(streamEvent);
              } catch (parseError) {
                console.warn("Failed to parse SSE data:", parseError, line);
              }
            }
          }
        }

        onComplete(finalResponse, capturedSessionId);
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Request was aborted");
        return;
      }
      onError(
        error instanceof Error ? error : new Error("Unknown streaming error")
      );
    } finally {
      this.currentController = null;
    }
  }

  private determineEventType(data: StreamEventData): StreamEvent["type"] {
    if (data.status === "connected") {
      return "connection";
    }
    if (data.type) {
      if (data.type === "assistant_message" && data.full_content) {
        return "message";
      }
      return "log";
    }
    // Réponse finale : quand on a une réponse complète avec session_id
    if ((data.full_content || data.response) && data.session_id) {
      return "final_response";
    }
    // Message intermédiaire pendant le streaming
    if (data.full_content) {
      return "message";
    }
    return "log";
  }

  private formatEventDisplay(data: StreamEventData): string {
    if (data.status === "connected") {
      return `🔗 Connected (ID: ${data.client_id?.slice(0, 8)}...)`;
    }
    if (data.display) {
      return data.display;
    }
    if (data.type) {
      return `📝 ${data.type}: ${JSON.stringify(data.details || {}).slice(
        0,
        50
      )}...`;
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
