'use client';

import { useState, useRef } from 'react';
import MessageList from '@/components/MessageList';
import ChatInput from '@/components/ChatInput';
import RoleSelector from '@/components/RoleSelector';
import { Message, ChatRole } from '@/types/chat';

/** 限制历史对话轮数（一问一答算一轮） */
const MAX_HISTORY_TURNS = 10;

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentRole, setCurrentRole] = useState<ChatRole>('sales');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /** 切换角色时重置对话 */
  const handleRoleChange = (newRole: ChatRole) => {
    if (messages.length > 0) {
      if (!confirm('切换角色将清空当前对话，是否继续？')) {
        return;
      }
    }
    setCurrentRole(newRole);
    setMessages([]);
    setError(null);
  };

  /** 截取最近 N 轮历史（不包含当前消息） */
  const getHistory = (allMessages: Message[]): Message[] => {
    // 取最近 MAX_HISTORY_TURNS * 2 条消息（一问一答）
    return allMessages.slice(-MAX_HISTORY_TURNS * 2);
  };

  const handleSend = async (userMessage: string) => {
    // 构造用户消息
    const userMsg: Message = { role: 'user', content: userMessage };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setIsLoading(true);
    setError(null);

    // 添加空的 AI 消息占位
    const aiMessage: Message = { role: 'assistant', content: '' };
    setMessages([...updatedMessages, aiMessage]);

    // 截取历史（不包含刚添加的空 AI 消息）
    const history = getHistory(updatedMessages);

    try {
      abortControllerRef.current = new AbortController();

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          role: currentRole,
          history: history,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      // 读取 SSE 流
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 解析 SSE 格式：data: xxx\n\n
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.slice(6);
            if (content === '[DONE]') break;

            // 逐字追加到 AI 消息
            setMessages(prev => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg && lastMsg.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...lastMsg,
                  content: lastMsg.content + content,
                };
              }
              return updated;
            });
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      console.error('Chat error:', err);
      setError('AI 服务暂时不可用');
      // 移除空的 AI 消息
      setMessages(prev => prev.filter(msg => msg.content !== '' || msg.role === 'user'));
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-bold text-gray-100">ISA Sales Agent</h1>
            <p className="text-sm text-gray-400">智能销售助手</p>
          </div>
          <RoleSelector
            currentRole={currentRole}
            onRoleChange={handleRoleChange}
            disabled={isLoading}
          />
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500 text-white px-6 py-3 text-center">
          {error}
          <button onClick={() => setError(null)} className="ml-4 underline text-sm">
            关闭
          </button>
        </div>
      )}

      {/* Message List */}
      <MessageList messages={messages} isLoading={isLoading} currentRole={currentRole} />

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
