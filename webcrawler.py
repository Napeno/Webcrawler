from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import requests
import json
import csv

app = Flask(__name__)
socketio = SocketIO(app)

class TikiCrawler:
    def __init__(self):
        self.laptop_page_url = "https://tiki.vn/api/v2/products?limit=48&include=advertisement&aggregations=1&category=8095&page={}&urlKey=laptop"
        self.product_url = "https://tiki.vn/api/v2/products/{}"
        self.product_id_file = "./data/product-id.txt"
        self.product_data_file = "./data/product.txt"
        self.product_file = "./data/product.csv"
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
        }
        self.flatten_field = [
            "badges", "inventory", "categories", "rating_summary", "brand", 
            "seller_specifications", "current_seller", "other_sellers", 
            "configurable_options", "configurable_products", "specifications", 
            "product_links", "services_and_promotions", "promotions", 
            "stock_item", "installment_info"
        ]
        self.fieldnames = [
            "id", "master_id", "sku", "name", "url_key", "url_path", "short_url", 
            "type", "book_cover", "short_description", "price", "list_price", 
            "original_price", "badges", "badges_new", "tracking_info", "discount", 
            "discount_rate", "rating_average", "review_count", "review_text", 
            "favourite_count", "thumbnail_url", "has_ebook", "inventory_status", 
            "inventory_type", "productset_group_name", "is_fresh", "seller", 
            "is_flower", "has_buynow", "is_gift_card", "salable_type", "data_version", 
            "day_ago_created", "all_time_quantity_sold", "meta_title", 
            "meta_description", "meta_keywords", "is_baby_milk", "is_acoholic_drink", 
            "description"
        ]
        

    def log_message(self, message):
        socketio.emit('log', {'message': message})

    def crawl_product_id(self):
        product_list = []
        i = 1
        while True:
            self.log_message(f"Crawling page: {i}")
            response = requests.get(self.laptop_page_url.format(i), headers=self.headers)
            if response.status_code != 200:
                self.log_message("Failed to retrieve data or no more data available.")
                break

            products = response.json().get("data", [])
            if not products:
                self.log_message("No more products found.")
                break

            for product in products:
                product_id = str(product["id"])
                self.log_message(f"Product ID: {product_id}")
                product_list.append(product_id)

            i += 1

        self.log_message(f"Total pages crawled: {i - 1}")
        return product_list, i

    def save_product_id(self, product_list=[]):
        with open(self.product_id_file, "w+", encoding="utf-8") as file:
            file.write("\n".join(product_list))
        self.log_message(f"Product IDs saved to {self.product_id_file}")

    def crawl_product(self, product_list=[]):
        product_detail_list = []
        for product_id in product_list:
            self.log_message(f"Crawling product details for product ID: {product_id}")
            response = requests.get(self.product_url.format(product_id), headers=self.headers)
            if response.status_code == 200:
                product_detail_list.append(response.text)
                self.log_message(f"Successfully crawled product ID: {product_id}")
            else:
                self.log_message(f"Failed to retrieve details for product ID: {product_id}")
        return product_detail_list

    def adjust_product(self, product):
        try:
            e = json.loads(product)
            if "id" in e:
                for field in self.flatten_field:
                    if field in e:
                        e[field] = json.dumps(e[field], ensure_ascii=False).replace('\n', '')
                return {k: v for k, v in e.items() if k in self.fieldnames}
            return None
        except json.JSONDecodeError:
            self.log_message("Error decoding JSON for product")
            return None

    def save_raw_product(self, product_detail_list=[]):
        with open(self.product_data_file, "w+", encoding="utf-8") as file:
            for product in product_detail_list:
                file.write(product + '\n')
        self.log_message(f"Product details saved to {self.product_data_file}")

    def load_raw_product(self):
        with open(self.product_data_file, "r", encoding="utf-8") as file:
            return file.readlines()

    def save_product_list(self, product_json_list):
        with open(self.product_file, "w", newline='', encoding="utf-8") as file:
            csv_writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            csv_writer.writeheader()
            for p in product_json_list:
                if p is not None:
                    csv_writer.writerow(p)
        self.log_message(f"Product list saved to {self.product_file}")
    
