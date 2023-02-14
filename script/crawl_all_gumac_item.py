import re
import requests
import logging
import os
import json

# from crawl_data
from objects.item_gumac import ItemGumac

# INTERGRATE CRAWL ALL PRODUCT AND CRAWL BY CATGEGORY

class GumacCrawlByCategory:

    def __init__(self, keyword, path_save_data, mode: str = "CATEGORY"):
        # self.url_category = url_category
        self.mode_crawl = mode
        if self.mode_crawl == "CATEGORY":
            self.keyword = keyword
        else:
            self.keyword = "all_product"
        self.path_save_data = path_save_data
        # self.keyword =
        self.list_item_crawled = []
        self.number_link = 0
        self.page_current = 1
        self.load_list_item_crawled()
        self.number_page = self.get_number_total_page()

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
            print(f"GET LINK IN PAGE {self.page_current}")
            print(f"Number link of page {self.page_current}: {len(list_data_package_item)}")
            self.page_current +=1
            return list_data_package_item
        else:
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
        print(f" Total:{len(list_total)}")
        self.list_item_crawled = list_total
        # print(list_total)
        return self.list_item_crawled


def get_all_category_gumac():
    url = "https://cms.gumac.vn/api/v1/product-categories"
    response = requests.get(url)
    jsonformat = json.loads(response.text)
    list_cat = []
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

    # path = r"E:/test_gumac_category/"
    # list_url_category = get_all_category_gumac()
    # print(list_url_category)
    # for url_category in list_url_category:
    #     print(f"Crawler: {url_category} ")
    #     search = GumacCrawlByCategory(url_category, path)
    #     crawl = Crawler(search, ItemGumac, 5)
    #     crawl.start()
    #     crawl.join()
    #     print(f"DONE {url_category}")
    # time.sleep(60 * 10)

    path = r"E:/test_gumac_all_product/"
    search = GumacCrawlByCategory("all_product", path, "ALL")
    crawl = Crawler(search, ItemGumac, 1)
    crawl.start()
    crawl.join()


