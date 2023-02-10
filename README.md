### 使用步骤
1. 配置python运行环境，安装所需的包，注意playwright要额外安装浏览器环境(playwright install)
```
pip install --upgrade pip
pip install pandas
pip install styleframe
pip install playwright
playwright install

```
2. async def main函数位置，配置最大停留次数、起始地点、终点、日期参数。
```python
async def main():
    async with async_playwright() as playwright:
        results = []
        max_stops = 1
        origins = ['TYO', 'ICN']
        destinations = ['NYC', 'YYZ']
        dates = [
            '2023-03-05',
            '2023-03-06',
            '2023-03-07',
            '2023-03-08',
            '2023-03-09',
            '2023-03-10'
        ]
        for ori in origins:
            for des in destinations:
                for date in dates:
                    print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
                    results.extend(await search(playwright, ori, des, date))
                    time.sleep(5)
        results_to_excel(results, max_stops=max_stops)
```
3.运行py文件，输出为output.xlsx

4.如果有报错提示，例如openpyxl等包未安装，使用pip安装即可。