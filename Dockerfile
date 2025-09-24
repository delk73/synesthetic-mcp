FROM python:3.11-slim

# Keep Python lean and predictable in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install lightweight tooling required for health checks
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source and install in editable mode
COPY . .
RUN pip install -e .

# Drop root privileges once dependencies are installed
RUN useradd --create-home --home-dir /home/mcp --shell /usr/sbin/nologin mcp \
    && chown -R mcp:mcp /app

USER mcp
ENV HOME=/home/mcp

# Default to the blocking MCP server; callers may override for tests
CMD ["python", "-m", "mcp"]
