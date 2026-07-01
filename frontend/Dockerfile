# =============================================================================
# Next.js Docker 多阶段构建
# 使用 standalone 输出模式，最小化镜像体积
# =============================================================================

# 阶段 1: 安装依赖（包括 devDependencies）
FROM node:18.20-slim AS deps

WORKDIR /app

# 复制 package 文件
COPY package.json package-lock.json* ./

# 安装所有依赖（包括 devDependencies，构建时需要 tailwindcss 等）
# 使用 npm install 替代 npm ci，避免跨平台 package-lock.json 兼容性问题
RUN npm install

# 阶段 2: 构建应用
FROM node:18.20-slim AS builder

WORKDIR /app

# 设置生产环境
ENV NODE_ENV=production

# 从 deps 阶段复制 node_modules（包含所有依赖）
COPY --from=deps /app/node_modules ./node_modules

# 复制源代码（包括 components、app、lib 等）
COPY . .

# 构建 Next.js 应用（生成 .next/standalone）
RUN npm run build

# 阶段 3: 生产运行
FROM node:18.20-slim AS runner

WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# 创建非 root 用户
RUN groupadd --system --gid 1001 nodejs && \
    useradd --system --uid 1001 --gid nodejs nextjs

# 复制 public 目录
# COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# 复制 standalone 产物
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切换到非 root 用户
USER nextjs

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# 启动命令
CMD ["node", "server.js"]
