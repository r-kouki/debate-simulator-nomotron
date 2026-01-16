# Docker Deployment Guide

## Prerequisites

1. **Docker** with Docker Compose v2
2. **NVIDIA Container Toolkit** (for GPU support)
3. **Models** downloaded to `./models` directory

### Install NVIDIA Container Toolkit

```bash
# Add NVIDIA GPG key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Add repo
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

## Quick Start

```bash
# Build and start everything
docker compose up --build

# Or run in background
docker compose up --build -d
```

**Access the application:**
- Frontend: http://localhost:4040
- Backend API: http://localhost:5040/api

---

## File Structure

```
├── Dockerfile.backend    # Backend with CUDA
├── Dockerfile.frontend   # Frontend multi-stage build
├── docker-compose.yml    # Orchestration
├── nginx.conf           # Frontend server + API proxy
└── .dockerignore        # Build exclusions
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device(s) to use |

### Ports

| Service | Container | Host |
|---------|-----------|------|
| Frontend | 80 | 4040 |
| Backend | 5040 | 5040 |

---

## Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after code changes
docker compose up --build

# Check status
docker compose ps
```

---

## Troubleshooting

### GPU Not Detected
```bash
# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### Models Not Loading
Ensure models are in `./models/base/` directory and adapters in `./models/adapters/`.

### Out of Memory
Reduce model size or use `CUDA_VISIBLE_DEVICES` to select a different GPU.
