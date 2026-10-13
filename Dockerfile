# Runs the API as a non-root user. For untrusted tasks also run the container with
#   --network none --read-only --tmpfs /tmp --pids-limit 128 --memory 1g
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt
COPY assistant ./assistant
RUN useradd -m coder
USER coder
EXPOSE 8000
CMD ["uvicorn", "assistant.api:app", "--host", "0.0.0.0", "--port", "8000"]
