# 前端 Dockerfile
# 多阶段构建：Stage 1 构建静态文件，Stage 2 使用 Caddy 托管

# Stage 1: 构建阶段
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json（如果存在）
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制应用代码
COPY . .

# 构建生产版本
RUN npm run build

# Stage 2: 服务阶段（使用 Caddy 替代 Nginx，支持自动 HTTPS）
FROM caddy:2-alpine

# 复制自定义 Caddy 配置
COPY Caddyfile /etc/caddy/Caddyfile

# 从构建阶段复制构建产物到 Caddy 站点目录
COPY --from=builder /app/dist /usr/share/caddy/html

# Caddy 默认暴露 80 和 443 端口
EXPOSE 80
EXPOSE 443

# 启动 Caddy（使用默认的 Caddyfile 路径）
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
