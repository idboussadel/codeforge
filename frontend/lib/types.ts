export interface Action {
  type: "file" | "shell";
  filePath?: string;
  content?: string;
  command?: string;
}

export interface Artifact {
  id: string;
  title: string;
  actions: Action[];
}

export interface GenerateResponse {
  content: string;
  artifact: Artifact | null;
}

export interface ExecuteResponse {
  results: any[];
  preview_url: string | null;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  artifact?: Artifact;
}

export type ModelProvider = "gpt" | "claude";
