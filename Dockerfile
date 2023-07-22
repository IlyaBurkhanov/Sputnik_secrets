FROM python:3.11.0

ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt --no-dependencies
COPY src ./src

CMD python src/app.py