"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sparkles, Bot, ChevronDown } from "lucide-react";
import type { ModelProvider } from "@/lib/types";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [modelProvider, setModelProvider] = useState<ModelProvider>("gpt");
  const router = useRouter();

  const handleSubmit = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    const sessionId = crypto.randomUUID();

    // Store the prompt and model provider in sessionStorage
    sessionStorage.setItem(`prompt-${sessionId}`, prompt);
    sessionStorage.setItem(`model-${sessionId}`, modelProvider);

    // Navigate to chat page
    router.push(`/chat/${sessionId}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden"
      style={{ backgroundColor: "#f5f1ea" }}
    >
      {/* Animated gradient orbs in background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-96 h-96 bg-gradient-to-br from-orange-200/40 to-pink-200/40 rounded-full blur-3xl animate-pulse" />
        <div
          className="absolute bottom-20 right-10 w-96 h-96 bg-gradient-to-br from-blue-200/40 to-purple-200/40 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "1s" }}
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-br from-yellow-200/20 to-orange-200/20 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: "2s" }}
        />
      </div>

      <div className="w-full max-w-4xl space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center space-y-6">
          <div className="flex items-center justify-center">
            <img src="/logo1.png" alt="CodeForge" className="h-28 w-auto" />
          </div>
        </div>

        {/* Prompt Area */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-300/80 px-6 py-4 shadow-xl shadow-gray-200/50">
          <Textarea
            placeholder="What would you like to build?"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            className="min-h-[120px] border-0 !text-base rounded-none resize-none focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-gray-400 p-0 shadow-none bg-transparent"
          />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400 bg-[#e8e4d9b7] border border-[#ada590b7] rounded px-2 py-1">
                ⏎ Enter
              </span>
              <span className="text-sm text-gray-400">to submit</span>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="ml-2 h-8 gap-1 text-xs bg-white border-gray-300 hover:bg-gray-50"
                  >
                    <Bot className="h-3.5 w-3.5" />
                    <span>{modelProvider === "gpt" ? "GPT-4o" : "Claude"}</span>
                    <ChevronDown className="h-3.5 w-3.5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  <DropdownMenuItem
                    onClick={() => setModelProvider("gpt")}
                    className="cursor-pointer"
                  >
                    <Bot className="h-4 w-4 mr-2" />
                    GPT-4o
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setModelProvider("claude")}
                    className="cursor-pointer"
                  >
                    <Bot className="h-4 w-4 mr-2" />
                    Claude 4.5 Sonnet
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim() || loading}
              size="icon"
              className="rounded-full bg-[#c6623f] cursor-pointer hover:bg-[#ce623ad7] text-white h-11 w-11"
            >
              {loading ? (
                <div className="h-5 w-5 border-2 border-gray-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 10l7-7m0 0l7 7m-7-7v18"
                  />
                </svg>
              )}
            </Button>
          </div>
        </div>

        {/* Examples */}
        <div className="flex flex-wrap gap-3 justify-center">
          {[
            { icon: "📺", text: "Build a Netflix clone" },
            { icon: "📦", text: "Build an admin dashboard" },
            { icon: "📋", text: "Build a kanban board" },
            { icon: "📁", text: "Build a file manager" },
            { icon: "📹", text: "Build a YouTube clone" },
            { icon: "🛍️", text: "Build a store page" },
            { icon: "🏡", text: "Build an Airbnb clone" },
            { icon: "🎵", text: "Build a Spotify clone" },
          ].map((example) => (
            <button
              key={example.text}
              onClick={() => setPrompt(example.text)}
              className="px-4 py-2.5 rounded-lg bg-white/80 backdrop-blur-sm border border-gray-200 hover:border-gray-300 transition-all text-sm text-gray-700 flex items-center gap-2 shadow-sm hover:shadow-md hover:bg-[#e8e4d9]"
            >
              <span>{example.icon}</span>
              <span>{example.text}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
