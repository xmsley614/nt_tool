### 使用步骤
1. install requirements
```
pip install -r requirements.txt
```
2. in main.py set the conditions you want.
```python
    max_stops = 2
    origins = ['PVG','TYO', 'HKG']
    destinations = ['LAX','SFO','ORD']
    start_dt = datetime.strptime('2023-09-29', '%Y-%m-%d')
    end_dt = datetime.strptime('2023-09-29', '%Y-%m-%d')
    dates = date_range(start_dt, end_dt)
    #  means eco, pre, biz and first
    cabin_class = [
                   "RWDECO",
                   "RWDPRECC",
                   "RWDBUS",
                   "RWDFIRST",
    ]
    price_filter = {
        'quota': {
            'operator': '>=',
            'value': 1
        },
        # 'cabin_class': {
        #     'operator': 'in',
        #     'value': ['J', 'F']
        # },
        # 'is_mix': {
        #     'operator': '==',
        #     'value': False
        # }
    }
    seg_sorter = {
        'key': 'departure_time',  # only takes 'duration_in_all', 'stops', 'departure_time' and 'arrival_time'.
        'ascending': True
    }
```
3.Run main.py and you will see the output file.



If you like this project, welcome to buy me a coffee.

<a href="https://www.buymeacoffee.com/xmsley" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
