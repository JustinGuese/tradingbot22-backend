FROM python:3.10-slim
RUN mkdir /app
WORKDIR /app
COPY ./src/requirements.txt /app
RUN pip install -r requirements.txt
COPY ./src/db.py /app/
COPY ./src/elastic.py /app/
COPY ./src/language.py /app/
COPY ./src/yfrecommendations.py /app/
COPY ./src/app.py /app/
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt');"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]