import re
import requests
import os
import json
import logging

# INTERGRATE CRAWL ALL PRODUCT AND CRAWL BY CATGEGORY


class GumacCrawlBySearch:

    def __init__(self, keyword, path_save_data, mode_crawl: str = "CATEGORY"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mode_crawl = mode_crawl
        if self.mode_crawl == "CATEGORY":
            self.keyword = keyword
            self.path_save_data = path_save_data + "Mode_category/"
            self.logger.info(f"SERVICE GET LINK GUMAC FOR CATEGORY {self.keyword}")
        elif self.mode_crawl == "KEYWORD":
            self.keyword = keyword
            self.path_save_data = path_save_data + "Mode_keyword/"
            self.logger.info(f"SERVICE GET LINK GUMAC FOR KEYWORD {self.keyword}")
        else:
            self.keyword = "all_product"
            self.path_save_data = path_save_data + "Mode_all_product/"
            self.logger.info(f"SERVICE GET ALL PRODUCT GUMAC")
        self.list_item_crawled = []
        self.number_link = 0
        self.page_current = 1
        self.load_list_item_crawled()
        self.number_page = self.get_number_total_page()

    def get_keyword_encoded(self):
        return "+".join(key for key in self.keyword.split())

    @staticmethod
    def process_url_category(url_category):
        result_regex = re.search(r"/(\w+-\w+)+$", url_category)
        if result_regex is None:
            return None
        start, end = result_regex.span()
        return url_category[start+1:end]

    def request_html_by_api(self, url):
        response = ""
        for _ in range(5):
            try:
                response = requests.get(url)
                break
            except Exception as e:
                print(e)
                response = None
                continue
        if response is None:
            return None
        jsonformat = json.loads(response.text)
        return jsonformat

    def get_number_total_page(self):
        if self.mode_crawl == "CATEGORY":
            url = f"https://cms.gumac.vn/api/v1/products?page=1&sort=created_date" \
                  f"&sort_order=desc&limit=16&category={self.keyword}"
        elif self.mode_crawl == "KEYWORD":
            url = f"https://cms.gumac.vn/api/v1/products?limit=10&page=1&keyword={self.get_keyword_encoded()}"
        else:
            url = "https://cms.gumac.vn/api/v1/products?page=1&sort=created_date&sort_order=desc&limit=16"
        data_about_page = self.request_html_by_api(url)["meta"]
        self.number_page = data_about_page["totalPages"]
        self.number_link = data_about_page["total"]
        return self.number_page

    @staticmethod
    def extract_color_item_api(data_color):
        list_color = []
        for each_color in data_color:
            list_color.append(each_color["name"])
        return list_color

    @staticmethod
    def extract_size_item_api(data_size):
        list_size = []
        for each_size in data_size:
            list_size.append(each_size["name"])
        return list_size

    def get_link_in_page_api(self, page):
        if self.mode_crawl == "CATEGORY":
            url = f"https://cms.gumac.vn/api/v1/products?page={page}" \
                  f"&sort=created_date&sort_order=desc&limit=16&category={self.keyword}"
        elif self.mode_crawl == "KEYWORD":
            url = f"https://cms.gumac.vn/api/v1/products?limit=10&page={page}&keyword={self.get_keyword_encoded()}"
        else:
            url = f"https://cms.gumac.vn/api/v1/products?page={page}&sort=created_date&sort_order=desc&limit=16"
        data_in_page = self.request_html_by_api(url)["data"]
        list_data_package_item = []
        for each_item in data_in_page:
            data_package = {"id": each_item["id"],
                            "url": "https://gumac.vn/" + each_item["category"]["slug"] + "/" + each_item["slug"],
                            "colors": self.extract_color_item_api(each_item["colors"]),
                            "sizes": self.extract_size_item_api(each_item["sizes"])}
            list_data_package_item.append(data_package)
        return list_data_package_item

    def get_link_for_key(self):
        if self.page_current <= self.number_page:
            list_data_package_item = self.get_link_in_page_api(self.page_current)
            self.logger.info(f"GET LINK IN PAGE {self.page_current}")
            self.logger.info(f"NUMBER LINK OF PAGE {self.page_current}: {len(list_data_package_item)}")
            self.page_current += 1
            return list_data_package_item
        else:
            self.logger.info(f"FINISHED GET ALL LINK")
            return "DONE"

    def load_list_item_crawled(self):
        file_data_folder = self.path_save_data + self.keyword.lower().replace(" ", "_") + "/text/"
        if os.path.exists(file_data_folder):
            list_item = os.listdir(file_data_folder)
            list_1 = [item.replace(".json", "") for item in list_item]
        else:
            list_1 = []
        list_total = list_1
        list_total = list(set(list_total))
        print(f"Total:{len(list_total)}")
        self.list_item_crawled = list_total
        self.logger.info(f"TOTAL ITEM CRAWLED IN STORAGE:{len(list_total)}")
        return self.list_item_crawled


def get_link_all_category():
    url = "https://cms.gumac.vn/api/v1/product-categories"
    list_cat = []
    response = None
    for _ in range(10):
        try:
            response = requests.get(url)
            if response is not None:
                break
        except:
            pass
    if response is None:
        return list_cat
    jsonformat = json.loads(response.text)
    for cat in jsonformat["data"]:
        list_cat.append(cat["slug"])
        if "children" in cat.keys():
            for child_cat in cat["children"]:
                # print(child_cat.keys())
                if "children" in child_cat.keys():
                    for child in child_cat["children"]:
                        list_cat.append(child["slug"])
                list_cat.append(child_cat["slug"])
    # print(len(list_cat))
    return list_cat


if __name__ == "__main__":
    print("GUMAC")
    path = r"E:\test_gumac\\"
    func_get_category = get_link_all_category
    link = func_get_category()
    search = GumacCrawlBySearch(keyword=link[1], path_save_data=path, mode_crawl="CATEGORY")
    print(search.number_page)
    while True:
        result = search.get_link_for_key()
        print(result)
        if result == "DONE":
            break




