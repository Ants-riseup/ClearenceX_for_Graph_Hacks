FROM python:3.11-slim
WORKDIR /app
ARG WITH_OCR=false
ARG WITH_MCP=true
RUN if [ "$WITH_OCR" = "true" ]; then apt-get update && apt-get install -y --no-install-recommends poppler-utils libgl1 libglib2.0-0 libgomp1 && rm -rf /var/lib/apt/lists/*; fi
COPY requirements-core.txt requirements.txt requirements-ocr.txt requirements-mcp.txt ./
RUN pip install --no-cache-dir -r requirements-core.txt
RUN if [ "$WITH_MCP" = "true" ]; then pip install --no-cache-dir -r requirements-mcp.txt; fi
RUN if [ "$WITH_OCR" = "true" ]; then pip install --no-cache-dir -r requirements.txt; fi
RUN useradd --create-home clearancex && mkdir -p /data/uploads && chown -R clearancex:clearancex /data
COPY --chown=clearancex:clearancex . .
USER clearancex
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
