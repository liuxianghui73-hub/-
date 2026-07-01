export type ChatRole = 'sales' | 'competitor' | 'portrait';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  stage?: 'analyze' | 'extract' | 'reply'; // Agent 当前阶段
}
