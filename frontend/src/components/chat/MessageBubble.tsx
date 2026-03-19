import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm     from "remark-gfm";
import { Copy, Check, Wand2 } from "lucide-react";
import type { Message }      from "@/types";
import { SourceChips }           from "./SourceChips";
import { SourceDrawer }          from "./SourceDrawer";
import { ConfidenceBar }         from "./ConfidenceBar";
import { FeedbackButtons }       from "./FeedbackButtons";
import { FollowUpSuggestions }   from "./FollowUpSuggestions";
import { TypingIndicator }       from "./TypingIndicator";
import { Badge }                 from "@/components/ui/Badge";
import { Tooltip }               from "@/components/ui/Tooltip";
import { cn }                    from "@/lib/utils";
import { useSession }            from "@/hooks/useSession";

interface MessageBubbleProps {
  message:      Message;
  prevUserMsg?: string;
  onFollowUp:   (q: string) => void;
}

export function MessageBubble({ message, prevUserMsg, onFollowUp }: MessageBubbleProps) {
  const { sessionId }  = useSession();
  const [drawerOpen,   setDrawerOpen]  = useState(false);
  const [copied,       setCopied]      = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  // ── User message ──────────────────────────────────────────────────────────
  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-slide-up">
        <div className="max-w-[78%] px-4 py-3 rounded-2xl rounded-tr-sm
                        bg-gitlab-orange text-white text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    );
  }

  // ── Assistant message ─────────────────────────────────────────────────────
  const showMeta = !message.isStreaming && message.content;

  return (
    <div className="flex gap-3 animate-slide-up group">
      <div className="shrink-0 mt-0.5 w-7 h-7 rounded-lg
                      bg-gradient-to-br from-gitlab-orange to-gitlab-red
                      flex items-center justify-center">
        <span className="text-white font-bold text-xs select-none">GL</span>
      </div>

      <div className="flex-1 min-w-0">
        {/* Badge row */}
        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
          {message.guardrailTriggered && (
            <Badge variant="warning">Off-topic — handbook only</Badge>
          )}
          {message.queryEnhanced && (
            <Tooltip text={`Original: "${message.originalQuery}"`} position="bottom">
              <Badge variant="info" className="flex items-center gap-1 cursor-help">
                <Wand2 size={10} />
                Query enhanced
              </Badge>
            </Tooltip>
          )}
        </div>

        {/* Body */}
        {message.isStreaming && !message.content
          ? <TypingIndicator />
          : (
            <div className={cn(
              "prose-chat text-sm text-gray-800 dark:text-gray-200",
              message.isStreaming && "after:content-['▋'] after:ml-0.5 after:animate-pulse after:text-gitlab-orange",
            )}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )
        }

        {/* Metadata */}
        {showMeta && (
          <div className="mt-1 space-y-0">
            {message.sources && message.sources.length > 0 && (
              <SourceChips
                sources={message.sources}
                onShowDrawer={() => setDrawerOpen((o) => !o)}
                expandedDrawer={drawerOpen}
              />
            )}
            {message.sources && (
              <SourceDrawer sources={message.sources} open={drawerOpen} />
            )}
            {typeof message.confidence === "number" && !message.guardrailTriggered && (
              <ConfidenceBar score={message.confidence} />
            )}
            {message.followUps && message.followUps.length > 0 && (
              <FollowUpSuggestions
                suggestions={message.followUps}
                onSelect={onFollowUp}
              />
            )}
            <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <FeedbackButtons
                sessionId={sessionId}
                query={prevUserMsg ?? ""}
                response={message.content}
              />
              <button
                onClick={copyToClipboard}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600
                           dark:hover:text-gray-300 hover:bg-surface-100
                           dark:hover:bg-surface-800 transition-colors ml-1"
              >
                {copied
                  ? <Check size={13} className="text-green-500" />
                  : <Copy  size={13} />
                }
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}