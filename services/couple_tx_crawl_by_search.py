import re
import hashlib
import logging
import os
import time

from queue import Queue
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor

from class_element_website.class_element_couple_tx import ClassCoupleTx
from services.web_crawl_by_search import WebCrawlBySearch
from utils.utils import setup_selenium_firefox_mode_load_partly


class CoupleTxCrawlBySearch(WebCrawlBySearch):

    def __init__(self, keyword, path_save_data, mode_crawl: str = "KEYWORD"):
        super(CoupleTxCrawlBySearch, self).__init__(keyword, path_save_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.class_element = ClassCoupleTx()
        self.mode_crawl = mode_crawl
        if self.mode_crawl == "CATEGORY":
            self.url_category = keyword["url_category"]
            self.path_save_data = path_save_data + "Mode_category/"
            self.keyword = keyword["category"]
            self.logger.info(f"SERVICE GET LINK FOR CATEGORY {self.keyword} FROM COUPLE_TX")
        elif self.mode_crawl == "KEYWORD":
            self.keyword = keyword
            self.path_save_data = path_save_data + "Mode_keyword/"
            self.logger.info(f"SERVICE GET LINK FOR KEYWORD {self.keyword} FROM COUPLE_TX")
        else:
            self.keyword = "all_product"
            self.path_save_data = path_save_data + "Mode_all_product/"
            self.logger.info(f"SERVICE GET ALL PRODUCT COUPLE_TX")
            self.queue_link_category = Queue()
        self.list_item_crawled = []
        self.flag_status = False
        self.load_list_item_crawled()
        print(self.list_item_crawled)

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

    def get_link_in_page(self, driver: webdriver, url):
        list_link = []
        response = ""
        for _ in range(5):
            try:
                driver.get(url)
                break
            except Exception as e:
                self.logger.error(e)
                response = None
                continue
        if response is None:
            return False
        try:
            while True:
                list_element_link_item = driver.find_elements(By.CLASS_NAME, self.class_element.element_link_item)
                javascript = "window.scrollBy(0,20000);"
                driver.execute_script(javascript)
                time.sleep(2)
                list_element_link_item_new = driver.find_elements(By.CLASS_NAME,
                                                                  self.class_element.element_link_item)
                if len(list_element_link_item) == len(list_element_link_item_new):
                    break
            list_element_link_item = driver.find_elements(By.CLASS_NAME, self.class_element.element_link_item)
            for each_element in list_element_link_item:
                link = each_element.get_attribute("href")
                if link not in list_link:
                    list_link.append(link)
        except:
            return False
        list_packet_data = []
        for link in list_link:
            id_url = self.generate_id_from_url(link)
            if id_url in self.list_item_crawled:
                continue
            list_packet_data.append({"url": link, "id": id_url})

        return list_packet_data

    def get_keyword_encoded(self):
        return "+".join(key for key in self.keyword.split())

    def get_link_for_mode_keyword(self):
        url = f"https://coupletx.com/search?type=product&q={self.get_keyword_encoded()}"
        driver = setup_selenium_firefox_mode_load_partly()
        # extension_path = r"D:\\trungphan\\backup_code\\crawl_data\\chromedriver_win32\\adblocker_ultimate-3.7.19.xpi"
        # driver.install_addon(extension_path, temporary=True)
        # time.sleep(1)
        # while len(driver.window_handles) > 1:
        #     driver.close()
        # driver.switch_to.window(driver.window_handles[0])
        list_link = self.get_link_in_page(driver, url)
        driver.close()
        if not list_link:
            return []
        return list_link

    def get_link_for_mode_category(self):
        url = self.url_category
        driver = setup_selenium_firefox_mode_load_partly()
        # extension_path = r"D:\\trungphan\\backup_code\\crawl_data\\chromedriver_win32\\adblocker_ultimate-3.7.19.xpi"
        # driver.install_addon(extension_path, temporary=True)
        # time.sleep(1)
        # while len(driver.window_handles) > 1:
        #     driver.close()
        # driver.switch_to.window(driver.window_handles[0])
        list_link = self.get_link_in_page(driver, url)
        driver.close()
        if not list_link:
            return []
        return list_link

    @staticmethod
    def generate_id_from_url(url: str):
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    @staticmethod
    def get_all_category():
        driver = setup_selenium_firefox_mode_load_partly()
        dict_category = {}
        # extension_path = r"D:\\trungphan\\backup_code\\crawl_data\\chromedriver_win32\\adblocker_ultimate-3.7.19.xpi"
        # driver.install_addon(extension_path, temporary=True)
        # time.sleep(1)
        # while len(driver.window_handles) > 1:
        #     driver.close()
        # driver.switch_to.window(driver.window_handles[0])
        driver.get("https://coupletx.com/")
        box_menu = driver.find_element(By.CLASS_NAME, "main-nav text-center".replace(" ", "."))
        action = ActionChains(driver)
        box_menu = box_menu.find_element(By.TAG_NAME, "ul")
        all_children_by_css = box_menu.find_elements(By.XPATH, "li")
        for each_cat in all_children_by_css:
            name_big_cat = each_cat.find_element(By.TAG_NAME, "a").text
            if re.search(r"Hàng mới về|Nam|Nữ|Áo khoác|Trẻ em|Phụ kiện", each_cat.text, flags=re.IGNORECASE) is None:
                continue
            action.move_to_element(each_cat).perform()
            time.sleep(1)
            try:
                box_sub_cat = each_cat.find_element(By.TAG_NAME, "div").find_element(By.TAG_NAME, "ul")
                list_sub_cat_element = box_sub_cat.find_elements(By.XPATH, "li")
                for sub_element_cat in list_sub_cat_element:
                    domain_sub_cat = sub_element_cat.find_element(By.TAG_NAME, "a").text
                    if re.search(r"Lướt theo giá", domain_sub_cat, flags=re.IGNORECASE) is not None:
                        continue
                    try:
                        box_sub_cat_of_sub_element = sub_element_cat.find_element(By.TAG_NAME, "ul")
                        list_element = box_sub_cat_of_sub_element.find_elements(By.XPATH, "li")
                        for each_category in list_element:
                            name_category = f"{name_big_cat} {domain_sub_cat} {each_category.text}".replace(" ", "_")
                            link_category = each_category.find_element(By.TAG_NAME, "a").get_attribute("href")
                            dict_category[name_category] = link_category
                    except:
                        name_category = f"{name_big_cat} {domain_sub_cat}".replace(" ", "_")
                        link_category = sub_element_cat.find_element(By.TAG_NAME, "a").get_attribute("href")
                        dict_category[name_category] = link_category
            except:
                name_category = name_big_cat.replace(" ", "_")
                link_category = each_cat.find_element(By.TAG_NAME, "a").get_attribute("href")
                dict_category[name_category] = link_category
        driver.close()
        return [{"category": key, "url_category": value} for key, value in dict_category.items()]

    def get_link_for_mode_all_product(self):
        list_category = self.get_all_category()
        list_total_link = []
        for each_link in list(list_category):
            self.queue_link_category.put(each_link["url_category"])
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.worker_get_link_for_category) for _ in range(3)]
        for future in futures:
            list_total_link += future.result()
        return list_total_link

    def worker_get_link_for_category(self):
        list_total_link = []
        driver = setup_selenium_firefox_mode_load_partly()
        # extension_path = r"D:\\trungphan\\backup_code\\crawl_data\\chromedriver_win32\\adblocker_ultimate-3.7.19.xpi"
        # driver.install_addon(extension_path, temporary=True)
        # time.sleep(1)
        # while len(driver.window_handles) > 1:
        #     driver.close()
        # driver.switch_to.window(driver.window_handles[0])
        while self.queue_link_category.qsize():
            link_category = self.queue_link_category.get()
            list_link = self.get_link_in_page(driver, link_category)
            if not list_link:
                continue
            list_total_link += list_link
        driver.close()
        return list_total_link

    def get_link_for_key(self):
        if self.flag_status:
            self.logger.info(f"FINISHED GET ALL LINK")
            return "DONE"
        if self.mode_crawl == "KEYWORD":
            list_link = self.get_link_for_mode_keyword()
            self.flag_status = True
        elif self.mode_crawl == "CATEGORY":
            list_link = self.get_link_for_mode_category()
            self.flag_status = True
        else:
            list_link = self.get_link_for_mode_all_product()
            self.flag_status = True
        return list_link


