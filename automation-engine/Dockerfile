FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

RUN mkdir -p downloads screenshots sessions

ENV DEMO_MODE=true
ENV HOST=0.0.0.0
ENV PORT=8003

EXPOSE 8003

CMD ["python", "run.py"]
