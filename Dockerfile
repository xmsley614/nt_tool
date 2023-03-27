FROM python:3.8
LABEL authors="xmsley"
COPY . /
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
WORKDIR /
CMD ["python","web_branch.py"]
