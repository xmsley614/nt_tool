## User Guide
### update Jun 1 2023
See update. [Update.md](https://github.com/xmsley614/nt_tool/blob/main/update.md)
###  Run project in Docker

1.Install [docker desktop](https://www.docker.com/products/docker-desktop/)

2.1 Create a docker-compose.yml file (preferably in a new work directory)

```
version: "3.8"
services:
  web:
    image: falantasw/nt-tool:${FILL ME WITH LATEST TAG}
    pull_policy: if_not_present
    ports:
      - 8050:8050
    volumes:
      - ./input:/code/input
      - ./output:/code/output
```
Visit [falanta's docker hub registry](https://hub.docker.com/repository/docker/falantasw/nt-tool/general) and update the image above with the latest tag. 

Sample compose file
```
version: "3.8"
services:
  web:
    image: falantasw/nt-tool:0.0.1
    pull_policy: if_not_present
    ports:
      - 8050:8050
    volumes:
      - ./input:/code/input
      - ./output:/code/output
```


2.2. Create an input directory and an output directory under the directory where the docker-compose.yml stays.

2.3. Use the input json as templates to create some input json files in the input directory you just created. 

3.If you are using linux or mac, open a terminal. If you are using windows, open a command prompt or PowerShell window. Navigate to the directory where you created the docker compose yaml file. Run the compose up command
```
docker-compose up
```
Note: make sure your docker desktop is running

4.1 If you would like to use the web UI search, open a browser and go to 
```
http://127.0.0.1:8050
```

4.2 If you would like to generate a excel output, you may use the following docker command
```
docker exec -i $(docker container ls --filter "ancestor=falantasw/nt-tool:0.0.1" --format "{{.ID}}" | head -n 1 | xargs) python /code/src/main.py ${FILL ME WITH AN AIRLINE} --input_file /code/input/${${FILL ME WITH YOU INPUT FILE NAME}} --output_dir /code/output/
```
Eligible airline functions
```
use_aa
use_dl
use_ac
```

A sample docker command looks like
```
docker exec -i $(docker container ls --filter "ancestor=tool:latest" --format "{{.ID}}" | head -n 1 | xargs) python /code/src/main.py use_aa --input_file /code/input/aa_or_dl_input.json --output_dir /code/output/
```




###  Run project in local 
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
