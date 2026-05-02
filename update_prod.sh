#!/bin/bash

echo "拉取最新代码..."
git pull

echo "重新构建并启动服务..."
docker compose -f docker-compose.prod.yml up -d --build

echo "清理旧镜像..."
docker image prune -f

echo "查看服务状态..."
docker compose -f docker-compose.prod.yml ps

echo "查看最新日志..."
docker compose -f docker-compose.prod.yml logs -f --tail=50