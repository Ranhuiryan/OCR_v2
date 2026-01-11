#!/bin/sh
set -e

host="$1"

# 从 host:port 字符串中提取 host 和 port
wait_host=$(echo "$host" | cut -d: -f1)
wait_port=$(echo "$host" | cut -d: -f2)

until nc -z "$wait_host" "$wait_port"; do
  >&2 echo "Service ${host} is unavailable - sleeping"
  sleep 1
done

>&2 echo "Service ${host} is up."