### 使用步骤
1. 配置python运行环境，安装所需的包
```
pip install -r requirements.txt
```
2. main.py 配置参数，出发地、目的地、日期，以及最大停留数。
```python
if __name__ == '__main__':
    results = []
    max_stops = 1
    origins = ['TYO', 'PVG']
    destinations = ['NYC', 'LAX']
    dates = [
        '2023-03-05',
        '2023-03-06',
        '2023-03-07',
        '2023-03-08',
        '2023-03-09',
        '2023-03-10'
    ]
```
3.运行py文件，输出为output.xlsx

4.如果有报错提示，例如openpyxl等包未安装，使用pip安装即可。
