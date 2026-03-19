import { clsx, type ClassValue } from "clsx";
import type { Message } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen - 1) + "…";
}

export function formatSourceUrl(url: string): string {
  try {
    const u     = new URL(url);
    const parts = u.pathname.split("/").filter(Boolean);
    const last  = parts[parts.length - 1] || parts[parts.length - 2] || "";
    return `${u.hostname} › ${last.replace(/-/g, " ")}`;
  } catch {
    return url;
  }
}

export function formatConfidence(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function confidenceColor(score: number): string {
  if (score >= 0.80) return "text-green-600  dark:text-green-400";
  if (score >= 0.60) return "text-amber-600  dark:text-amber-400";
  return                     "text-red-500   dark:text-red-400";
}

export function confidenceBarColor(score: number): string {
  if (score >= 0.80) return "bg-green-500";
  if (score >= 0.60) return "bg-amber-500";
  return                     "bg-red-500";
}

export function sessionTitle(messages: Message[]): string {
  const first = messages.find((m) => m.role === "user");
  if (!first) return "New conversation";
  return truncate(first.content, 42);
}

/** Export conversation as Markdown and trigger browser download */
export function exportAsMarkdown(messages: Message[]): void {
  const lines: string[] = [
    "# GitLab Handbook AI — Conversation Export",
    `*Exported: ${new Date().toLocaleString()}*`,
    "",
  ];
  for (const msg of messages) {
    if (msg.role === "user") {
      lines.push(`## You`, msg.content, "");
    } else {
      lines.push(`## GitLab AI`, msg.content, "");
      if (msg.sources?.length) {
        lines.push(
          "**Sources:**",
          ...msg.sources.map((s) => `- [${s.page_title || s.source_url}](${s.source_url})`),
          "",
        );
      }
    }
  }
  downloadFile(lines.join("\n"), `gitlab-ai-${Date.now()}.md`, "text/markdown");
}

/** Export conversation as PDF using jsPDF */
export async function exportAsPDF(messages: Message[]): Promise<void> {
  // Dynamic import — only load jspdf when needed (code splitting)
  const { jsPDF } = await import("jspdf");

  const doc     = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageW   = doc.internal.pageSize.getWidth();
  const pageH   = doc.internal.pageSize.getHeight();
  const margin  = 16;
  const maxW    = pageW - margin * 2;
  let   cursorY = margin;

  const ensureSpace = (needed: number) => {
    if (cursorY + needed > pageH - margin) {
      doc.addPage();
      cursorY = margin;
    }
  };

  const addText = (text: string, size: number, isBold = false, color = "#111111") => {
    doc.setFontSize(size);
    doc.setFont("helvetica", isBold ? "bold" : "normal");
    doc.setTextColor(color);

    // Strip markdown symbols for PDF (basic)
    const clean = text
      .replace(/#{1,6}\s/g, "")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/`(.*?)`/g,  "$1")
      .replace(/^[-•]\s/gm, "  • ");

    const lines = doc.splitTextToSize(clean, maxW) as string[];
    const lineH = size * 0.45;

    ensureSpace(lines.length * lineH + 4);
    doc.text(lines, margin, cursorY);
    cursorY += lines.length * lineH + 4;
  };

  // Title
  addText("GitLab Handbook AI — Conversation Export", 16, true, "#FC6D26");
  addText(`Exported: ${new Date().toLocaleString()}`, 9, false, "#888888");
  cursorY += 6;

  // Messages
  for (const msg of messages) {
    if (msg.role === "user") {
      ensureSpace(10);
      addText("You", 11, true, "#FC6D26");
      addText(msg.content, 10, false, "#222222");
    } else {
      ensureSpace(10);
      addText("GitLab AI", 11, true, "#6B4FBB");
      addText(msg.content, 10, false, "#222222");

      if (msg.sources?.length) {
        addText("Sources:", 9, true, "#888888");
        for (const src of msg.sources) {
          addText(`• ${src.source_url}`, 8, false, "#0066CC");
        }
      }
    }
    cursorY += 5;
  }

  doc.save(`gitlab-ai-${Date.now()}.pdf`);
}

export function downloadFile(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}