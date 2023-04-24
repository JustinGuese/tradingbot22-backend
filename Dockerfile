FROM python:3.10-slim
RUN mkdir /app
WORKDIR /app
COPY ./src/requirements.txt /app
RUN pip install -r requirements.txt
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt');"
COPY ./src/allowed_stocks.py /app/
COPY ./src/buysell.py /app/
COPY ./src/stoploss_takeprofit.py /app/
COPY ./src/pricing_functions.py /app/
COPY ./src/check_open_stoploss.py /app/
COPY ./src/db.py /app/
COPY ./src/notification.py /app/
COPY ./src/elastic.py /app/
COPY ./src/language.py /app/
COPY ./src/earnings.py /app/
COPY ./src/yfrecommendations.py /app/
COPY ./src/yahoo_extras.py /app/
COPY ./src/alpy.py /app/
COPY ./src/graphs.py /app/
COPY ./src/app.py /app/
CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]