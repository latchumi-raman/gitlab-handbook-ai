import { Header }     from "./Header";
import { Sidebar }    from "@/components/sidebar/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChat }    from "@/hooks/useChat";

export function Layout() {
  const { sendChat } = useChat();

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-surface-50 dark:bg-surface-950">
      <Header />
      <div className="flex flex-1 min-h-0">
        <Sidebar onTopicSelect={(q) => sendChat(q)} />
        <main className="flex flex-col flex-1 min-w-0">
          <ChatWindow />
        </main>
      </div>
    </div>
  );
}