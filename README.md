# Design-and-implement-ETL-data-clothing
- Project  crawl and process clothes data (detail of product, images).
- Get data from 3 website https://ivymoda.com/, https://coupletx.com/, https://gumac.vn/
- Apply multi thread to improve performance
- Usage:
python .\crawl_data_service.py --shop_name [CoupleTx|Gumac|Ivymoda] --path_save_data path_save_data --mode_crawl [CATEGORY|ALL|KEYWORD] --keyword Name_prodcut
- examples: + python .\crawl_data_service.py --shop_name Gumac --path_save_data D:\test_coupletx\ --mode_crawl KEYWORD --keyword Qu?n
           + python .\crawl_data_service.py --shop_name Ivymoda --path_save_data D:\test_ivymoda\ --mode_crawl CATEGORY
          + python .\crawl_data_service.py --shop_name CoupleTx --path_save_data D:\test_coupletx\ --mode_crawl ALL
        
