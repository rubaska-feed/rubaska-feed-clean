import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

SHOP_NAME = "676c64"
API_VERSION = "2023-10"
TOKEN = os.getenv("SHOPIFY_API_TOKEN")

BASE_URL = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}"
HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json"
}

def get_products():
    url = f"{BASE_URL}/products.json?limit=1&status=active"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["products"]

def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")  # Регистрируем один раз
    rss = ET.Element("rss", {"version": "2.0"})  # ⚠️ Убираем xmlns:g отсюда
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(channel, "link").text = "https://rubaska.prom.ua/"
    ET.SubElement(channel, "{http://base.google.com/ns/1.0}description").text = "RSS 2.0 product data feed"

    if not products:
        return ET.ElementTree(rss)

    product = products[0]
    variant = product["variants"][0]
    product_metafields = get_metafields(product["id"])

    item = ET.SubElement(channel, "item")

    ET.SubElement(item, "{http://base.google.com/ns/1.0}id").text = str(product["id"])
    ET.SubElement(item, "{http://base.google.com/ns/1.0}title").text = product.get("title", "Без назви")
    ET.SubElement(item, "{http://base.google.com/ns/1.0}description").text = product.get("body_html", "")
    ET.SubElement(item, "{http://base.google.com/ns/1.0}link").text = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

    for i, image in enumerate(product.get("images", [])):
        if i == 0:
            ET.SubElement(item, "{http://base.google.com/ns/1.0}image_link").text = image["src"]
        else:
            ET.SubElement(item, "{http://base.google.com/ns/1.0}additional_image_link").text = image["src"]

    ET.SubElement(item, "{http://base.google.com/ns/1.0}availability").text = "in stock" if variant.get("inventory_quantity", 0) > 0 else "out of stock"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}price").text = f'{variant.get("price", "0")} UAH'
    ET.SubElement(item, "{http://base.google.com/ns/1.0}product_type").text = product.get("product_type", "")
    ET.SubElement(item, "{http://base.google.com/ns/1.0}brand").text = product.get("vendor", "RUBASKA")
    ET.SubElement(item, "{http://base.google.com/ns/1.0}identifier_exists").text = "no"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}condition").text = "new"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}size").text = variant.get("title", "M")

    # SKU
    sku = variant.get("sku") or str(product["id"])
    ET.SubElement(item, "{http://base.google.com/ns/1.0}vendorCode").text = sku

    # Цвет из Metaobjects: content > metaobject > color → title
    color = "Невідомо"
    for metafield in product_metafields:
        if metafield.get("namespace") == "color" and metafield.get("key") == "title":
            color = metafield.get("value", "Невідомо")
            break
    ET.SubElement(item, "{http://base.google.com/ns/1.0}color").text = color

    # Видео из custom.video_url
    video_url = ""
    for metafield in product_metafields:
        if metafield.get("namespace") == "custom" and metafield.get("key") == "video_url":
            video_url = metafield.get("value", "")
            break
    if video_url:
        ET.SubElement(item, "{http://base.google.com/ns/1.0}video_link").text = video_url

    # Постоянные характеристики
    constant_details = [
        ("Країна виробник", "Туреччина"),
        ("Де_знаходиться_товар", "Одеса"),
    ]
    for name, value in constant_details:
        detail = ET.SubElement(item, "{http://base.google.com/ns/1.0}product_detail")
        ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_name").text = name
        ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_value").text = value

    return ET.ElementTree(rss)

# Запуск
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
