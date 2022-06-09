FROM python:3.11.0b1-alpine
RUN pip install --upgrade pip
WORKDIR /home/ephemerate
ENV PATH="/home/ephemerate/.local/bin:${PATH}"
ENV PIP_USER=1
ENV PIPENV_SYSTEM=1
COPY --chown=ephemerate:ephemerate Pipfile Pipfile
COPY --chown=ephemerate:ephemerate Pipfile.lock Pipfile.lock
COPY --chown=ephemerate:ephemerate ephemerator.py ephemerator.py
RUN adduser --uid 1000 -D ephemerate
USER ephemerate
RUN pip install --no-cache-dir --user pipenv
RUN pipenv install --system --deploy --ignore-pipfile --clear
CMD kopf run -A --liveness=http://0.0.0.0:8080/healthz --log-format=plain ephemerator.py