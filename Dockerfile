FROM python:3.12-slim
LABEL authors="mayko"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
# docker build -t my-python-app .
# docker run -d --name my-python-container -p 8000:8000 my-python-app