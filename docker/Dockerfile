FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/cache data/logs data/plugins data/db data/vault

EXPOSE 8080 8081

ENV PYTHONUNBUFFERED=1
ENV CTZ_ENV=production

CMD ["python", "mcp_servers/unified_control_mcp.py"]