class PhongVuCrawler:
    def __init__(self):
        self.product_url = "https://discovery.tekoapis.com/api/v1/product?sku={}&location=&terminalCode=phongvu"
        self.product_id_file = "./data/discovery-product-id.txt"
        self.product_data_file = "./data/discovery-product.txt"
        self.product_file = "./data/discovery-product.csv"
        self.fieldnames = ["SKU", "Name", "Brand", "Category", "Price", "Discount", "Image URL"]
        self.skus=[
    "240401677", "240200161", "240300076", "221000517", "240201287",
    "240100232", "240100231", "240502377", "240403798", "240403799",
    "240302748", "240300666", "240201291", "240502290", "230704076",
    "240201292", "240300072", "240201294", "240302543", "240301719",
    "240201833", "240201289", "240201288", "240201286", "220801877",
    "231004211", "231002103", "230702516", "220700044", "231103542",
    "231103658", "240201130", "1701363", "1701554", "230903484",
    "230903485", "230702670", "230903095", "230604092", "221200301"
    ]

    def log_message(self, message):
        socketio.emit('log', {'message': message})

    def fetch_product_data(self, sku):
        response = requests.get(self.product_url.format(sku))
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "0":
                return data.get("result", {}).get("product", {})
        return None

    

    def crawl_product(self):
        product_list = []
        for sku in self.skus:
            self.log_message(f"Crawling product details for SKU: {sku}")
            product_data = self.fetch_product_data(sku)
            if product_data:
                product_info = product_data.get("productInfo", {})
                prices = product_data.get("prices", [])
                product = {
                    "SKU": product_info.get("sku", ""),
                    "Name": product_info.get("name", ""),
                    "Brand": product_info.get("brand", {}).get("name", ""),
                    "Category": product_info.get("categories", [{}])[0].get("name", ""),
                    "Price": prices[0].get("latestPrice", "") if prices else "",
                    "Discount": prices[0].get("discountAmount", "") if prices else "",
                    "Image URL": product_info.get("imageUrl", "")
                }
                product_list.append(product)
                self.log_message(f"Successfully crawled SKU: {sku}")
            else:
                self.log_message(f"Failed to retrieve details for SKU: {sku}")
        return product_list

    def save_product_list(self, product_list):
        with open(self.product_file, "w", newline='', encoding="utf-8") as file:
            csv_writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            csv_writer.writeheader()
            for product in product_list:
                if product is not None:
                    csv_writer.writerow(product)
        self.log_message(f"Product list saved to {self.product_file}")

tiki_crawler = TikiCrawler()
discovery_crawler = PhongVuCrawler()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crawl/tiki', methods=['POST'])
def crawl_tiki():
    tiki_crawler.log_message("Starting Tiki data crawling process...")
    product_list, page = tiki_crawler.crawl_product_id()
    tiki_crawler.save_product_id(product_list)
    product_detail_list = tiki_crawler.crawl_product(product_list)
    tiki_crawler.save_raw_product(product_detail_list)
    product_json_list = [tiki_crawler.adjust_product(p) for p in product_detail_list if tiki_crawler.adjust_product(p)]
    tiki_crawler.save_product_list(product_json_list)
    tiki_crawler.log_message("Tiki data crawling process completed.")
    return jsonify({'status': 'success', 'message': 'Tiki data crawling completed.'})

@app.route('/crawl/discovery', methods=['POST'])
def crawl_discovery():
    discovery_crawler.log_message("Starting PhongVu data crawling process...")
    product_list = discovery_crawler.crawl_product()
    discovery_crawler.save_product_list(product_list)
    discovery_crawler.log_message("PhongVu data crawling process completed.")
    return jsonify({'status': 'success', 'message': 'PhongVu data crawling completed.'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
