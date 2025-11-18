"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Message, Artifact } from "@/lib/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Send,
  CheckCircle2,
  Circle,
  Play,
  Loader2,
  XCircle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatPanelProps {
  messages: Message[];
  loading: boolean;
  onSendMessage: (content: string) => void;
  onExecuteArtifact: () => void;
  currentArtifact: Artifact | null;
  executingActions: number[];
  completedActions?: number[];
  failedActions?: number[];
  createdFiles?: Set<string>;
}

export function ChatPanel({
  messages,
  loading,
  onSendMessage,
  onExecuteArtifact,
  currentArtifact,
  executingActions,
  completedActions = [],
  failedActions = [],
  createdFiles = new Set(),
}: ChatPanelProps) {
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    if (!input.trim() || loading) return;
    onSendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="h-14 border-b flex items-center px-4 shrink-0">
        <Link href="/" className="cursor-pointer">
          <img src="/logo1.png" alt="CodeForge" className="h-7 w-auto" />
        </Link>
      </header>
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-4 p-4">
            {messages.map((message, index) => (
              <div key={index} className="space-y-2">
                <div
                  className={`flex ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      message.role === "user"
                        ? "bg-[#e8e4d9] text-black/80"
                        : "bg-white"
                    }`}
                  >
                    {message.role === "user" ? (
                      <p className="text-base whitespace-pre-wrap">
                        {message.content}
                      </p>
                    ) : (
                      <div className="prose prose-base dark:prose-invert max-w-none [&_ul]:list-disc [&_ul]:ml-4 [&_ol]:list-decimal [&_ol]:ml-4 [&_li]:my-1 [&_p]:my-2 [&_h1]:text-xl [&_h1]:font-bold [&_h2]:text-lg [&_h2]:font-semibold [&_h3]:text-base [&_h3]:font-semibold [&_strong]:font-bold">
                        {/* Extract only text before artifact tag */}
                        {(() => {
                          const artifactMatch =
                            message.content.match(/<artifact[\s\S]*$/);
                          const textOnly = artifactMatch
                            ? message.content
                                .substring(0, artifactMatch.index)
                                .trim()
                            : message.content;

                          return (
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                // Disable code blocks - code is shown in artifact section
                                code(props) {
                                  const {
                                    node,
                                    inline,
                                    className,
                                    children,
                                    ...rest
                                  } = props as any;
                                  // Don't render code blocks at all
                                  if (!inline) {
                                    return null;
                                  }
                                  // Keep inline code
                                  return (
                                    <code className={className} {...rest}>
                                      {children}
                                    </code>
                                  );
                                },
                              }}
                            >
                              {textOnly}
                            </ReactMarkdown>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                </div>

                {/* Show artifact plan if exists */}
                {message.artifact && (
                  <div className="pl-4">
                    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                      {message.artifact.actions.map((action, actionIndex) => {
                        const isExecuting =
                          executingActions.includes(actionIndex);
                        const isFailed = failedActions.includes(actionIndex);
                        const isCompleted =
                          completedActions.includes(actionIndex);

                        return (
                          <div key={actionIndex}>
                            {actionIndex > 0 && (
                              <div className="border-t border-gray-200" />
                            )}
                            <div className="flex items-start gap-2.5 text-base px-4 py-3 hover:bg-gray-50 transition-colors cursor-pointer">
                              {isFailed ? (
                                <XCircle className="h-5 w-5 text-red-600 mt-0.5 shrink-0" />
                              ) : isExecuting ? (
                                <Loader2 className="h-5 w-5 text-blue-600 mt-0.5 shrink-0 animate-spin" />
                              ) : isCompleted ? (
                                <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5 shrink-0" />
                              ) : (
                                <Circle className="h-5 w-5 text-gray-400 mt-0.5 shrink-0" />
                              )}
                              <div className="flex-1">
                                {action.type === "file" ? (
                                  <span>
                                    {createdFiles.has(action.filePath || "")
                                      ? "Update"
                                      : "Create"}{" "}
                                    file:{" "}
                                    <code className="text-sm font-mono">
                                      {action.filePath}
                                    </code>
                                  </span>
                                ) : (
                                  <span>
                                    Run:{" "}
                                    <code className="text-sm font-mono">
                                      {action.command}
                                    </code>
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-lg px-4 py-2">
                  <div className="flex items-center gap-2">
                    <div
                      className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <div
                      className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <div
                      className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Input */}
      <div className="border-t p-4 shrink-0">
        <div className="flex gap-2 bg-white rounded-2xl border border-gray-300/80 px-4 py-3 items-end">
          <Textarea
            placeholder="Describe what you want to build or modify..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            className="min-h-[60px] max-h-[200px] border-0 p-0 resize-none focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-gray-400 shadow-none"
          />
          <Button
            onClick={handleSubmit}
            disabled={!input.trim() || loading}
            size="icon"
            className="h-10 w-10 rounded-lg bg-[#c6623f] hover:bg-[#ce623ad7] text-white shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
