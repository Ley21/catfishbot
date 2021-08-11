FROM Python:3.9
COPY requirments.txt .
RUN pip install -r requirments.txt
COPY . .
CMD ["python","main.py"]