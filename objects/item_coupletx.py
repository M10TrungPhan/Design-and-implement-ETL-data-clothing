import hashlib

import requests
import time
import os
import re
import json
import logging

from selenium.webdriver.common.by import By

from utils.utils import setup_selenium_firefox_mode_load_partly
from class_element_website.class_element_couple_tx import ClassCoupleTx
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from concurrent.futures import ALL_COMPLETED
from objects.item import Item


class ItemCoupleTx(Item):

    def __init__(self,  data_package_item: dict, keyword, path_save_data):
        super(ItemCoupleTx, self).__init__(data_package_item)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.url = data_package_item["url"]
        self.id = data_package_item["id"]
        self.keyword = keyword
        self.path_save_data = path_save_data
        self.class_element = ClassCoupleTx()
        self.driver = None
        self.main_information = None
        self.description_information = None
        self.detail_information = None
        self.reference_information = None
        self.technical_information = None
        self.dict_color_image = {}
        self.image = []
        self.list_color = []

    def access_website(self):
        self.driver = setup_selenium_firefox_mode_load_partly()
        res = ""
        for _ in range(5):
            try:
                self.driver.get(self.url)
                break
            except:
                res = None
        if res is None:
            return None
        time.sleep(1)
        return True

    def get_image_and_color(self):
        dict_color_image = {}
        try:
            box_color = self.driver.find_element(By.CLASS_NAME, self.class_element.box_main_information_2)
        except:
            return False
        button_select_image = box_color.find_elements(By.CLASS_NAME,
                                                      self.class_element.button_select_image.replace(" ", "."))
        for button in button_select_image:
            try:
                button.click()
                color = box_color.find_element(By.CLASS_NAME, "header").text
                # print(color)
                box_image_gallery = self.driver.find_element(By.CLASS_NAME,
                                                             self.class_element.box_image_gallery_1.replace(" ", "."))
                box_image_gallery = box_image_gallery.find_element(By.CLASS_NAME,
                                                                   self.class_element.box_image_gallery_2.replace(" ", "."))
                list_element_image = box_image_gallery.find_elements(By.TAG_NAME, "img")
                list_image = []
                for each_el in list_element_image:
                    link_image = each_el.get_attribute("src")
                    if re.search(r"https://product.hstatic.net/", link_image) is None:
                        continue
                    list_image.append(link_image)
                dict_color_image[color] = list_image
            except:
                pass
        if not len(dict_color_image.keys()):
            return False
        self.dict_color_image = dict_color_image
        self.list_color = list(dict_color_image.keys())
        return True

    def get_size(self, box_size_information):
        try:
            box_size = box_size_information.find_element(By.ID, self.class_element.box_size)
            list_element_size = box_size.find_elements(By.CLASS_NAME, self.class_element.element_size)
        except:
            return None
        list_size = []
        for each_size in list_element_size:
            size = each_size.text
            list_size.append(size)
        return list_size

    @staticmethod
    def process_price(price):
        if price is None:
            return None
        return int(price.replace("VND", "").replace(".", "").replace(",", "").strip())

    def get_price(self, box_price_and_name_item):
        try:

            box_price = box_price_and_name_item.find_element(By.CLASS_NAME,
                                                             self.class_element.box_price.replace(" ", "."))
            try:
                current_price_element = box_price.find_element(By.TAG_NAME, "span")
                current_price = current_price_element.text
            except:
                current_price = None
            try:
                initiate_price_element = box_price.find_element(By.TAG_NAME, "del")
                initiate_price = initiate_price_element.text
            except:
                initiate_price = None

            return {"giá_gốc": self.process_price(initiate_price),
                    "giá_hiện_tại": self.process_price(current_price)}
        except Exception as er:
            print(er)
            return None

    @staticmethod
    def get_name_item(box_price_and_name_item):
        name_item_element = box_price_and_name_item.find_element(By.TAG_NAME, "h1")
        if name_item_element is None:
            return None
        return name_item_element.text

    def get_main_information(self):
        main_information = {}
        try:
            box_price_and_name_item = self.driver.find_element(By.CLASS_NAME, self.class_element.box_main_information_1)

            main_information["name"] = self.get_name_item(box_price_and_name_item)
            main_information["price"] = self.get_price(box_price_and_name_item)
            main_information["màu_sắc"] = self.list_color
        except:
            return None
        try:
            box_size_information = self.driver.find_element(By.CLASS_NAME, self.class_element.box_main_information_2)
            main_information["size"] = self.get_size(box_size_information)
        except:
            pass
        return main_information

    def get_description(self):
        box_detail_information = self.driver.find_element(By.CLASS_NAME,
                                                          self.class_element.box_desc_and_detail.replace(" ", "."))
        description = ""
        list_element_description = box_detail_information.find_elements(By.TAG_NAME, "p")
        if not len(list_element_description):
            return None
        for each in list_element_description:
            description += each.text + "\n"
        return description.strip()

    def get_detail_information(self):
        detail_information = {}
        try:
            box_detail_information = self.driver.find_element(By.CLASS_NAME,
                                                              self.class_element.box_desc_and_detail.replace(" ", "."))
        except:
            return None
        list_element_detail = box_detail_information.find_elements(By.TAG_NAME, "li")
        for each in list_element_detail:
            detail = each.text
            regex_result = re.search(r"\w+:", detail)
            if regex_result is None:
                continue
            start, end = regex_result.span()
            detail_information[detail[:end - 1].strip().replace(" ", "_")] = detail[end:].strip()
        return detail_information

    def get_reference_information(self):
        try:
            box_reference_information = self.driver.find_element(By.CLASS_NAME,
                                                                 self.class_element.box_reference.replace(" ", "."))
            element_reference = box_reference_information.find_element(By.TAG_NAME, "ul")
        except:
            return None
        return element_reference.text

    def get_technical_information(self):
        technical_detail = {}
        try:
            box_technical_information = self.driver.find_elements(By.CLASS_NAME,
                                                                  self.class_element.box_technical.replace(" ", "."))
        except:
            return None
        if len(box_technical_information) < 2:
            return None
        element_rows = box_technical_information[1].find_elements(By.TAG_NAME, "tr")
        if len(element_rows) < 2:
            return None
        list_key = []
        for each_size in element_rows[0].find_elements(By.TAG_NAME, "td")[1:]:
            size_text = each_size.text
            list_key.append(size_text)
        for each_key in list_key:
            technical_detail[each_key] = {}
        for each_attribute in element_rows[1:]:
            list_col = each_attribute.find_elements(By.TAG_NAME, "td")
            name_attribute = list_col[0].text.strip().replace(" ", "_")
            list_detail = list_col[1:]
            for idx in range(len(list_detail)):
                technical_detail[list_key[idx]].update({name_attribute: list_detail[idx].text})
                # print(size_detail)
        if "+/-" in technical_detail.keys():
            del technical_detail["+/-"]
        return technical_detail

    @staticmethod
    def process_link_image(link_image: str):
        list_split = link_image.split("/")
        if re.search(r"\.\w+", list_split[-1]) is not None:
            return hashlib.md5(list_split[-1].encode("utf-8")).hexdigest()
        return hashlib.md5(link_image.encode("utf-8")).hexdigest()

    def save_images_for_color(self, color):
        list_image_of_color = []
        for link_image in self.dict_color_image[color]:
            try:
                name_image = color.replace(" ", "_") + "_" + self.process_link_image(link_image) + ".jpg"
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

    @property
    def dict_data(self):
        return {"_id": self.id,
                "url": self.url,
                "keyword": self.keyword,
                "main_information": self.main_information,
                "description": self.description_information,
                "detail_information": self.detail_information,
                "reference_information": self.reference_information,
                "technical_information": self.technical_information,
                "image": self.image}

    def save_text(self):
        path_text = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text"
        os.makedirs(path_text, exist_ok=True)
        file_data_folder = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text/" + str(self.id)
        json.dump(self.dict_data, open(file_data_folder + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=4)

    def extract_information(self):
        # self.get_images_and_color()
        try:
            if not self.get_image_and_color():
                return False
            self.main_information = self.get_main_information()
            if self.main_information is None:
                return False
            self.description_information = self.get_description()
            self.detail_information = self.get_detail_information()
            self.reference_information = self.get_reference_information()
            self.technical_information = self.get_technical_information()
        except:
            return False
        return True

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

