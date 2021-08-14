FROM python:3.9
COPY requirements.txt .
RUN pip install pipenv
RUN pipenv install
COPY . .
CMD ["pipenv","run","main.py"]