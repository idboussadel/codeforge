"use client";

import { useState, useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Loader2, Terminal as TerminalIcon, X } from "lucide-react";

interface TerminalProps {
  sessionId: string | null;
}

interface TerminalLine {
  type: "input" | "output" | "error";
  content: string;
}

export function Terminal({ sessionId }: TerminalProps) {
  const [input, setInput] = useState("");
  const [currentDir, setCurrentDir] = useState("/home/user");
  const [lines, setLines] = useState<TerminalLine[]>([
    {
      type: "output",
      content: "Terminal ready. Type commands to execute in the sandbox.",
    },
  ]);
  const [executing, setExecuting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new lines are added
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines]);

  const executeCommand = async (command: string) => {
    if (!sessionId || !command.trim()) return;

    // Show current directory in prompt
    const displayDir =
      currentDir === "/home/user" ? "~" : currentDir.replace("/home/user", "~");

    // Add input line
    setLines((prev) => [
      ...prev,
      { type: "input", content: `${displayDir} $ ${command}` },
    ]);
    setInput("");
    setExecuting(true);

    try {
      const response = await fetch("http://localhost:8000/api/terminal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          command: command.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update current directory if changed
      if (data.cwd) {
        setCurrentDir(data.cwd);
      }

      // Add output
      if (data.stdout) {
        setLines((prev) => [...prev, { type: "output", content: data.stdout }]);
      }

      if (data.stderr) {
        setLines((prev) => [...prev, { type: "error", content: data.stderr }]);
      }

      if (!data.stdout && !data.stderr && data.exit_code === 0) {
        // Don't show anything for successful silent commands like cd
      }
    } catch (error) {
      setLines((prev) => [
        ...prev,
        {
          type: "error",
          content: `Error: ${
            error instanceof Error ? error.message : "Command failed"
          }`,
        },
      ]);
    } finally {
      setExecuting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !executing) {
      executeCommand(input);
    }
  };

  const clearTerminal = () => {
    setLines([
      {
        type: "output",
        content: "Terminal cleared.",
      },
    ]);
  };

  return (
    <div className="flex flex-col h-full bg-white overflow-hidden">
      {/* Output */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div ref={scrollRef} className="p-3 font-mono text-sm">
            {lines.map((line, index) => (
              <div
                key={index}
                className={`${
                  line.type === "input"
                    ? "text-green-600"
                    : line.type === "error"
                    ? "text-red-600"
                    : "text-gray-800"
                } whitespace-pre-wrap break-words`}
              >
                {line.content}
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Input - Fixed at bottom */}
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 border-t border-gray-300 shrink-0">
        <span className="text-blue-600 font-mono text-sm">
          {currentDir === "/home/user"
            ? "~"
            : currentDir.replace("/home/user", "~")}
        </span>
        <span className="text-green-600 font-mono text-sm">$</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={executing || !sessionId}
          placeholder={
            sessionId ? "Type a command..." : "Execute artifact first..."
          }
          className="flex-1 bg-transparent text-gray-800 font-mono text-sm outline-none disabled:opacity-50 placeholder:text-gray-400"
        />
        {executing && (
          <Loader2 className="h-4 w-4 text-gray-600 animate-spin" />
        )}
      </div>
    </div>
  );
}
