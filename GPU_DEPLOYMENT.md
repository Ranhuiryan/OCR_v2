# GPU 加速部署指南

## 概述

使用 GPU 可以显著加速 OCR 处理速度，特别是在处理大批量文档时。本文档介绍如何在 Docker 环境中启用 GPU 加速。

## 前置要求

### 1. 硬件要求
- ✅ NVIDIA GPU（支持 CUDA）
- ✅ 推荐：显存 ≥ 4GB

### 2. 软件要求
- ✅ NVIDIA Driver（版本 ≥ 450.x）
- ✅ Docker Engine 19.03+
- ✅ NVIDIA Container Toolkit

## 安装步骤

### 步骤 1：验证 NVIDIA Driver

```bash
# 检查 NVIDIA Driver 是否安装
nvidia-smi

# 应该看到类似输出：
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.xx.xx    Driver Version: 525.xx.xx    CUDA Version: 12.x  |
# +-----------------------------------------------------------------------------+
```

如果未安装，请参考：https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html

### 步骤 2：安装 NVIDIA Container Toolkit

#### Ubuntu/Debian

```bash
# 1. 设置 APT 源
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. 安装
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 3. 配置 Docker Runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### CentOS/RHEL

```bash
# 1. 设置 YUM 源
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# 2. 安装
sudo yum install -y nvidia-container-toolkit

# 3. 配置 Docker Runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 步骤 3：验证 GPU 可用

```bash
# 测试 Docker 是否能访问 GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# 应该看到 nvidia-smi 输出，显示 GPU 信息
```

## 使用 GPU 版本

### 1. 配置环境变量

编辑 `.env` 文件：

```env
# 指定使用的 GPU 数量
GPU_COUNT=1

# 指定使用哪些 GPU
# all: 使用所有 GPU
# 0: 仅使用 GPU 0
# 0,1: 使用 GPU 0 和 1
GPU_DEVICE_IDS=all

# 调整并发数（GPU 模式建议降低以避免显存不足）
CELERY_CONCURRENCY=1

# 模型源（可选）
MINERU_MODEL_SOURCE=modelscope
```

### 2. 启动 GPU 版本

```bash
# 停止现有服务（如果正在运行）
docker compose down

# 使用 GPU 配置启动
docker compose -f docker-compose.gpu.yml up -d --build

# 查看日志确认 GPU 使用
docker compose logs -f celery
```

### 3. 验证 GPU 使用

```bash
# 查看 Celery worker 容器是否能看到 GPU
docker exec ocr_celery_worker nvidia-smi

# 查看日志中是否有 CUDA 相关信息
docker compose logs celery | grep -i cuda

# 实时监控 GPU 使用情况
watch -n 1 nvidia-smi
```

## 性能优化

### 调整并发数

```env
# GPU 显存充足时可以增加并发
CELERY_CONCURRENCY=2

# 显存不足时建议降低
CELERY_CONCURRENCY=1
```

### 选择合适的 GPU

```env
# 使用特定 GPU（适用于多 GPU 系统）
GPU_DEVICE_IDS=0    # 使用第一个 GPU
GPU_DEVICE_IDS=1    # 使用第二个 GPU
GPU_DEVICE_IDS=0,1  # 同时使用两个 GPU
```

### 监控 GPU 使用

```bash
# 实时监控
watch -n 1 nvidia-smi

# 或安装 nvtop（更友好的界面）
sudo apt install nvtop
nvtop
```

## 常见问题

### Q1: `docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]`

**原因**：NVIDIA Container Toolkit 未正确安装或配置

**解决**：
```bash
# 重新配置 Docker Runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 验证配置
docker info | grep -i runtime
```

### Q2: 容器内看不到 GPU

**原因**：Docker Compose 版本过低或配置错误

**解决**：
```bash
# 确认 Docker Compose 版本 ≥ 1.28
docker compose version

# 如果版本过低，升级
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### Q3: GPU 显存不足 (CUDA out of memory)

**解决**：
```env
# 降低并发数
CELERY_CONCURRENCY=1

# 或分批处理文档
```

### Q4: GPU 利用率低

**可能原因**：
1. PDF 页数少，GPU 优势不明显
2. 瓶颈在其他环节（如 PDF 解析）
3. 数据传输开销

**建议**：
- 批量处理大量文档时 GPU 优势更明显
- 监控整体处理流程，找出瓶颈

## 性能对比

| 配置 | 单页处理时间 | 100 页文档处理时间 |
|------|-------------|-------------------|
| CPU (8 核) | ~2-3 秒 | ~4-5 分钟 |
| GPU (RTX 3080) | ~0.5-1 秒 | ~1-2 分钟 |

*实际性能取决于硬件配置、文档复杂度和模型选择*

## 切换回 CPU 模式

```bash
# 停止 GPU 版本
docker compose -f docker-compose.gpu.yml down

# 启动标准版本
docker compose up -d
```

## 参考资源

- [NVIDIA Container Toolkit 文档](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker GPU 支持](https://docs.docker.com/compose/gpu-support/)
- [MinerU GPU 优化](https://github.com/opendatalab/MinerU)

---

如有问题，请查看主 README 的 Troubleshooting 章节或提交 Issue。
