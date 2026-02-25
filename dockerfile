FROM python:3.12.9

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY req.txt /app/

RUN pip install --upgrade pip && pip install -r req.txt

COPY . /app/

EXPOSE 8010

# CMD ["gunicorn", "service_profiles.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
CMD ["python", "start.py"]


