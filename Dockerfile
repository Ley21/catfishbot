FROM python:3.9
COPY Pipfile Pipfile.lock
RUN pip install pipenv
RUN pipenv install --system --deploy
COPY . .
CMD ["python","main.py"]