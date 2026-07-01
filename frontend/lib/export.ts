import { Message } from '@/types/chat';

/**
 * 导出对话为 Markdown 文件
 */
export function exportToMarkdown(messages: Message[], role: string): void {
  const now = new Date();
  const dateStr = now.toLocaleString('zh-CN');
  
  // 构建 Markdown 内容
  let md = `# ISA Sales Agent 对话记录\n\n`;
  md += `**角色**: ${role}\n`;
  md += `**时间**: ${dateStr}\n\n`;
  md += `---\n\n`;
  
  messages.forEach(msg => {
    const roleLabel = msg.role === 'user' ? '👤 用户' : '🤖 AI';
    md += `### ${roleLabel}\n\n`;
    md += `${msg.content}\n\n`;
  });
  
  // 创建 Blob 并下载
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `isa-chat-${now.getTime()}.md`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * 模拟导出到飞书文档
 */
export async function exportToFeishu(messages: Message[], role: string): Promise<boolean> {
  // Mock API 调用
  console.log('Exporting to Feishu:', { messages, role });
  
  // 模拟网络延迟
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 模拟成功
  return true;
}
