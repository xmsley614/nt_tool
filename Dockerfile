FROM python:3.8-slim
LABEL authors="xmsley"
COPY . /
RUN pip install --upgrade pip
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
WORKDIR /
CMD ["python","web_branch.py"]
