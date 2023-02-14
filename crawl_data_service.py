import concurrent.futures
import json
import os
import random
import threading
import time
from queue import Queue
from threading import Thread
import logging
import argparse

from utils.utils import change_vpn, import_from_string
from config.config import Config


# SERVICE GET 3 ARGUMENT
# - SEARCH KEY SERVICE: GET LINK FOR PAGE WHICH USER CRAWL.
# - ITEM CLASS: STRUCTURE AND APPROACH CRAWL THIS PAGE.
# - NUMBER CRAWLER: NUMBER ITEM OF PAGE CRAWLING ON THE SAME TIME.

class Crawler(Thread):

    def __init__(self, search_key_service, item_class, number_crawler: int):
        super(Crawler, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.number_crawler = number_crawler
        self.item_class_web = item_class
        self.search_key_service = search_key_service
        self.path_save_data = self.search_key_service.path_save_data
        self.flag_finish = False
        self.flag_vpn = 0
        self.queue_item = Queue()
        self.chang_ip_time = 0
        self.queue_manage_crawler = Queue()
        self.number_item_crawl_successful = 0

    # GET ITEM IN QUEUES AND CRAWL
    def crawl(self):
        if not self.queue_item.qsize():
            self.queue_manage_crawler.get()
            return
        url = self.queue_item.get()
        item = self.item_class_web(url, self.search_key_service.keyword, self.path_save_data)
        status = ""
        if item.id in self.search_key_service.list_item_crawled:
            self.queue_manage_crawler.get()
            return
        try:
            # print(f"START CRAWL {item.id}")
            status = item.extract_data()
        except Exception as error:
            self.logger.error(f"ERROR IN {item.url}: {error}")
        try:
            item.driver.close()
        except:
            pass
        # CHECK WEBSITE BAN IP (FOR SHOPEE)
        if status == "VPN CHANGE":
            self.rotate_vpn()
            change_vpn()
            self.queue_manage_crawler.get()
            return
        self.search_key_service.list_item_crawled.append(item.id)
        self.number_item_crawl_successful += 1
        self.queue_manage_crawler.get()

    # CHANGE VPN IF WEBSITE BAN IP
    def rotate_vpn(self):
        if self.flag_vpn:
            return
        self.flag_vpn = 1
        change_vpn()
        self.flag_vpn = 0

    # def change_vpn(self):
    #     time.sleep(10)
    #     list_country = ["Viet nam", "Italy", "United States", "Spain", "Japan", "Taiwan", "Hong Kong"]
    #     country = random.choice(list_country)
    #     os.system("""nordvpn.lnk -c -g "{}" """.format(country))
    #     print(f"CONNECT VPN IN {country}")
    #     time.sleep(15)

    # GET LINK AND PUT TO QUEUE
    def manage_crawler(self):
        while True:
            if self.queue_item.qsize() < 2 * self.number_crawler:
                list_link = self.search_key_service.get_link_for_key()
                if list_link == "DONE":
                    self.flag_finish = True
                    break
                else:
                    for each in list_link:
                        self.queue_item.put(each)
            time.sleep(15)

    def thread_crawler(self):
        while True:
            if (not self.queue_item.qsize()) and (self.flag_finish == True):
                return
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.number_crawler) as executor:
                [executor.submit(self.crawl) for _ in range(self.number_crawler)]
            self.chang_ip_time += 1
            if self.chang_ip_time % 100 == 0:
                print("CHANGE VPN ")
                # self.rotate_vpn()
            time.sleep(5)

    # CREATE FOLDER TO SAVE DATA
    def create_folder_save_data(self):
        os.makedirs(self.path_save_data, exist_ok=True)

    def thread_manage_number_crawler(self):
        flag_notification = 0
        while self.queue_item.qsize() or not self.flag_finish:
            flag_notification += 1
            if self.queue_manage_crawler.qsize() < self.number_crawler:
                for _ in range(self.number_crawler):
                    if self.queue_manage_crawler.qsize() < self.number_crawler:
                        thread_request_next_page = threading.Thread(target=self.crawl)
                        thread_request_next_page.start()
                        self.queue_manage_crawler.put(1)
            if not(flag_notification % 30):
                self.logger.info(f"NUMBER ITEM CRAWLED SUCCESSFUL: {self.number_item_crawl_successful}")
            time.sleep(10)

        print("DONE THREAD CRAWLER")

    def run(self):
        self.logger.info(f"SERVICE GET KEY {self.search_key_service.__class__.__name__}")
        self.logger.info(f"ITEM CRAWL {self.item_class_web.class_name()}")
        self.create_folder_save_data()
        manage_crawler = threading.Thread(target=self.manage_crawler)
        manage_crawler.start()
        crawler = threading.Thread(target=self.thread_manage_number_crawler)
        crawler.start()
        crawler.join()
        manage_crawler.join()
        self.logger.info(f"FINISH CRAWL {self.number_item_crawl_successful} {self.item_class_web.class_name()} "
                         f"WITH KEYWORD {self.search_key_service.keyword}")


if __name__ == "__main__":
    # GUMAC OR IVYMODA OR COUPLETX
    file_class = json.load(open("crawler_config.json", "r", encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--shop_name", dest="shop_name", type=str, required=True)
    parser.add_argument("--path_save_data", dest= "path_save_data", type=str, required=True)
    parser.add_argument('--number_crawler', dest="number_crawler", default=5, type=int)
    parser.add_argument('--mode_crawl', dest="mode_crawl", default="CATEGORY")
    args = parser.parse_args()
    shop_name = args.shop_name
    search_service = import_from_string(file_class[shop_name]["search_link"])
    item_shop = import_from_string(file_class[shop_name]["format_item"])
    func_get_link = import_from_string(file_class[shop_name]["get_link_all_category"])
    if args.mode_crawl == "CATEGORY":
        print(f"MODE CRAWL: {args.mode_crawl}")
        list_key = func_get_link()
        print(list_key)
        for key in list_key:
            path = args.path_save_data
            search = search_service(key, path, mode_crawl=args.mode_crawl)
            crawl = Crawler(search, item_shop, args.number_crawler)
            crawl.start()
            crawl.join()
    elif args.mode_crawl == "ALL":
        print(f"MODE CRAWL: {args.mode_crawl}")
        path = args.path_save_data
        search = search_service("ALL", path, mode_crawl=args.mode_crawl)
        crawl = Crawler(search, item_shop, args.number_crawler)
        crawl.start()
        crawl.join()


    #python .\crawl_data_service.py --shop_name CoupleTx --path_save_data \\smb-ai.tmt.local\Public-AI\Public\Data\Clothing_shop\Coupletx_shop\test_coupletx\ --mode_crawl CATEGORY
