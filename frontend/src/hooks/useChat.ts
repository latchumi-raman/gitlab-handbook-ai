import { useRef, useCallback } from "react";
import { useChatStore } from "@/store/chatStore";
import { readSSEStream } from "@/lib/stream";
import { endpoints }    from "@/lib/api";
import type { SSEEvent, SourceChunk } from "@/types";

export function useChat() {
  const abortRef = useRef<AbortController | null>(null);

  const {
    activeSessionId, activeMessages, pageTypeFilter, matchCount,
    status, addUserMessage, sendMessage, appendToken, finalizeMessage, setStatus,
  } = useChatStore();

  const sendChat = useCallback(
    async (query: string) => {
      if (!query.trim() || status === "generating") return;

      abortRef.current?.abort();
      abortRef.current = new AbortController();

      addUserMessage(query.trim());
      const assistantMsgId = sendMessage();
      setStatus("generating");

      let sources:          SourceChunk[] = [];
      let confidence:       number        = 0;
      let followUps:        string[]      = [];
      let guardrailTriggered              = false;
      let queryEnhanced                   = false;

      try {
        const history = activeMessages()
          .filter((m) => !m.isStreaming)
          .slice(-10)
          .map((m) => ({ role: m.role, content: m.content }));

        await readSSEStream(
          endpoints.chatStream,
          {
            query,
            session_id:       activeSessionId,
            history,
            page_type_filter: pageTypeFilter,
            match_count:      matchCount,
          },
          (event: SSEEvent) => {
            switch (event.type) {
              case "token":
                appendToken(assistantMsgId, event.content);
                break;

              case "sources":
                sources = event.sources;
                finalizeMessage(assistantMsgId, { sources, isStreaming: true });
                break;

              case "metadata":
                confidence = event.confidence;
                followUps  = event.follow_ups;
                break;

              case "guardrail":
                guardrailTriggered = true;
                break;

              // NEW in Phase 4
              case "query_enhanced":
                queryEnhanced = true;
                break;

              case "error":
                appendToken(assistantMsgId, `\n\n*Error: ${event.message}*`);
                break;

              case "done":
                finalizeMessage(assistantMsgId, {
                  sources,
                  confidence,
                  followUps,
                  guardrailTriggered,
                  queryEnhanced,
                  originalQuery: queryEnhanced ? query : undefined,
                  isStreaming: false,
                });
                setStatus("idle");
                break;
            }
          },
          abortRef.current.signal,
        );
      } catch (err: unknown) {
        if ((err as Error)?.name !== "AbortError") {
          const msg = err instanceof Error ? err.message : "Unknown error";
          appendToken(assistantMsgId, `\n\n*Connection error: ${msg}*`);
        }
        finalizeMessage(assistantMsgId, { isStreaming: false });
        setStatus("idle");
      }
    },
    [
      activeSessionId, activeMessages, pageTypeFilter, matchCount, status,
      addUserMessage, sendMessage, appendToken, finalizeMessage, setStatus,
    ],
  );

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
  }, [setStatus]);

  return { sendChat, stopGeneration, isGenerating: status === "generating" };
}