import re

import hashlib
import requests
import logging
import os
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from services.web_crawl_by_search import WebCrawlBySearch
from class_element_website.class_element_ivymoda import ClassIvyModa
from bs4 import BeautifulSoup
from utils.utils import setup_selenium_firefox, setup_selenium_firefox_mode_load_partly


class IvyModaCrawlBySearch(WebCrawlBySearch):

    def __init__(self, keyword, path_save_data, mode_crawl: str = "KEYWORD"):
        super(IvyModaCrawlBySearch, self).__init__(keyword, path_save_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.class_element = ClassIvyModa()
        self.mode_crawl = mode_crawl
        self.flag_status = False
        if self.mode_crawl == "CATEGORY":
            self.url_category = keyword
            self.path_save_data = path_save_data + "Mode_category/"
            self.keyword = self.process_url_category(self.url_category)
            self.logger.info(f"SERVICE GET LINK FOR CATEGORY {self.keyword}")
            self.page_current = 1
            self.number_page = self.get_number_total_page()
            self.logger.info(f"NUMBER PAGE GET LINK OF KEYWORD {self.keyword} IS: {self.number_page}")
        elif self.mode_crawl == "KEYWORD":
            self.keyword = keyword
            self.path_save_data = path_save_data + "Mode_keyword/"
            self.logger.info(f"SERVICE GET LINK FOR KEYWORD {self.keyword}")
            self.page_current = 1
            self.number_page = self.get_number_total_page()
            self.logger.info(f"NUMBER PAGE GET LINK OF KEYWORD {self.keyword} IS: {self.number_page}")
        else:
            self.keyword = "all_product"
            self.queue_link_category = Queue()
            self.path_save_data = path_save_data + "Mode_all_product/"
            self.logger.info(f"SERVICE GET ALL PRODUCT IVYMODA")
        self.list_item_crawled = []
        self.load_list_item_crawled()

    @staticmethod
    def process_url_category(url_category):
        result_regex = re.search(r"/(\w+-?)+$", url_category)
        if result_regex is None:
            return "Unknown"
        start, end = result_regex.span()
        return url_category[start + 1:end]

    def load_list_item_crawled(self):
        file_data_folder = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text/"
        if os.path.exists(file_data_folder):
            list_item = os.listdir(file_data_folder)
            list_1 = [item.replace(".json", "") for item in list_item]
        else:
            list_1 = []
        list_total = list_1
        list_total = list(set(list_total))
        self.logger.info(f"TOTAL ITEM CRAWLED IN STORAGE:{len(list_total)}")
        self.list_item_crawled = list_total
        return self.list_item_crawled

    def get_keyword_encoded(self):
        return "+".join(key for key in self.keyword.split())

    def request_html(self, url):
        response = ""
        for _ in range(5):
            try:
                response = requests.get(url)
                break
            except Exception as e:
                self.logger.error(e)
                response = None
                continue
        if response is None:
            return None
        return self.parse_response(response)

    @staticmethod
    def parse_response(response):
        return BeautifulSoup(response.text, "lxml")

    def get_number_total_page(self):
        if self.mode_crawl =="KEYWORD":
            url = f"https://ivymoda.com/timkiem?q={self.get_keyword_encoded()}"
        elif self.mode_crawl == "CATEGORY":
            url = self.url_category
        else:
            return
        data_about_page = self.request_html(url)
        element_last_page = data_about_page.find("li", class_=self.class_element.last_page)
        if element_last_page is None:
            return 1
        link_last_page = element_last_page.find("a").get("href")
        number_page = self.extract_last_number_page(link_last_page)
        if number_page is None:
            return 1
        return int(number_page)

    @staticmethod
    def extract_last_number_page(link_last_page):
        result_regex = re.search(r"/page/\d+|/\d+\?", link_last_page)
        if result_regex is None:
            return None
        start, end = result_regex.span()
        string_page = link_last_page[start:end]
        result_regex = re.search(r"\d+", string_page)
        if result_regex is None:
            return None
        start, end = result_regex.span()
        return string_page[start:end]

    @staticmethod
    def extract_id_item_from_url(url_item):
        regex_result = re.search(r"ms-\w+", url_item)
        if regex_result is None:
            return hashlib.md5(url_item.encode("utf-8")).hexdigest()
        start, end = regex_result.span()
        string_id = url_item[start:end]
        regex_result = re.search(r"-\w+", string_id)
        if regex_result is None:
            return hashlib.md5(url_item.encode("utf-8")).hexdigest()
        start, end = regex_result.span()
        id_item = string_id[start+1:end]
        if len(id_item) < 6:
            return hashlib.md5(url_item.encode("utf-8")).hexdigest()
        if re.search(r"\d+x\d+", id_item) is not None:
            return hashlib.md5(url_item.encode("utf-8")).hexdigest()
        return id_item

    def get_link_in_page(self, page):
        if self.mode_crawl == "KEYWORD":
            url = f"https://ivymoda.com/tim-kiem/page/{page}?q={self.get_keyword_encoded()}"
        elif self.mode_crawl == "CATEGORY":
            url = self.url_category + f"/{page}"
        data_in_page = self.request_html(url)
        list_link_product = []
        list_product_element = data_in_page.find_all("div", class_=self.class_element.box_item_gallery)
        for each_item in list_product_element:
            element_link = each_item.find("a")
            if element_link is None:
                continue
            link = element_link.get("href")
            id_item = self.extract_id_item_from_url(link)
            if link is None:
                continue
            list_link_product.append({"id": id_item, "url": link})
        return list_link_product

    def get_link_for_key(self):
        if self.flag_status:
            self.logger.info(f"FINISHED GET ALL LINK")
            return "DONE"
        if self.mode_crawl == "CATEGORY" or self.mode_crawl == "KEYWORD":
            if self.page_current <= self.number_page:
                list_link = self.get_link_in_page(self.page_current)
                self.logger.info(f"GET LINK IN PAGE {self.page_current}")
                self.logger.info(f"NUMBER LINK OF PAGE {self.page_current}: {len(list_link)}")
                self.page_current += 1
                return list_link
            else:
                self.flag_status = True
        else:
            list_link = self.get_link_for_mode_all_product()
            self.flag_status = True
            return list_link

    @staticmethod
    def get_all_category():
        driver = setup_selenium_firefox()
        url = "https://ivymoda.com/"
        driver.get(url)
        box_menu = driver.find_element(By.CLASS_NAME, "menu")
        action = ActionChains(driver)
        list_link_category = []
        all_children_by_css = box_menu.find_elements(By.XPATH, "li")
        for each_cat in all_children_by_css:
            if re.search(r"NAM|NỮ|TRẺ EM| SALE TẾT", each_cat.text, flags=re.IGNORECASE) is None:
                continue
            action.move_to_element(each_cat).perform()
            time.sleep(1)
            list_link_element = each_cat.find_elements(By.TAG_NAME, "a")
            for each_category in list_link_element:
                link_category = each_category.get_attribute("href")
                if re.search("https://ivymoda.com", link_category) is None:
                    continue
                list_link_category.append(link_category)
        driver.close()
        return list_link_category

    def get_link_for_mode_all_product(self):
        list_category_link = self.get_all_category()
        list_total_link = []
        for each_link in list(list_category_link):
            self.queue_link_category.put(each_link)
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.worker_get_link_for_category) for _ in range(3)]
        for future in futures:
            list_total_link += future.result()

        # print(len(list(set(list_total_link))))
        list_total_link_2 = []
        list_id_post = []
        for each in list_total_link:
            if each["id"] not in list_id_post:
                list_id_post.append(each["id"])
                list_total_link_2.append(each)
        print(len(list_total_link))
        print(len(list_total_link_2))
        return list_total_link_2

    def get_all_item_for_category(self, url):
        list_total_link_category = []
        data_about_page = self.request_html(url)
        element_last_page = data_about_page.find("li", class_=self.class_element.last_page)
        if element_last_page is None:
            number_page_of_category = 1
        else:
            link_last_page = element_last_page.find("a").get("href")
            number_page = self.extract_last_number_page(link_last_page)
            if number_page is None:
                number_page_of_category = 1
            else:
                number_page_of_category = int(number_page)
        for page in range(1, number_page_of_category+1):
            url_category = url + f"/{page}"
            data_in_page = self.request_html(url_category)
            list_link_product = []
            list_product_element = data_in_page.find_all("div", class_=self.class_element.box_item_gallery)
            for each_item in list_product_element:
                element_link = each_item.find("a")
                if element_link is None:
                    continue
                link = element_link.get("href")
                id_item = self.extract_id_item_from_url(link)
                if link is None:
                    continue
                list_link_product.append({"id": id_item, "url": link})
            list_total_link_category += list_link_product
        return list_total_link_category

    def worker_get_link_for_category(self):
        list_total_link = []
        # extension_path = r"D:\\trungphan\\backup_code\\crawl_data\\chromedriver_win32\\adblocker_ultimate-3.7.19.xpi"
        # driver.install_addon(extension_path, temporary=True)
        # time.sleep(1)
        # while len(driver.window_handles) > 1:
        #     driver.close()
        # driver.switch_to.window(driver.window_handles[0])
        while self.queue_link_category.qsize():
            link_category = self.queue_link_category.get()
            list_link = self.get_all_item_for_category(link_category)
            if not list_link:
                continue
            list_total_link += list_link
        return list_total_link


