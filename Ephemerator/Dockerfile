FROM python:3.9.9-alpine
RUN pip install --no-cache-dir --upgrade pip pipenv
COPY Pipfile /
COPY Pipfile.lock /
ADD ephemerator.py /
RUN pipenv install --system --deploy --ignore-pipfile --clear
CMD kopf run -A --liveness=http://0.0.0.0:8080/healthz --log-format=plain /ephemerator.py