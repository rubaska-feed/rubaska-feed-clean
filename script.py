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
    url = f"{BASE_URL}/products.json?limit=50&status=active"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["products"]


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

    product = products[0]
    variant = product['variants'][0]
    metafields = get_metafields(product["id"])

    availability = "true" if variant.get("inventory_quantity", 0) > 0 else "false"
    offer = ET.SubElement(channel, "offer", {
        "id": str(product["id"]),
        "available": availability,
        "in_stock": "true",
        "type": "vendor.model",
        "selling_type": "r"
    })

    # Назва
    title = product.get("title", "Немає назви")
    ET.SubElement(offer, "name").text = title
    ET.SubElement(offer, "g:title").text = title

    # SKU / Артикул
    sku = variant.get("sku") or str(product["id"])
    ET.SubElement(offer, "vendorCode").text = sku

    # Ссылка
    handle = product.get("handle", "")
    ET.SubElement(offer, "g:link").text = f"https://rubaska.com/products/{handle}"
    ET.SubElement(offer, "g:ads_redirect").text = f"https://rubaska.com/products/{handle}"

    # Описание
    ET.SubElement(offer, "description").text = product.get("body_html", "")
    ET.SubElement(offer, "description_ua").text = product.get("body_html", "")

    # Фото (все)
    for image in product.get("images", []):
        if "src" in image:
            ET.SubElement(offer, "picture").text = image["src"]

    # Цена
    ET.SubElement(offer, "price").text = f"{variant['price']}"

    # Бренд
    ET.SubElement(offer, "vendor").text = product.get("vendor", "")
    ET.SubElement(offer, "g:brand").text = product.get("vendor", "")

    # Стан
    ET.SubElement(offer, "g:condition").text = "new"

    # Размер
    ET.SubElement(offer, "g:size").text = variant.get("title", "")

    # Цвет из метафилдов
    color = "Невідомо"
    for mf in metafields:
        if mf.get("namespace") == "shopify" and mf.get("key") == "color-pattern":
            color = mf.get("value", "Невідомо").capitalize()
            break
    ET.SubElement(offer, "g:color").text = color

    # Тип товару
    product_type = product.get("product_type", "")
    ET.SubElement(offer, "g:product_type").text = product_type

    # Если это "Чоловічі сорочки", добавляем номер категории
    if product_type.strip().lower() == "чоловічі сорочки":
        ET.SubElement(offer, "categoryId").text = "129880800"

    return ET.ElementTree(rss)


if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
