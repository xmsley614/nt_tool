FROM python:3.8-slim
LABEL authors="xmsley"
WORKDIR /code
COPY . /code
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python","web_branch.py"]
