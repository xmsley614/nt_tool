FROM python:3.8-slim
LABEL authors="xmsley"
WORKDIR /code
COPY . /code
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
CMD ["python","web_branch.py"]
