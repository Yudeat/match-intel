FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy only requirements.txt
COPY requirements.txt* ./

RUN uv pip install --system --no-cache -r requirements.txt || uv pip install --system --no-cache fastapi uvicorn redis numpy pydantic sse-starlette

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]