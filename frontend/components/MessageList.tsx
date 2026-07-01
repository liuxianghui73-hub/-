'use client';

import { useState } from 'react';
import { Message, ChatRole } from '@/types/chat';
import { exportToMarkdown, exportToFeishu } from '@/lib/export';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  currentRole: ChatRole;
}

const ROLE_LABELS: Record<ChatRole, string> = {
  sales: '销售话术生成',
  competitor: '竞品分析',
  portrait: '客户画像',
};

export default function MessageList({ messages, isLoading, currentRole }: MessageListProps) {
  const [exportingIndex, setExportingIndex] = useState<number | null>(null);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="text-6xl mb-4">💬</div>
          <p className="text-lg">开始对话吧！</p>
        </div>
      </div>
    );
  }

  const handleExportMd = (upToIndex: number) => {
    const subset = messages.slice(0, upToIndex + 1);
    exportToMarkdown(subset, ROLE_LABELS[currentRole]);
  };

  const handleExportFeishu = async (upToIndex: number) => {
    setExportingIndex(upToIndex);
    try {
      const subset = messages.slice(0, upToIndex + 1);
      const ok = await exportToFeishu(subset, ROLE_LABELS[currentRole]);
      if (ok) {
        alert('✅ 已同步到飞书文档（模拟）');
      }
    } finally {
      setExportingIndex(null);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, index) => (
        <div
          key={index}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div className={`max-w-[70%] ${msg.role === 'assistant' ? 'space-y-1' : ''}`}>
            <div
              className={`rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              <div className="whitespace-pre-wrap break-words">{msg.content}</div>
              {msg.role === 'assistant' && isLoading && index === messages.length - 1 && (
                <span className="inline-block w-2 h-4 bg-gray-300 animate-pulse ml-1" />
              )}
            </div>

            {/* AI 消息导出按钮 */}
            {msg.role === 'assistant' && msg.content && !(isLoading && index === messages.length - 1) && (
              <div className="flex gap-2 px-1">
                <button
                  onClick={() => handleExportMd(index)}
                  className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                  title="导出为 Markdown"
                >
                  📄 Markdown
                </button>
                <button
                  onClick={() => handleExportFeishu(index)}
                  disabled={exportingIndex === index}
                  className="text-xs text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-50"
                  title="同步到飞书文档"
                >
                  {exportingIndex === index ? '同步中...' : '📤 飞书'}
                </button>
              </div>
            )}
          </div>
        </div>
      ))}

      {/* 等待 AI 回复的加载动画 */}
      {isLoading && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
        <div className="flex justify-start">
          <div className="bg-gray-700 text-gray-100 rounded-2xl px-4 py-3">
            <div className="flex space-x-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
