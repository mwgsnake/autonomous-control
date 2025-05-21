FROM python:3.9

WORKDIR /app

# System packages
# RUN apt-get update && apt-get install -y docker.io

COPY ../docker_wheels /wheels

# RUN pip install streamlit tensorflow pandas numpy streamlit_autorefresh
RUN pip install --no-index --find-links=/wheels streamlit streamlit-autorefresh pandas numpy tensorflow joblib scikit-learn

COPY app /app

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

