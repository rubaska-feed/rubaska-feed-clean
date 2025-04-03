import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

SHOP_NAME = "676c64"
API_VERSION = "2023-10"
TOKEN = os.getenv("SHOPIFY_API_TOKEN")

BASE_URL = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json"
}

# Step 1: Get products
def get_products():
    url = f"{BASE_URL}/products.json?limit=5"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["products"]

# Step 2: Generate XML

def generate_xml(products):
    rss = ET.Element("rss", attrib={"xmlns:g": "http://base.google.com/ns/1.0", "version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Інтернет-магазин Rubaska"
    ET.SubElement(channel, "link").text = "https://rubaska.com/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    for product in products:
        variant = product['variants'][0]  # берем первый вариант (например, размер M)
        item = ET.SubElement(channel, "item")

        ET.SubElement(item, "g:id").text = str(product["id"])
        ET.SubElement(item, "g:title").text = product["title"]
        ET.SubElement(item, "g:description").text = product["body_html"]
        ET.SubElement(item, "g:link").text = f"https://rubaska.com/products/{product['handle']}"
        ET.SubElement(item, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"
        ET.SubElement(item, "g:image_link").text = product["image"]["src"] if product.get("image") else ""
        ET.SubElement(item, "g:availability").text = "in stock"
        ET.SubElement(item, "g:price").text = f"{variant['price']} UAH"
        ET.SubElement(item, "g:product_type").text = product["product_type"]
        ET.SubElement(item, "g:brand").text = product["vendor"]
        ET.SubElement(item, "g:identifier_exists").text = "no"
        ET.SubElement(item, "g:condition").text = "new"

    return ET.ElementTree(rss)

if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
