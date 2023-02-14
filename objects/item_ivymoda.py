import requests
import time
import os
import re
import json
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from utils.utils import setup_selenium_firefox, setup_selenium_firefox_mode_load_partly
from class_element_website.class_element_ivymoda import ClassIvyModa
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from concurrent.futures import ALL_COMPLETED
from objects.item import Item


class ItemIvyModa(Item):

    def __init__(self,  data_package_item: dict, keyword, path_save_data):
        super(ItemIvyModa, self).__init__(data_package_item)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.url = data_package_item["url"]
        self.id = data_package_item["id"]
        self.keyword = keyword
        self.path_save_data = path_save_data
        self.class_element = ClassIvyModa()
        self.driver = None
        self.main_information = None
        self.introduction_information = None
        self.detail_information = None
        self.preserve_information = None
        self.dict_color_image = {}
        self.image = []
        self.list_color = []

    @staticmethod
    def setup_selenium_firefox_to_get_image():
        ser = Service(r"D:/trungphan/backup_code/crawl_data/chromedriver_win32/geckodriver.exe")
        firefox_options = FirefoxOptions()
        firefox_options.set_preference('devtools.jsonview.enabled', False)
        firefox_options.set_preference('dom.webnotifications.enabled', False)
        firefox_options.add_argument("--test-type")
        firefox_options.add_argument('--ignore-certificate-errors')
        firefox_options.add_argument('--disable-extensions')
        firefox_options.add_argument('disable-infobars')
        firefox_options.add_argument("--incognito")
        firefox_options.add_argument("--headless")
        firefox_options.set_capability("pageLoadStrategy", "eager")
        driver = webdriver.Firefox(service=ser, options=firefox_options)
        return driver

    def access_website(self):
        self.driver = setup_selenium_firefox_mode_load_partly()
        res = ""
        for _ in range(5):
            try:
                res = ""
                # extension_path = r"D:\\trungphan\\backup_code\\crawl_data\\chromedriver_win32\\adblocker_ultimate-3.7.19.xpi"
                # self.driver.install_addon(extension_path, temporary=True)
                # time.sleep(1)
                # self.driver.close()
                # self.driver.switch_to.window(self.driver.window_handles[0])
                self.driver.get(self.url)
                break
            except:
                res = None
                continue
        if res is None:
            self.driver.close()
            return None
        time.sleep(5)
        return True

    def get_images_and_color(self):
        dict_color = {}
        try:
            box_button_color = self.driver.find_element(By.CLASS_NAME, self.class_element.box_button_color)
            list_button_element = box_button_color.find_elements(By.TAG_NAME, "label")
        except:
            return False
        for idx in range(len(list_button_element)):
            try:
                box_button_color = self.driver.find_element(By.CLASS_NAME, self.class_element.box_button_color)
                list_button_element_to_click = box_button_color.find_elements(By.TAG_NAME, "label")
                list_button_element_to_click[idx].click()
                time.sleep(1)
                content_color = self.driver.find_element(By.CLASS_NAME, self.class_element.content_color).text
                color = "unknown"
                if content_color is not None:
                    color = self.process_content_color(content_color)
                try:
                    box_gallery_image = self.driver.find_element(By.CLASS_NAME, self.class_element.box_gallery_image.
                                                                 replace(" ", "."))
                    list_box_images = box_gallery_image.find_element(By.TAG_NAME, "div")\
                        .find_elements(By.TAG_NAME, "div")
                    list_image = []
                    for each in list_box_images:
                        try:
                            img_element = each.find_element(By.TAG_NAME, "img")
                        except:
                            continue
                        img = img_element.get_attribute("src")
                        # driver_image = setup_selenium_firefox()
                        # driver_image.get(img)
                        if img is not None:
                            list_image.append(img)
                    dict_color[color] = list_image
                except:
                    continue

            except:
                pass
        self.dict_color_image = dict_color
        self.list_color = list(dict_color.keys())
        # print(self.dict_color_image, self.list_color)
        return True

    def get_image_and_color_ver2(self):
        list_link_color = []
        dict_color = {}
        try:
            box_button_color = self.driver.find_element(By.CLASS_NAME, self.class_element.box_button_color)
            list_button_element = box_button_color.find_elements(By.TAG_NAME, "label")
        except:
            return False
        for each_element in list_button_element:
            try:
                link_color = each_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                list_link_color.append(link_color)
            except:
                continue
        if not len(list_link_color):
            return False
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(self.get_link_image_for_each_color, link_color)
                       for link_color in list_link_color]
            wait(futures, return_when=ALL_COMPLETED)
            for future in futures:
                result = future.result()
                if not result:
                    continue
                dict_color.update(future.result())
        if not len(list(dict_color.keys())):
            return False
        self.dict_color_image = dict_color
        self.list_color = list(dict_color.keys())
        # print(self.dict_color_image)
        # print(self.list_color)
        return True

    def get_link_image_for_each_color(self, link_color):
        driver_image = self.setup_selenium_firefox_to_get_image()
        dict_color = {}
        result_request = False
        for _ in range(3):
            try:
                driver_image.get(link_color)
                time.sleep(1)
                result_request = True
                break
            except:
                pass
        if not result_request:
            driver_image.close()
            return False
        color = "unknown"
        try:
            WebDriverWait(driver_image, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, self.class_element.content_color)))
            content_color = driver_image.find_element(By.CLASS_NAME, self.class_element.content_color).text
            if content_color is not None:
                color = self.process_content_color(content_color)
        except:
            pass
        try:
            WebDriverWait(driver_image, 30).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME,
                                                     self.class_element.box_gallery_image.replace(" ", "."))))
            box_gallery_image = driver_image.find_element(By.CLASS_NAME, self.class_element.box_gallery_image.
                                                          replace(" ", "."))
            list_box_images = box_gallery_image.find_element(By.TAG_NAME, "div") \
                .find_elements(By.TAG_NAME, "div")
            list_image = []
            for each in list_box_images:
                try:
                    img_element = each.find_element(By.TAG_NAME, "img")
                except:
                    continue
                img = img_element.get_attribute("src")
                if img is not None:
                    list_image.append(img)
        except:
            driver_image.close()
            return False
        dict_color[color] = list_image
        driver_image.close()
        # print(dict_color)
        return dict_color

    @staticmethod
    def process_content_color(content_color):
        regex_result = re.search(r"Màu sắc:", content_color)
        if regex_result is None:
            return content_color
        start, end = regex_result.span()
        return content_color[end:].strip()

    def get_price_item(self, box_main_information):

        try:
            box_price_information = box_main_information.find_element(By.CLASS_NAME,
                                                                      self.class_element.box_price_information)
        except:
            return None
        try:
            current_price = box_price_information.find_element(By.TAG_NAME, "b").text
        except:
            current_price = None
        try:
            initial_price = box_price_information.find_element(By.TAG_NAME, "del").text
        except:
            initial_price = None
        try:
            discount = box_price_information.find_element(By.TAG_NAME, "div").text
        except:
            discount = None
        # print(initial_price, current_price, discount)
        if (initial_price is None) and (current_price is None) and (discount is None):

            return None
        return {"giá_gốc": self.process_price(initial_price), "giá_hiện_tại": self.process_price(current_price),
                "giảm_giá": discount}

    @staticmethod
    def get_name_item(box_main_information):
        try:
            name_item_element = box_main_information.find_element(By.TAG_NAME, "h1")
        except:
            return None
        name_item = name_item_element.text
        if name_item is None:
            return None
        return name_item

    def get_size_item(self):
        list_size = []
        try:
            box_size = self.driver.find_element(By.CLASS_NAME, self.class_element.box_size)
        except:
            return list_size
        element_size = box_size.find_elements(By.TAG_NAME, "label")
        for each_size in element_size:
            size = each_size.text
            if size is not None:
                list_size.append(size)
        return list_size

    def get_main_information(self):
        main_information = {"màu_sắc": self.list_color}
        try:
            box_main_information = self.driver.find_element(By.CLASS_NAME,
                                                            self.class_element.box_main_information.replace(" ", "."))
        except:
            return None
        # GET NAME
        name_item = self.get_name_item(box_main_information)
        # GET PRICE
        price = self.get_price_item(box_main_information)
        # GET SIZE
        size = self.get_size_item()
        main_information["name"] = name_item
        main_information["price"] = price
        main_information["size"] = size
        return main_information

    @staticmethod
    def process_price(price):
        if price is None:
            return None
        return int(price.replace("đ", "").replace(".", "").strip())

    def show_more_information(self):
        box_show_more_information = self.driver.find_element(By.CLASS_NAME,
                                                             self.class_element.box_show_more_information)
        box_show_more_information.find_element(By.TAG_NAME, "a").click()

    def get_introduction_information(self, tab_select):
        tab_select[0].click()
        self.show_more_information()
        time.sleep(1)
        content_introduction = ""
        try:
            box_introduction_information = self.driver.find_element(By.CLASS_NAME,
                                                                    self.class_element.box_introduction_information.
                                                                    replace(" ", "."))
        except:
            return None
        element_paragraph = box_introduction_information.find_elements(By.TAG_NAME, "p")
        for each_paragraph in element_paragraph:
            content_paragraph = each_paragraph.text
            if content_paragraph is not None:
                content_introduction += content_paragraph + "\n"
        return content_introduction

    def get_detail_information(self, tab_select):
        tab_select[1].click()
        self.show_more_information()
        time.sleep(1)
        detail_information = {}
        try:
            box_detail_information = self.driver.find_element(By.CLASS_NAME,
                                                              self.class_element.box_detail_information.
                                                              replace(" ", "."))
        except:
            return None
        list_element_detail = box_detail_information.find_elements(By.TAG_NAME, "tr")
        for each_detail in list_element_detail:
            elements = each_detail.find_elements(By.TAG_NAME, "td")
            keys = elements[0].text
            values = elements[1].text
            if (keys is not None) and (values is not None):
                detail_information[keys.replace(" ", "_")] = values
        return detail_information

    def get_preserve_information(self, tab_select):
        tab_select[2].click()
        self.show_more_information()
        time.sleep(1)
        content_preserve = ""
        try:
            box_preserve_information = self.driver.find_element(By.CLASS_NAME,
                                                                self.class_element.box_preserve_information.
                                                                replace(" ", "."))
        except:
            return None
        element_paragraph = box_preserve_information.find_elements(By.TAG_NAME, "p")
        for each_paragraph in element_paragraph:
            # print(each_paragraph.text)
            content_paragraph = each_paragraph.text
            if content_paragraph is not None:
                content_preserve += content_paragraph + "\n"
        return content_preserve

    def extract_more_information(self):
        try:
            box_select_tab_information = self.driver.find_element(By.CLASS_NAME,
                                                                  self.class_element.box_select_tab_information)
            tab_select = box_select_tab_information.find_elements(By.TAG_NAME, "div")
        except:
            return False
        self.introduction_information = self.get_introduction_information(tab_select)
        self.detail_information = self.get_detail_information(tab_select)
        self.preserve_information = self.get_preserve_information(tab_select)
        if ((self.introduction_information is None) and (self.detail_information is None) and
                (self.preserve_information is None)):
            return False
        return True

    def extract_information(self):
        # self.get_images_and_color()
        try:
            if not self.get_image_and_color_ver2():
                return False
            self.main_information = self.get_main_information()
            if self.main_information is None:
                return False
            if not self.extract_more_information():
                return False
            return True
        except:
            return False

    @staticmethod
    def process_link_image(link_image):
        regex_result = re.search(r"/\w+\.\w+$", link_image)
        if regex_result is not None:
            start, end = regex_result.span()
            return link_image[start + 1:]
        return link_image

    def save_images_for_color(self, color):
        list_image_of_color = []
        for link_image in self.dict_color_image[color]:
            try:
                name_image = color.replace(" ", "_") + "_" + self.process_link_image(link_image)
                filename = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/image/" + str(
                    self.id) + "/" + name_image
                with open(filename, 'wb') as f:
                    f.write(requests.get(link_image).content)
                list_image_of_color.append(self.keyword.lower().replace(" ", "_") + "/image/" + str(
                    self.id) + "/" + name_image)
            except:
                pass
        return list_image_of_color

    def save_image(self):
        if not len(self.dict_color_image.keys()):
            # print(self.image, self.url)
            return
        path_image = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/image/" + str(self.id)
        os.makedirs(path_image, exist_ok=True)
        with ThreadPoolExecutor(5) as executor:
            futures = [executor.submit(self.save_images_for_color,color) for color in self.dict_color_image.keys()]
            wait(futures, return_when=ALL_COMPLETED)
            for future in futures:
                list_image = future.result()
                for each_image in list_image:
                    self.image.append(each_image)
        # print(self.image)

        # for color in self.dict_color_image.keys():
        #     for link_image in self.dict_color_image[color]:
        #         name_image = color.replace(" ", "_") + "_" + self.process_link_image(link_image)
        #         filename = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/image/" + str(
        #             self.id) + "/" + name_image
        #         with open(filename, 'wb') as f:
        #             f.write(requests.get(link_image).content)
        #         self.image.append(self.keyword.lower().replace(" ", "_") + "/image/" + str(
        #             self.id) + "/" + name_image)

    @property
    def dict_data(self):
        return {"_id": self.id,
                "url": self.url,
                "keyword": self.keyword,
                "main_information": self.main_information,
                "introduction_information": self.introduction_information,
                "detail_information": self.detail_information,
                "preserve_information": self.preserve_information,
                "image": self.image}

    def save_text(self):
        path_text = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text"
        os.makedirs(path_text, exist_ok=True)
        file_data_folder = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text/" + str(self.id)
        json.dump(self.dict_data, open(file_data_folder + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=4)

    def extract_data(self):
        if self.access_website() is None:
            print(f"LINK FAILED: {self.url}")
            self.driver.close()
            return False
        result_extract_information = self.extract_information()
        if not result_extract_information:
            print(f"LINK FAILED: {self.url}")
            self.driver.close()
            return False
        self.save_image()
        self.save_text()
        self.driver.close()
        # print("SUCCESSFUL")
        return True


if __name__ == "__main__":
    pass