def get_link_all_category():
    driver = setup_selenium_firefox_mode_load_partly()
    dict_category = {}
    # extension_path = r"D:\\trungphan\\backup_code\\crawl_data\\chromedriver_win32\\adblocker_ultimate-3.7.19.xpi"
    # driver.install_addon(extension_path, temporary=True)
    # time.sleep(1)
    # while len(driver.window_handles) > 1:
    #     driver.close()
    # driver.switch_to.window(driver.window_handles[0])
    driver.get("https://coupletx.com/")
    box_menu = driver.find_element(By.CLASS_NAME, "main-nav text-center".replace(" ", "."))
    action = ActionChains(driver)
    box_menu = box_menu.find_element(By.TAG_NAME, "ul")
    all_children_by_css = box_menu.find_elements(By.XPATH, "li")
    for each_cat in all_children_by_css:
        name_big_cat = each_cat.find_element(By.TAG_NAME, "a").text
        if re.search(r"Hàng mới về|Nam|Nữ|Áo khoác|Trẻ em|Phụ kiện", each_cat.text, flags=re.IGNORECASE) is None:
            continue
        action.move_to_element(each_cat).perform()
        time.sleep(1)
        try:
            box_sub_cat = each_cat.find_element(By.TAG_NAME, "div").find_element(By.TAG_NAME, "ul")
            list_sub_cat_element = box_sub_cat.find_elements(By.XPATH, "li")
            for sub_element_cat in list_sub_cat_element:
                domain_sub_cat = sub_element_cat.find_element(By.TAG_NAME, "a").text
                if re.search(r"Lướt theo giá", domain_sub_cat, flags=re.IGNORECASE) is not None:
                    continue
                try:
                    box_sub_cat_of_sub_element = sub_element_cat.find_element(By.TAG_NAME, "ul")
                    list_element = box_sub_cat_of_sub_element.find_elements(By.XPATH, "li")
                    for each_category in list_element:
                        name_category = f"{name_big_cat} {domain_sub_cat} {each_category.text}".replace(" ", "_")
                        link_category = each_category.find_element(By.TAG_NAME, "a").get_attribute("href")
                        dict_category[name_category] = link_category
                except:
                    name_category = f"{name_big_cat} {domain_sub_cat}".replace(" ", "_")
                    link_category = sub_element_cat.find_element(By.TAG_NAME, "a").get_attribute("href")
                    dict_category[name_category] = link_category
        except:
            name_category = name_big_cat.replace(" ", "_")
            link_category = each_cat.find_element(By.TAG_NAME, "a").get_attribute("href")
            dict_category[name_category] = link_category
    driver.close()
    return [{"category": key, "url_category": value} for key, value in dict_category.items()]


if __name__ == "__main__":
    # list_category = get_link_all_category()
    couple_tx = CoupleTxCrawlBySearch("Áo", "abc", mode_crawl="keyword")
    list_category = couple_tx.get_all_category()
    # list_category = [1]
    for cat in list_category:
        print("_____________________________________________")
        print(cat)
        couple_tx = CoupleTxCrawlBySearch(cat, "abc", mode_crawl="CATEGORY")
        while True:
            result = couple_tx.get_link_for_key()
            print(result)
            if result == "DONE":
                break
            print(len(result))

