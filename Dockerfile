FROM python:3.9
RUN pip install pipenv
ENV PROJECT_DIR /usr/local/src/catfishbot
WORKDIR ${PROJECT_DIR}
COPY Pipfile Pipfile.lock ${PROJECT_DIR}/
RUN pipenv install --system --deploy
COPY . ${PROJECT_DIR}/
VOLUME ["${PROJECT_DIR}/database", "${PROJECT_DIR}/presets/alttpr/external"]
CMD ["python","catfishbot.py"]