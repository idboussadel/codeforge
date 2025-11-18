import { GenerateResponse, ExecuteResponse, Action } from "./types";

const API_BASE_URL = "http://localhost:8000";

export class APIClient {
  static async generate(
    prompt: string,
    conversationHistory: any[] = [],
    modelProvider: "gpt" | "claude" = "gpt"
  ): Promise<GenerateResponse> {
    const response = await fetch(`${API_BASE_URL}/api/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt,
        conversation_history: conversationHistory,
        model_provider: modelProvider,
      }),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  static async execute(
    sessionId: string,
    actions: Action[],
    onProgress?: (actionIndex: number, status: string, result?: any) => void
  ): Promise<ExecuteResponse> {
    const response = await fetch(`${API_BASE_URL}/api/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        actions,
      }),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    // Handle streaming response
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let previewUrl: string | null = null;

    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));

            if (data.type === "progress" && onProgress) {
              onProgress(data.action_index, data.status, data.result);
            } else if (data.type === "complete") {
              previewUrl = data.preview_url;
            } else if (data.type === "error") {
              throw new Error(data.message);
            }
          }
        }
      }
    }

    return {
      results: [],
      preview_url: previewUrl,
    };
  }
}
