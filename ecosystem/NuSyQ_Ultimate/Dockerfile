# Minimal Dockerfile for NuSyQ Root

FROM python:3.12-slim
WORKDIR /app

# Copy only requirements.txt first for dependency install
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN if [ -f mcp_server/requirements.txt ]; then pip install --no-cache-dir -r mcp_server/requirements.txt; fi

# Copy source code
COPY src/ ./src/
COPY mcp_server/ ./mcp_server/
COPY mcp_server/requirements.txt ./mcp_server/requirements.txt
COPY README.md ./
COPY Dockerfile ./

# Install mcp_server-specific requirements (copied above)
RUN if [ -f mcp_server/requirements.txt ]; then python -m pip install --no-cache-dir --upgrade -r mcp_server/requirements.txt; fi

# Expose MCP server port
EXPOSE 8765

# Start MCP server (use mcp_server main)
CMD ["python", "mcp_server/main.py"]
