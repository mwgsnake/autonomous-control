FROM python:3.9
WORKDIR /
COPY *.py .
COPY docker_wheels /wheels
RUN pip install --no-index --find-links=/wheels requests rstr
CMD ["python", "traffic_malicious.py"]

