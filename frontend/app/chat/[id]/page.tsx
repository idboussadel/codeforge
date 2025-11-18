"use client";

import { useState, useEffect, use } from "react";
import { APIClient } from "@/lib/api";
import { Message, Artifact, ModelProvider } from "@/lib/types";
import { ChatPanel } from "@/components/chat-panel";
import { PreviewPanel } from "@/components/preview-panel";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";

export default function ChatPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: sessionId } = use(params);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentArtifact, setCurrentArtifact] = useState<Artifact | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [executingActions, setExecutingActions] = useState<number[]>([]);
  const [completedActions, setCompletedActions] = useState<number[]>([]);
  const [failedActions, setFailedActions] = useState<number[]>([]);
  const [createdFiles, setCreatedFiles] = useState<Set<string>>(new Set());
  const [modelProvider, setModelProvider] = useState<ModelProvider>("gpt");

  useEffect(() => {
    // Get initial prompt and model from sessionStorage
    const initialPrompt = sessionStorage.getItem(`prompt-${sessionId}`);
    const storedModel = sessionStorage.getItem(
      `model-${sessionId}`
    ) as ModelProvider;

    if (storedModel) {
      setModelProvider(storedModel);
    }

    if (initialPrompt) {
      // Pass the stored model directly to avoid React state timing issue
      handleSendMessage(initialPrompt, storedModel || "gpt");
      sessionStorage.removeItem(`prompt-${sessionId}`);
      sessionStorage.removeItem(`model-${sessionId}`);
    }
  }, [sessionId]);

  const handleSendMessage = async (
    content: string,
    overrideModel?: ModelProvider
  ) => {
    if (!content.trim() || loading) return;

    // Add user message
    const userMessage: Message = { role: "user", content };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      // Get conversation history for API
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      // Call API - use overrideModel if provided (for initial call), otherwise use state
      const response = await APIClient.generate(
        content,
        history,
        overrideModel || modelProvider
      );

      // Add assistant message
      const assistantMessage: Message = {
        role: "assistant",
        content: response.content,
        artifact: response.artifact || undefined,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Update current artifact
      if (response.artifact) {
        setCurrentArtifact(response.artifact);
        // Auto-execute artifact after a brief delay
        setTimeout(() => {
          handleExecuteArtifact(response.artifact || undefined);
        }, 500);
      }
    } catch (error) {
      console.error("Error generating response:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: `Error: ${
          error instanceof Error ? error.message : "Failed to generate response"
        }`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteArtifact = async (artifact?: Artifact) => {
    const artifactToExecute = artifact || currentArtifact;
    if (!artifactToExecute) return;

    // Only reset executing actions, preserve completed/failed states
    setExecutingActions([]);

    try {
      // Execute with real-time progress updates
      const response = await APIClient.execute(
        sessionId,
        artifactToExecute.actions,
        (actionIndex, status, result) => {
          // Update UI as each action progresses
          if (status === "executing" || status === "waiting_for_server") {
            setExecutingActions((prev) => {
              if (!prev.includes(actionIndex)) {
                return [...prev, actionIndex];
              }
              return prev;
            });
          } else if (status === "completed") {
            // Remove from executing
            setExecutingActions((prev) =>
              prev.filter((i) => i !== actionIndex)
            );

            // Check if command failed
            if (result?.status === "failed") {
              console.error(`Action ${actionIndex} failed:`, result.error);
              setFailedActions((prev) => [...prev, actionIndex]);
            } else {
              // Mark as successfully completed
              setCompletedActions((prev) => [...prev, actionIndex]);

              // Track created/updated files
              const action = artifactToExecute.actions[actionIndex];
              if (action.type === "file" && action.filePath) {
                setCreatedFiles((prev) => new Set([...prev, action.filePath!]));
              }
            }
          }
        }
      );

      setPreviewUrl(response.preview_url);
      setExecutingActions([]); // Clear executing when done
    } catch (error) {
      console.error("Error executing artifact:", error);
      // Don't clear completedActions or failedActions - preserve the state
      setExecutingActions([]);
    }
  };

  return (
    <div className="h-screen">
      {/* Main Content - Split View */}
      <ResizablePanelGroup direction="horizontal" className="h-full">
        {/* Left Panel - Chat */}
        <ResizablePanel defaultSize={50} minSize={30}>
          <ChatPanel
            messages={messages}
            loading={loading}
            onSendMessage={handleSendMessage}
            onExecuteArtifact={handleExecuteArtifact}
            currentArtifact={currentArtifact}
            executingActions={executingActions}
            completedActions={completedActions}
            failedActions={failedActions}
            createdFiles={createdFiles}
          />
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Right Panel - Preview */}
        <ResizablePanel defaultSize={50} minSize={30}>
          <PreviewPanel
            artifact={currentArtifact}
            previewUrl={previewUrl}
            sessionId={sessionId}
            messages={messages}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
