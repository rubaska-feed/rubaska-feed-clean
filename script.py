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
    url = f"{BASE_URL}/products.json?limit=5&status=active"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    products = response.json()["products"]
    return products


def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])


def generate_xml(products):
    rss = ET.Element("rss", attrib={"xmlns:g": "http://base.google.com/ns/1.0", "version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Інтернет-магазин Rubaska"
    ET.SubElement(channel, "link").text = "https://rubaska.prom.ua/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    if not products:
        return ET.ElementTree(rss)

    # Используем только первый активный товар
    product = products[0]
    variant = product['variants'][0]
    metafields = get_metafields(product["id"])

    availability = "true" if variant.get("inventory_quantity", 0) > 0 else "false"
    offer = ET.SubElement(channel, "offer", {
        "id": str(product["id"]),
        "available": availability,
        "in_stock": "true",
        "type": "vendor.model",
        "selling_type": "r",
        "group_id": "348"
    })

    # Название (name)
    ET.SubElement(offer, "name").text = product.get("title", "Назва відсутня")

    # Название на укр (name_ua)
    ET.SubElement(offer, "name_ua").text = product.get("title", "Назва відсутня")

    # Название как модель
    ET.SubElement(offer, "model").text = "Сорочка чоловіча"

    # Категория
    ET.SubElement(offer, "categoryId").text = "129880800"
    ET.SubElement(offer, "portal_category_url").text = "https://prom.ua/Muzhskie-rubashki"

    # Ссылка на товар
    ET.SubElement(offer, "g:link").text = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(offer, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

    # Фото (все изображения)
    for img in product.get("images", []):
        if img.get("src"):
            ET.SubElement(offer, "picture").text = img["src"]

    # Цена
    ET.SubElement(offer, "price").text = f"{variant['price']}"

    # Валюта
    ET.SubElement(offer, "currencyId").text = "UAH"

    # Код товара (SKU)
    sku = variant.get("sku") or str(product["id"])
    ET.SubElement(offer, "vendorCode").text = sku

    # Описание (в CDATA)
    description = product.get("body_html", "")
    desc_element = ET.SubElement(offer, "description")
    desc_element.text = f"<![CDATA[{description}]]>"

    # Описание укр
    desc_ua_element = ET.SubElement(offer, "description_ua")
    desc_ua_element.text = f"<![CDATA[{description}]]>"

    # Цвет из метафилда shopify.color-pattern
    color = "Невідомо"
    for field in metafields:
        if field.get("namespace") == "shopify" and field.get("key") == "color-pattern":
            color = field.get("value", "Невідомо").capitalize()
    ET.SubElement(offer, "color").text = color

    # Размер (международный)
    ET.SubElement(offer, "size").text = variant["title"]

    # Производитель
    ET.SubElement(offer, "vendor").text = product.get("vendor", "")

    # Состояние
    ET.SubElement(offer, "condition").text = "new"

    return ET.ElementTree(rss)


if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