def get_link_all_category():
    driver = setup_selenium_firefox()
    url = "https://ivymoda.com/"
    driver.get(url)
    box_menu = driver.find_element(By.CLASS_NAME, "menu")
    action = ActionChains(driver)
    list_link_category = []
    all_children_by_css = box_menu.find_elements(By.XPATH, "li")
    for each_cat in all_children_by_css:
        if re.search(r"NAM|NỮ|TRẺ EM| SALE TẾT", each_cat.text, flags=re.IGNORECASE) is None:
            continue
        action.move_to_element(each_cat).perform()
        time.sleep(1)
        list_link_element = each_cat.find_elements(By.TAG_NAME, "a")
        for each_category in list_link_element:
            link_category = each_category.get_attribute("href")
            if re.search("https://ivymoda.com", link_category) is None:
                continue
            list_link_category.append(link_category)
    driver.close()
    return list_link_category


if __name__ == "__main__":
    # list_category = get_link_all_category()
    list_category = [1]
    # print(list_category)
    # print(len(list_category))
    for cat in list_category:
        # print(cat)
        ivymoda = IvyModaCrawlBySearch("all", "abc", mode_crawl="ALL")
        # print(ivymoda.get_number_total_page())
        # print(ivymoda.number_page)
        while True:
            result = ivymoda.get_link_for_key()
            print(result)
            if result == "DONE":
                break

