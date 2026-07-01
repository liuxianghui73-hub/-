# ISA-Sales-Agent

基于 AI Agent 的智能销售助手系统，支持多角色切换、线索分析与话术生成。

## 核心特性

- **多角色 Agent**：销售话术生成 / 竞品分析 / 客户画像，一键切换 System Prompt
- **LangGraph ReAct Agent**：analyze → extract → reply 三阶段流水线，基于 DeepSeek Thinking 模式
- **流式对话**：FastAPI SSE + OpenAI stream=True 异步流式响应
- **Markdown 渲染**：AI 回复支持标题、列表、引用块等富文本排版
- **飞书导出**：一键导出对话为 Markdown 文件 / 模拟同步到飞书文档
- **Docker 一键部署**：多阶段构建 + docker-compose 编排（含 Redis 速率限制）
- **API 鉴权与限流**：X-API-Key 鉴权 + slowapi 速率限制（10 req/min）

> ⚠️ **已知问题**：`/api/agent/stream` 流式输出（逐 token 推送）目前在 Docker 环境下偶现整段返回，本地 `uvicorn` 直连正常。详见 [当前状态](#当前状态)。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn | 异步 Web 服务 |
| **AI Agent** | LangGraph 0.2.0 | StateGraph 编排 analyze → extract → reply |
| **LLM** | DeepSeek (deepseek-chat) | 通过 OpenAI SDK 调用，启用 Thinking 模式 |
| **前端框架** | Next.js 14 (App Router) | React 18 + TypeScript |
| **样式** | Tailwind CSS | 无第三方 UI 库 |
| **Markdown** | react-markdown + remark-gfm | AI 回复富文本渲染 |
| **容器化** | Docker + Docker Compose | 多阶段构建，非 root 运行 |
| **缓存/限流** | Redis + slowapi | 速率限制与会话缓存 |
| **日志** | Loguru | JSON 格式结构化日志 |

## 项目结构

```
isa-sales-agent/
├── backend/
│   ├── app/
│   │   ├── api/            # REST API 路由（chat / agent）
│   │   ├── core/           # 配置 / 安全 / 日志 / 限流
│   │   ├── graphs/         # LangGraph Agent（sales_agent.py）
│   │   ├── services/       # 业务服务层
│   │   └── main.py         # FastAPI 入口
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── app/                # Next.js App Router 页面
│   ├── components/         # 组件（ChatInput / MessageList / RoleSelector）
│   ├── lib/                # 工具函数（Markdown 导出 / 飞书模拟）
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 快速开始

### 前置要求

- Docker & Docker Compose（推荐）
- 或 Python 3.11+ + Node.js 18+（本地开发）

### 1. 克隆项目

```bash
git clone https://github.com/liuxianghui73-hub/-.git
cd isa-sales-agent
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，填入你的 DeepSeek API Key：

```env
OPENAI_API_KEY=sk-your-deepseek-key-here
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
API_SECRET_KEY=your-custom-api-key
```

### 3. 启动服务（Docker Compose，推荐）

```bash
docker compose build --no-cache
docker compose up -d
```

服务启动后：

| 服务 | 地址 |
|------|------|
| **前端** | http://localhost:3000 |
| **后端 API 文档** | http://localhost:8000/docs |
| **健康检查** | http://localhost:8000/health |

### 4. 本地开发（不使用 Docker）

```bash
# 后端
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

## API 接口

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/health` | 健康检查 | 无 |
| POST | `/api/chat/stream` | 流式对话（支持 role + history） | X-API-Key |
| POST | `/api/agent/stream` | LangGraph Agent 流式（analyze → extract → reply） | X-API-Key |
| GET | `/api/agent/status` | Agent 状态 | X-API-Key |

### curl 测试

```bash
# 健康检查
curl http://localhost:8000/health

# Agent 流式接口
curl -X POST http://localhost:8000/api/agent/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-custom-api-key" \
  -d "{\"message\":\"预算50万，系统太慢，Q3上线\"}"
```

## 当前状态

### v1.0 — MVP 已完成

| 功能 | 状态 |
|------|------|
| FastAPI 后端骨架 + CORS + 限流 + 鉴权 | ✅ |
| LangGraph ReAct Agent（analyze → extract → reply） | ✅ |
| DeepSeek API 集成（Thinking 模式 + Function Calling） | ✅ |
| 多角色 System Prompt（销售 / 竞品 / 客户画像） | ✅ |
| Next.js 前端 + Markdown 渲染 + 角色切换 | ✅ |
| 飞书导出（Markdown 下载 / 模拟同步） | ✅ |
| Docker 多阶段构建 + docker-compose 编排 | ✅ |
| 流式输出（逐 token SSE 推送） | ⚠️ 偶现问题 |

### ⚠️ 流式输出已知问题

`/api/agent/stream` 在 Docker 环境下偶现整段返回而非逐 token 推送。本地 `uvicorn --reload` 直连 DeepSeek 时流式正常，问题可能与 Docker 网络层的缓冲策略有关（nginx-proxy / content-encoding）。计划在下一版本修复。

## Roadmap

- [ ] **v1.1**：修复流式输出在 Docker 环境下的偶现问题
- [ ] **v1.2**：接入 Redis 会话管理，支持多轮对话上下文
- [ ] **v2.0**：接入向量知识库（ChromaDB），支持 RAG 检索增强
- [ ] **v2.1**：销售漏斗分析 Dashboard
- [ ] **v3.0**：飞书 OAuth 真实对接



