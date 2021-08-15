FROM python:3.9
COPY requirements.txt .
RUN pip install pipenv
RUN pipenv install --system --deploy
COPY . .
CMD ["python","main.py"]