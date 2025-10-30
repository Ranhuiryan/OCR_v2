#!/bin/sh

# 如果任何命令失败，立即退出
set -e

# 等待数据库准备就绪
# [修正] 使用正确的环境变量名 POSTGRES_HOST 和 POSTGRES_PORT
/app/wait-for-it.sh "$POSTGRES_HOST:$POSTGRES_PORT"

# 等待 Redis 准备就绪
/app/wait-for-it.sh "$REDIS_HOST:6379"

# 现在服务都已就绪, 执行作为参数传入此脚本的命令
exec "$@"