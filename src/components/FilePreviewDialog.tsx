import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Download } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";

type FileKind = "markdown" | "json" | "csv" | "text";

interface FilePreviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  conversationId: string;
  filename: string; // just the filename, not a path
  displayName?: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const FilePreviewDialog: React.FC<FilePreviewDialogProps> = ({
  open,
  onOpenChange,
  conversationId,
  filename,
  displayName,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");

  const fileKind: FileKind = useMemo(() => {
    const lower = filename.toLowerCase();
    if (
      lower.endsWith(".md") ||
      lower.endsWith(".markdown") ||
      lower.endsWith(".mdx")
    )
      return "markdown";
    if (lower.endsWith(".json")) return "json";
    if (lower.endsWith(".csv")) return "csv";
    return "text";
  }, [filename]);

  // Simple CSV parser that supports quoted fields and escaped quotes
  const parseCSV = (text: string): string[][] => {
    const rows: string[][] = [];
    let row: string[] = [];
    let field = "";
    let inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const char = text[i];
      const next = text[i + 1];
      if (inQuotes) {
        if (char === '"') {
          if (next === '"') {
            // Escaped quote
            field += '"';
            i++;
          } else {
            inQuotes = false;
          }
        } else {
          field += char;
        }
      } else {
        if (char === '"') {
          inQuotes = true;
        } else if (char === ",") {
          row.push(field);
          field = "";
        } else if (char === "\n") {
          row.push(field);
          rows.push(row);
          row = [];
          field = "";
        } else if (char === "\r") {
          // ignore CR (handle CRLF)
        } else {
          field += char;
        }
      }
    }
    // Push last field/row
    row.push(field);
    rows.push(row);
    // Remove potential trailing empty row when text ends with newline
    if (
      rows.length &&
      rows[rows.length - 1].length === 1 &&
      rows[rows.length - 1][0] === ""
    ) {
      rows.pop();
    }
    return rows;
  };

  const csvRows = useMemo(() => {
    if (fileKind !== "csv" || !content) return [] as string[][];
    try {
      const rows = parseCSV(content);
      return rows;
    } catch {
      return [] as string[][];
    }
  }, [fileKind, content]);

  useEffect(() => {
    const fetchContent = async () => {
      if (!open) return;
      setLoading(true);
      setError(null);
      setContent("");
      try {
        const url = `${API_BASE}/files/conversations/${encodeURIComponent(
          conversationId
        )}/attachments/${encodeURIComponent(filename)}`;
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const text = await res.text();
        if (fileKind === "json") {
          try {
            const obj = JSON.parse(text);
            setContent(JSON.stringify(obj, null, 2));
          } catch {
            // If JSON parse fails, show raw text
            setContent(text);
          }
        } else {
          setContent(text);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [open, conversationId, filename, fileKind]);

  const title = displayName || filename;

  const handleDownload = async () => {
    try {
      const url = `${API_BASE}/files/conversations/${encodeURIComponent(
        conversationId
      )}/attachments/${encodeURIComponent(filename)}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Nettoyer l'URL créée
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error("Erreur lors du téléchargement:", error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl w-full h-[80vh] max-h-[80vh] flex flex-col overflow-hidden">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="truncate">{title}</DialogTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              className="h-7 px-2 ml-2"
              title="Télécharger le fichier"
            >
              <Download className="h-3 w-3" />
            </Button>
          </div>
        </DialogHeader>

        {/* Body */}
        <div className="mt-2 flex-1 min-h-0 flex flex-col overflow-hidden">
          {loading && (
            <div className="text-sm text-muted-foreground">
              Chargement du fichier…
            </div>
          )}
          {error && (
            <div className="text-sm text-red-600 dark:text-red-400">
              Erreur: {error}
            </div>
          )}
          {!loading && !error && (
            <ScrollArea className="h-full rounded border bg-muted/10">
              {fileKind === "markdown" ? (
                <div className="p-4">
                  <MarkdownRenderer content={content} />
                </div>
              ) : fileKind === "csv" ? (
                <div className="p-4 overflow-x-auto">
                  {csvRows.length > 0 ? (
                    <table className="min-w-full border border-border text-sm">
                      <thead className="bg-muted/40">
                        <tr>
                          {csvRows[0].map((h, i) => (
                            <th
                              key={i}
                              className="px-3 py-2 border-b border-r text-left font-semibold text-foreground/90"
                            >
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {csvRows.slice(1).map((r, ri) => (
                          <tr
                            key={ri}
                            className={
                              ri % 2 === 0 ? "bg-background" : "bg-muted/20"
                            }
                          >
                            {r.map((c, ci) => (
                              <td
                                key={ci}
                                className="px-3 py-2 border-b border-r whitespace-pre-wrap break-words align-top"
                              >
                                {c}
                              </td>
                            ))}
                            {/* Fill missing cells if row shorter than headers */}
                            {r.length < csvRows[0].length &&
                              Array.from({
                                length: csvRows[0].length - r.length,
                              }).map((_, k) => (
                                <td
                                  key={`pad-${k}`}
                                  className="px-3 py-2 border-b border-r"
                                />
                              ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      CSV vide ou invalide.
                    </div>
                  )}
                </div>
              ) : (
                <pre className="p-4 text-sm font-mono whitespace-pre-wrap break-words">
                  {content}
                </pre>
              )}
            </ScrollArea>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FilePreviewDialog;
