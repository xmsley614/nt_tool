2023-04-19

1. Add wechat/sms notification. (`cp config.sample.py config.py` and replace
   the content)
2. Add results_to_csv method to store history searches.

2023-04-18

1. Add sound notification.
2. Get queries from a csv file, a query includes origin, destination, date
   range, and other options for filtering. Multiple queires are run as multi-processes.

2023-04-13

1. Add DL engine support. DL engine will only return first 20 results.
2. Use some way to filter results with the extremely high requirement of miles of AA and DL.
3. Minor bugs fixed.
4. Add connection time showing with from_to field.

2023-03-26

1. Update web client.
2. Remove some codes in use_aa.py since AA engine can not search Premium_Economy cabin. Instead, you can use price
   filter.
3. Re-arrange the structs of classes.

2023-03-20

1. Add airbound filter.
2. Remove useless parameter and vars.
