"use client";

import { useState } from "react";
import { Artifact } from "@/lib/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import {
  Code,
  Monitor,
  ChevronRight,
  ChevronDown,
  Folder,
  File,
  Globe,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Terminal } from "@/components/terminal";
import { Message } from "@/lib/types";

interface PreviewPanelProps {
  artifact: Artifact | null;
  previewUrl: string | null;
  sessionId: string;
  messages?: Message[];
}

interface FileNode {
  name: string;
  path: string;
  type: "file" | "folder";
  children?: FileNode[];
  fileIndex?: number;
}

// Build file tree from flat file list
const buildFileTree = (files: any[]): FileNode[] => {
  const root: FileNode[] = [];

  files.forEach((file, index) => {
    const parts = file.filePath.split("/").filter(Boolean);
    let currentLevel = root;

    parts.forEach((part: string, i: number) => {
      const isFile = i === parts.length - 1;
      const existingNode = currentLevel.find((node) => node.name === part);

      if (existingNode) {
        if (!isFile && existingNode.children) {
          currentLevel = existingNode.children;
        } else if (isFile) {
          existingNode.fileIndex = index;
        }
      } else {
        const newNode: FileNode = {
          name: part,
          path: parts.slice(0, i + 1).join("/"),
          type: isFile ? "file" : "folder",
          children: isFile ? undefined : [],
          fileIndex: isFile ? index : undefined,
        };

        currentLevel.push(newNode);

        if (!isFile && newNode.children) {
          currentLevel = newNode.children;
        }
      }
    });
  });

  // Sort function: folders first, then files, alphabetically within each group
  const sortNodes = (nodes: FileNode[]): FileNode[] => {
    return nodes
      .sort((a, b) => {
        if (a.type === b.type) {
          return a.name.localeCompare(b.name);
        }
        return a.type === "folder" ? -1 : 1;
      })
      .map((node) => {
        if (node.children) {
          return { ...node, children: sortNodes(node.children) };
        }
        return node;
      });
  };

  return sortNodes(root);
};

// Get language for syntax highlighting
const getLanguage = (filePath: string) => {
  const ext = filePath.split(".").pop()?.toLowerCase();

  const langMap: Record<string, string> = {
    tsx: "tsx",
    ts: "typescript",
    jsx: "jsx",
    js: "javascript",
    json: "json",
    css: "css",
    html: "html",
    md: "markdown",
  };

  return langMap[ext || ""] || "text";
};

