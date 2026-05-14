FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
COPY index.html .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]