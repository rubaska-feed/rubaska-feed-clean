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

def get_products():
    url = f"{BASE_URL}/products.json?limit=5&status=active"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["products"]

def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", {"xmlns:g": "http://base.google.com/ns/1.0", "version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(channel, "link").text = "https://rubaska.prom.ua/"
    ET.SubElement(channel, "{http://base.google.com/ns/1.0}description").text = "RSS 2.0 product data feed"

    if not products:
        return ET.ElementTree(rss)

    product = products[0]
    variant = product["variants"][0]
    metafields = get_metafields(product["id"])

    item = ET.SubElement(channel, "item")
    sku = variant.get("sku") or str(product["id"])

    ET.SubElement(item, "{http://base.google.com/ns/1.0}id").text = sku
    ET.SubElement(item, "{http://base.google.com/ns/1.0}title").text = product.get("title", "Без назви")
    ET.SubElement(item, "{http://base.google.com/ns/1.0}description").text = product.get("body_html", "")
    ET.SubElement(item, "{http://base.google.com/ns/1.0}link").text = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

    for i, image in enumerate(product.get("images", [])):
        tag = "image_link" if i == 0 else "additional_image_link"
        ET.SubElement(item, f"{{http://base.google.com/ns/1.0}}{tag}").text = image["src"]

    # Цвет из метаобъекта
    color = "Невідомо"
    for mf in metafields:
        if mf.get("namespace") == "shopify" and mf.get("key") == "color":
            color = mf.get("value", "").strip().capitalize()
    ET.SubElement(item, "{http://base.google.com/ns/1.0}color").text = color

    # Видео
    for mf in metafields:
        if mf.get("namespace") == "custom" and mf.get("key") == "video_url":
            ET.SubElement(item, "{http://base.google.com/ns/1.0}video_link").text = mf.get("value")

    # Доступность
    availability = "in stock" if variant.get("inventory_quantity", 0) > 0 else "out of stock"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}availability").text = availability
    ET.SubElement(item, "{http://base.google.com/ns/1.0}price").text = f"{variant['price']} UAH"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}product_type").text = "одяг та взуття > чоловічий одяг > чоловічі сорочки"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}brand").text = product.get("vendor", "RUBASKA")
    ET.SubElement(item, "{http://base.google.com/ns/1.0}identifier_exists").text = "no"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}condition").text = "new"
    ET.SubElement(item, "{http://base.google.com/ns/1.0}size").text = variant.get("title", "M")

    # Постоянные характеристики
    static_details = [
        ("Країна виробник", "Туреччина"),
        ("Де_знаходиться_товар", "Одеса"),
        ("Назва_групи", "Чоловічі сорочки")
    ]
    for name, value in static_details:
        detail = ET.SubElement(item, "{http://base.google.com/ns/1.0}product_detail")
        ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_name").text = name
        ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_value").text = value

    return ET.ElementTree(rss)

if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