export function PreviewPanel({
  artifact,
  previewUrl,
  sessionId,
  messages = [],
}: PreviewPanelProps) {
  const [selectedFileIndex, setSelectedFileIndex] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<string>("code");
  const [collapsedFolders, setCollapsedFolders] = useState<Set<string>>(
    new Set()
  );

  const toggleFolder = (path: string) => {
    setCollapsedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  // File tree component
  const FileTreeNode = ({
    node,
    depth = 0,
  }: {
    node: FileNode;
    depth?: number;
  }) => {
    const isCollapsed = collapsedFolders.has(node.path);
    const isSelected = node.fileIndex === selectedFileIndex;

    if (node.type === "file") {
      return (
        <button
          onClick={() =>
            node.fileIndex !== undefined && setSelectedFileIndex(node.fileIndex)
          }
          className={`w-full flex items-center gap-1.5 px-2 py-1 rounded text-sm transition-colors ${
            isSelected
              ? "bg-foreground/10  text-black/80"
              : "text-muted-foreground hover:bg-foreground/10 hover:text-foreground"
          }`}
          style={{ paddingLeft: `${depth * 16 + 24}px` }}
        >
          <File className="h-4 w-4 shrink-0" />
          <span className="truncate text-left text-[13px]">{node.name}</span>
        </button>
      );
    }

    return (
      <div>
        <button
          onClick={() => toggleFolder(node.path)}
          className="w-full flex items-center gap-1.5 px-2 py-1 rounded text-sm transition-colors text-muted-foreground hover:bg-foreground/10 hover:text-foreground"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {isCollapsed ? (
            <ChevronRight className="h-3.5 w-3.5 shrink-0" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5 shrink-0" />
          )}
          <Folder className="h-4 w-4 shrink-0 text-[#797467]" />
          <span className="truncate text-left text-[13px]">{node.name}</span>
        </button>
        {!isCollapsed && node.children && (
          <div className="space-y-0.5">
            {node.children.map((child, i) => (
              <FileTreeNode key={i} node={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  if (!artifact) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground bg-background">
        <div className="text-center space-y-2">
          <Monitor className="h-12 w-12 mx-auto opacity-20" />
          <p className="font-medium">No preview available</p>
          <p className="text-sm">Start building to see your app here</p>
        </div>
      </div>
    );
  }

  // Collect ALL file actions from ALL messages (later messages override earlier ones)
  const allFileActions: any[] = [];
  const fileMap = new Map<string, any>();

  messages.forEach((message) => {
    if (message.artifact?.actions) {
      message.artifact.actions
        .filter((action) => action.type === "file")
        .forEach((action) => {
          fileMap.set(action.filePath || "", action);
        });
    }
  });

  // Convert map back to array
  fileMap.forEach((action) => allFileActions.push(action));

  // If we have no files at all, show empty state
  if (allFileActions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground bg-background">
        <div className="text-center space-y-2">
          <Monitor className="h-12 w-12 mx-auto opacity-20" />
          <p className="font-medium">No files yet</p>
          <p className="text-sm">Files will appear here as they're created</p>
        </div>
      </div>
    );
  }

  const fileTree = buildFileTree(allFileActions);

  return (
    <div className="h-full flex flex-col bg-background overflow-hidden">
      <Tabs
        defaultValue="code"
        value={activeTab}
        onValueChange={setActiveTab}
        className="flex-1 flex flex-col overflow-hidden"
      >
        <div className="h-14 border-b px-4 flex items-center shrink-0">
          <TabsList>
            <TabsTrigger value="code" className="gap-2">
              <Code className="h-4 w-4" />
              Code
            </TabsTrigger>
            <TabsTrigger value="demo" className="gap-2">
              <Monitor className="h-4 w-4" />
              Demo
            </TabsTrigger>
          </TabsList>
        </div>

        {/* URL Display - Only shown when demo tab is active */}
        {activeTab === "demo" && previewUrl && (
          <div className="border-b px-4 py-3 bg-muted/30 shrink-0">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-sm">
                <Globe className="h-4 w-4 text-gray-500 shrink-0" />
                <span className="text-sm font-mono text-gray-700 truncate flex-1">
                  {previewUrl}
                </span>
              </div>
              <button
                onClick={() => {
                  const iframe = document.querySelector(
                    'iframe[src="' + previewUrl + '"]'
                  ) as HTMLIFrameElement;
                  if (iframe) {
                    iframe.src = iframe.src;
                  }
                }}
                className="flex items-center justify-center h-9 w-9 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
                title="Reload preview"
              >
                <RefreshCw className="h-4 w-4 text-gray-600" />
              </button>
              <a
                href={previewUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center h-9 w-9 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
                title="Open in new tab"
              >
                <ExternalLink className="h-4 w-4 text-gray-600" />
              </a>
            </div>
          </div>
        )}

        <TabsContent value="code" className="flex-1 m-0 flex overflow-hidden">
          {/* File Explorer Sidebar */}
          <div className="w-64 border-r bg-muted/30 flex flex-col overflow-hidden">
            <div className="px-3 py-2 border-b bg-muted/50 shrink-0">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Files
              </span>
            </div>
            <ScrollArea className="flex-1 h-full">
              <div className="p-2">
                <div className="space-y-0.5">
                  {fileTree.map((node, i) => (
                    <FileTreeNode key={i} node={node} depth={0} />
                  ))}
                </div>
              </div>
            </ScrollArea>
          </div>

          {/* Code Editor View */}
          <div className="flex-1 flex flex-col bg-white overflow-hidden">
            {allFileActions.length > 0 && allFileActions[selectedFileIndex] ? (
              <>
                <div className="border-b px-4 py-2.5 bg-muted/30 shrink-0">
                  <div className="flex items-center gap-2.5">
                    <File className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-mono text-muted-foreground">
                      {allFileActions[selectedFileIndex].filePath}
                    </span>
                  </div>
                </div>
                <ScrollArea className="flex-1 bg-white overflow-auto">
                  <SyntaxHighlighter
                    language={getLanguage(
                      allFileActions[selectedFileIndex].filePath || ""
                    )}
                    style={oneLight}
                    showLineNumbers={true}
                    customStyle={{
                      margin: 0,
                      padding: "20px",
                      background: "#ffffff",
                      fontFamily:
                        'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                      fontSize: "14px",
                      lineHeight: "21px",
                      fontWeight: 400,
                    }}
                    lineNumberStyle={{
                      minWidth: "3.5em",
                      paddingRight: "1.5em",
                      color: "#9ca3af",
                      userSelect: "none",
                      background: "#ffffff",
                      fontFamily:
                        'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                    }}
                    codeTagProps={{
                      style: {
                        background: "#ffffff",
                        fontFamily:
                          'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                        fontSize: "14px",
                        lineHeight: "21px",
                        fontWeight: 400,
                      },
                    }}
                    wrapLongLines={false}
                  >
                    {allFileActions[selectedFileIndex].content || ""}
                  </SyntaxHighlighter>
                </ScrollArea>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground bg-white">
                <div className="text-center space-y-2">
                  <Code className="h-12 w-12 mx-auto opacity-20" />
                  <p className="font-medium">No files to display</p>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent
          value="demo"
          className="flex-1 m-0 flex flex-col overflow-hidden"
        >
          {previewUrl ? (
            <ResizablePanelGroup direction="vertical" className="flex-1">
              <ResizablePanel defaultSize={70} minSize={30}>
                <div className="h-full overflow-hidden">
                  <iframe
                    src={previewUrl}
                    className="w-full h-full border-0"
                    title="Preview"
                  />
                </div>
              </ResizablePanel>

              <ResizableHandle withHandle />

              <ResizablePanel defaultSize={30} minSize={20}>
                <Terminal sessionId={sessionId} />
              </ResizablePanel>
            </ResizablePanelGroup>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center space-y-2">
                <Monitor className="h-12 w-12 mx-auto opacity-20" />
                <p>No preview available yet</p>
                <p className="text-sm">
                  Execute the artifact to see the preview
                </p>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
