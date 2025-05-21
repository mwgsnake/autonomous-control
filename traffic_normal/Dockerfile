FROM python:3.9

WORKDIR /app

COPY traffic_normal.py .

COPY docker_wheels /wheels

RUN pip install --no-index --find-links=/wheels requests

CMD ["python", "traffic_normal.py"]

