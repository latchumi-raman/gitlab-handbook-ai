import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Moon, Sun, PanelLeft, Download, FileText, Keyboard, BarChart2 } from "lucide-react";
import { useTheme }         from "@/hooks/useTheme";
import { useChatStore }     from "@/store/chatStore";
import { Button }           from "@/components/ui/Button";
import { Tooltip }          from "@/components/ui/Tooltip";
import { StatusIndicator }  from "@/components/ui/StatusIndicator";
import { KeyboardShortcutsModal } from "@/components/ui/KeyboardShortcutsModal";
import { exportAsMarkdown, exportAsPDF } from "@/lib/utils";
import { useSession }       from "@/hooks/useSession";

export function Header() {
  const { toggle, isDark }   = useTheme();
  const toggleSidebar        = useChatStore((s) => s.toggleSidebar);
  const messages             = useChatStore((s) => s.activeMessages());
  const { startNewChat }     = useSession();
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const navigate = useNavigate();

  // Register all keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey;

      // ⌘K — focus input
      if (meta && e.key === "k") {
        e.preventDefault();
        document.querySelector<HTMLTextAreaElement>("textarea")?.focus();
      }
      // ⌘\ — toggle sidebar
      if (meta && e.key === "\\") {
        e.preventDefault();
        toggleSidebar();
      }
      // ⌘D — toggle dark mode
      if (meta && e.key === "d") {
        e.preventDefault();
        toggle();
      }
      // ⌘E — export markdown
      if (meta && !e.shiftKey && e.key === "e" && messages.length) {
        e.preventDefault();
        exportAsMarkdown(messages);
      }
      // ⌘⇧E — export PDF
      if (meta && e.shiftKey && e.key === "E" && messages.length) {
        e.preventDefault();
        exportAsPDF(messages);
      }
      // ⌘⇧N — new chat
      if (meta && e.shiftKey && e.key === "N") {
        e.preventDefault();
        startNewChat();
      }
      // ? — show shortcuts
      if (e.key === "?" && !e.metaKey && !e.ctrlKey) {
        const active = document.activeElement;
        const isTyping = active?.tagName === "TEXTAREA" || active?.tagName === "INPUT";
        if (!isTyping) setShortcutsOpen(true);
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [toggle, toggleSidebar, messages, startNewChat]);

  return (
    <>
      <header className="flex items-center justify-between px-3 py-2.5
                         border-b border-surface-200 dark:border-surface-800
                         bg-white dark:bg-surface-950 shrink-0">
        {/* Left */}
        <div className="flex items-center gap-2">
          <Tooltip text="Toggle sidebar (⌘\)">
            <Button variant="ghost" size="sm" onClick={toggleSidebar}>
              <PanelLeft size={16} />
            </Button>
          </Tooltip>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 hidden sm:block">
            GitLab Handbook AI
          </span>
        </div>

        {/* Right */}
        <div className="flex items-center gap-1">
          {/* Backend status */}
          <div className="px-2">
            <StatusIndicator />
          </div>

          {/* Export buttons — only show when there are messages */}
          {messages.length > 0 && (
            <>
              <Tooltip text="Export as markdown (⌘E)">
                <Button variant="ghost" size="sm" onClick={() => exportAsMarkdown(messages)}>
                  <Download size={15} />
                </Button>
              </Tooltip>
              <Tooltip text="Export as PDF (⌘⇧E)">
                <Button variant="ghost" size="sm" onClick={() => exportAsPDF(messages)}>
                  <FileText size={15} />
                </Button>
              </Tooltip>
            </>
          )}

          {/* Analytics dashboard link */}
          <Tooltip text="Analytics dashboard">
            <Button variant="ghost" size="sm" onClick={() => navigate("/admin")}>
              <BarChart2 size={15} />
            </Button>
          </Tooltip>

          {/* Keyboard shortcuts */}
          <Tooltip text="Keyboard shortcuts (?)">
            <Button variant="ghost" size="sm" onClick={() => setShortcutsOpen(true)}>
              <Keyboard size={15} />
            </Button>
          </Tooltip>

          {/* Dark mode */}
          <Tooltip text={isDark ? "Light mode (⌘D)" : "Dark mode (⌘D)"}>
            <Button variant="ghost" size="sm" onClick={toggle}>
              {isDark ? <Sun size={15} /> : <Moon size={15} />}
            </Button>
          </Tooltip>
        </div>
      </header>

      <KeyboardShortcutsModal
        open={shortcutsOpen}
        onClose={() => setShortcutsOpen(false)}
      />
    </>
  );
}