/** @type {import('next').NextConfig} */
const nextConfig = {
  // 启用 standalone 输出模式（用于 Docker 部署）
  output: 'standalone',
  
  // 配置后端 API 代理
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
