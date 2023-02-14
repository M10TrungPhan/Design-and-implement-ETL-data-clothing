import requests
import time
import os
import re
import json

from selenium.webdriver.common.by import By

from objects.item import Item
from utils.utils import setup_selenium_firefox
from class_element_website.class_element_gumac import ClassElementGumac


class ItemGumac(Item):

    def __init__(self, data_package_item: dict, keyword, path_save_data):
        super(ItemGumac, self).__init__(data_package_item)
        self.data_package_item = data_package_item
        self.id: str = str(data_package_item["id"])
        self.url = self.data_package_item["url"]
        self.class_element = ClassElementGumac()
        self.data_package_item = data_package_item
        self.keyword = keyword
        self.path_save_data = path_save_data
        self.driver = None
        self.main_information = None
        self.detail_information = None
        self.description = None
        self.feature_detail = None
        self.list_link_image = []
        self.image = []
        self.link_image_consultant = []
        self.image_consultant = None

    # def parse_html(self):
    #     return BeautifulSoup(self.driver.page_source, "lxml")

    def access_website(self):
        self.driver = setup_selenium_firefox()
        res = ""
        for _ in range(5):
            try:
                res = ""
                self.driver.get(self.url)
                # extension_path = r"D:\\trungphan\\backup_code\\crawl_data\\chromedriver_win32\\adblocker_ultimate-3.7.19.xpi"
                # self.driver.install_addon(extension_path, temporary=True)
                # time.sleep(1)
                # self.driver.close()
                # self.driver.switch_to.window(self.driver.window_handles[0])
                break
            except:
                res = None
                continue
        if res is None:
            self.driver.close()
            return None
        time.sleep(5)
        return True

    def get_main_information(self):
        main_information = {"màu_sắc": self.data_package_item["colors"], "size": self.data_package_item["sizes"]}
        try:
            main_information["name"] = self.driver.find_element(By.CLASS_NAME, self.class_element.name_item.
                                                                replace(" ", ".")).text
        except:
            pass

        try:
            main_information["giá_hiện_tại"] = self.driver.find_element(By.CLASS_NAME, self.class_element.current_price.
                                                                        replace(" ", ".")).text
        except:
            pass
        try:
            main_information["giá_gốc"] = self.driver.find_element(By.CLASS_NAME, self.class_element.initial_price.
                                                                   replace(" ", ".")).text
        except:
            pass

        return main_information

    def get_detail_information(self):
        try:
            self.turn_off_ads()
            table_detail_information = self.driver.find_element(By.CLASS_NAME, self.class_element.
                                                                table_detail_information.replace(" ", "."))
        except:
            return None
        self.turn_off_ads()
        list_detail_informations = table_detail_information.find_elements(By.TAG_NAME, "tr")
        detail_information = {}
        for detail_element in list_detail_informations:
            self.turn_off_ads()
            try:
                elements_p = detail_element.find_elements(By.TAG_NAME, "p")
                keys = elements_p[0].text.replace(" ", "_")
                values = elements_p[1].text
                # print(elements_p[0].text)
                detail_information[keys] = values
            except:
                continue
        return detail_information

    def get_description(self):
        try:
            self.turn_off_ads()
            box_descprition = self.driver.find_element(By.CLASS_NAME, "t-productDetailContent")
        except:
            return None
        # print(box_desciprtion.text)
        text_descriptions = ""
        self.turn_off_ads()
        list_element_p = box_descprition.find_elements(By.TAG_NAME, "p")
        # print(len(list_element_p))
        for each_p in list_element_p[1:]:
            self.turn_off_ads()
            content_text = each_p.text
            if content_text is not None:
                text_descriptions += content_text
        return text_descriptions

    def get_feature_detail(self):
        try:
            self.turn_off_ads()
            box_feature_detail = self.driver.find_element(By.CLASS_NAME, self.class_element.box_feature_detail)
        except:
            return None
        self.turn_off_ads()
        list_feature = box_feature_detail.find_elements(By.TAG_NAME, "li")
        text_feature_detail = []
        for each in list_feature:
            self.turn_off_ads()
            text_feature_detail.append(each.text)
        return text_feature_detail

    def get_image(self):
        list_url_image = []
        try:
            list_attribute = self.driver.find_elements(By.CLASS_NAME, value=self.class_element.box_button_color.
                                                       replace(" ", "."))
        except:
            return list_url_image
        for each in list_attribute:
            list_button_color = each.find_elements(By.CLASS_NAME,
                                                   value=self.class_element.button_color.replace(" ", "."))
            for each_button_color in list_button_color:
                try:
                    each_button_color.click()
                except:
                    continue
                time.sleep(1)
                list_image_color = self.driver.find_elements(By.CLASS_NAME,
                                                             value=self.class_element.box_image.replace(" ", "."))
                for each_image in list_image_color:
                    try:
                        box_image = each_image.find_element(By.TAG_NAME, "img")
                    except:
                        continue
                    url_image = box_image.get_attribute("src")
                    if url_image not in list_url_image:
                        list_url_image.append(url_image)
                        # print(url_image)
            return list_url_image

    def get_image_consultant(self):
        image_consultant = None
        try:
            box_consultant_size = self.driver.find_element(By.CLASS_NAME,
                                                           value=self.class_element.box_consultant_size.replace(" ", "."))

            box_consultant_size.find_element(By.TAG_NAME, "div").click()
        except:
            return image_consultant
        time.sleep(1)
        try:
            box_image_consultant = self.driver.find_element(By.CLASS_NAME,
                                                            self.class_element.box_image_consultant.replace(" ", "."))
            image_consultant = box_image_consultant.find_element(By.TAG_NAME, "img").get_attribute("src")
            # print(image_consultant)
        except:
            pass
        box_consultant_open = self.driver.find_element(By.CLASS_NAME, self.class_element.box_consultant_open)
        box_consultant_open.find_element(By.TAG_NAME, "button").click()
        return image_consultant

    def turn_off_ads(self):
        try:
            button_turn_off_ads = self.driver.find_element(By.CLASS_NAME, self.class_element.button_turn_off_ads)
            button_turn_off_ads.click()
            time.sleep(1)
        except:
            pass
        pass

    def create_folder_save_data(self):
        path_text = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text"
        os.makedirs(path_text, exist_ok=True)
        # path_image = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/image/" + str(self.id)
        # os.makedirs(path_image, exist_ok=True)

    def save_image(self):
        if not len(self.list_link_image):
            # print(self.image, self.url)
            return
        path_image = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/image/" + str(self.id)
        os.makedirs(path_image, exist_ok=True)
        for link_image in self.list_link_image:
            name_image = self.process_link_image(link_image)
            filename = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/image/" + str(
                self.id) + "/" + name_image
            with open(filename, 'wb') as f:
                f.write(requests.get(link_image).content)
            self.image.append(self.keyword.lower().replace(" ", "_") + "/image/" + str(
                self.id) + "/" + name_image)

    def save_image_consultant(self):
        if self.link_image_consultant is None:
            return
        name_image = self.process_link_image(self.link_image_consultant)
        path_image = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/image/" + str(self.id)
        os.makedirs(path_image, exist_ok=True)
        filename = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/image/" + str(
            self.id) + "/" + name_image
        with open(filename, 'wb') as f:
            f.write(requests.get(self.link_image_consultant).content)
        self.image_consultant = filename

    @staticmethod
    def process_link_image(link_image):
        regex_result = re.search(r"/(\w+-+\w+)+\.\w+$", link_image)
        if regex_result is not None:
            start, end = regex_result.span()
            return link_image[start + 1:]
        return None

    @property
    def dict_data(self):
        return {"_id": self.id,
                "url": self.url,
                "keyword": self.keyword,
                "main_information": self.main_information,
                "detail": self.detail_information,
                "feature_detail": self.feature_detail,
                "description": self.description,
                "image": self.image,
                "image_consultant_size": self.image_consultant}

    def save_text(self):
        path_text = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text"
        os.makedirs(path_text, exist_ok=True)
        file_data_folder = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text/" + str(self.id)
        # path_text = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text/"
        # os.makedirs(path_text, exist_ok=True)
        json.dump(self.dict_data, open(file_data_folder + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=4)

    def extract_information(self):
        # self.get_video_link()
        self.turn_off_ads()
        self.main_information = self.get_main_information()
        self.turn_off_ads()
        self.list_link_image = self.get_image()
        self.turn_off_ads()
        self.link_image_consultant = self.get_image_consultant()
        # print(self.list_color_img, self.image)
        javascript = "window.scrollBy(0,4000);"
        self.turn_off_ads()
        self.driver.execute_script(javascript)
        time.sleep(1)
        # self.driver.execute_script(javascript)
        # time.sleep(1)
        # self.driver.execute_script(javascript)
        time.sleep(1)
        self.turn_off_ads()
        self.description = self.get_description()
        self.detail_information = self.get_detail_information()
        if self.detail_information is not None:
            if "" in self.detail_information.keys():
                # print("XXXXXXXXXXX")
                print(self.url)
                self.driver.close()
                return False
        self.feature_detail = self.get_feature_detail()
        # print(self.dict_data)
        self.driver.close()
        return True

    def extract_data(self):
        # self.create_folder_save_data()
        if self.access_website() is None:
            print(f"LINK FAILED: {self.url}")
            self.driver.close()
            return
        result_extract_data = self.extract_information()
        if not result_extract_data:
            # print("OOOO")
            return
        self.save_image()
        self.save_image_consultant()
        self.save_text()
        return True
        # self.save_video()


if __name__ == "__main__":
    data_package = {'id': 55038, 'url': 'https://gumac.vn/ao-so-mi-nu-cong-so/ac09057', 'colors': ['Trắng'],
                    'sizes': ['XS', 'S', 'M', 'L', 'XL']}
    itemGumac = ItemGumac(data_package, "áo sơ mi", r"E:/test_gumac/")
    itemGumac.extract_data()
