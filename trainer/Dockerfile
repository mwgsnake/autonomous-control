FROM python:3.9

WORKDIR /app

COPY trainer.py .

COPY docker_wheels /wheels
RUN pip install --no-index --find-links=/wheels tensorflow pandas numpy scikit-learn joblib
CMD ["python", "trainer.py"]

