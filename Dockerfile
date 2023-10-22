FROM python:3.11-slim
COPY pyproject.toml poetry.lock /app/
WORKDIR /app
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev
COPY ./src/ /app/
CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]