## User Guide
### update Apr 13 2023
1. install requirements
```
pip install -r requirements.txt
```
2. In use_aa.py or use_ac.py or use_dl.py set the conditions you want. 
```python
    origins = ['HKG']
    destinations = ['KUL']
    start_dt = '2023-03-31'
    end_dt = '2023-03-31'
    dates = date_range(start_dt, end_dt)
    #  means eco, pre, biz and first
    cabin_class = [
        "ECO",
        "PRE",
        "BIZ",
        "FIRST"
    ]
    airbound_filter = AirBoundFilter(
        max_stops=1,
        airline_include=[],
        airline_exclude=['MH'],
    )
    price_filter = PriceFilter(
        min_quota=1,
        max_miles_per_person=999999,
        preferred_classes=[CabinClass.J, CabinClass.F, CabinClass.Y],
        mixed_cabin_accepted=True
    )
```
3. Run use_aa.py or use_ac.py and you will see the output file.

4. You can also run web_branch.py and go through with a web view. Currently the app wiil use both engines to search results.


If you like this project, welcome to buy me a coffee.

<a href="https://www.buymeacoffee.com/xmsley" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
