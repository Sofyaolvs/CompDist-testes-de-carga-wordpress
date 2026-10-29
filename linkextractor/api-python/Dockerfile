FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 5000
# 4 processos x 4 threads, como o Puma da versão Ruby
CMD ["gunicorn", "-w", "4", "--threads", "4", "--keep-alive", "30", "-b", "0.0.0.0:5000", "--timeout", "60", "main:app"]
