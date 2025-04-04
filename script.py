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

# Получение товаров

def get_products():
    url = f"{BASE_URL}/products.json?status=active&limit=5"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("products", [])

# Получение метафилдов

def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

# Генерация XML для Prom.ua

def generate_xml(products):
    yml = ET.Element("yml_catalog", date="2024-04-04")
    shop = ET.SubElement(yml, "shop")
    ET.SubElement(shop, "name").text = "Rubaska"
    ET.SubElement(shop, "company").text = "Rubaska"
    ET.SubElement(shop, "url").text = "https://rubaska.com"

    # Категории
    categories = ET.SubElement(shop, "categories")
    ET.SubElement(categories, "category", id="129880800", parentId="129880784").text = "Чоловічі сорочки"

    # Начинаем блок товаров
    offers = ET.SubElement(shop, "offers")

    if not products:
        return ET.ElementTree(yml)

    product = products[0]
    variant = product['variants'][0]
    product_metafields = get_metafields(product["id"])

    availability = "true" if variant.get("available", False) else "false"
    offer = ET.SubElement(offers, "offer", {
        "id": str(product["id"]),
        "available": availability,
        "in_stock": "true",
        "type": "vendor.model",
        "selling_type": "r",
        "group_id": "348"
    })

    # Назва
    title = product["title"] if product.get("title") else "Немає назви"
    name_text = f"{title} {variant['title']}"
    ET.SubElement(offer, "name").text = name_text

    # Название группы
    ET.SubElement(offer, "categoryId").text = "129880800"
    ET.SubElement(offer, "portal_category_id").text = "129880800"
    ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
    ET.SubElement(offer, "model").text = "Сорочка чоловіча"

    # Цена
    ET.SubElement(offer, "price").text = variant['price']
    ET.SubElement(offer, "currencyId").text = "UAH"

    # Фото
    for image in product.get("images", [])[:10]:
        if "src" in image:
            ET.SubElement(offer, "g:image_link").text = image["src"]

    # Описание
    description = product.get("body_html", "")
    if description:
        ET.SubElement(offer, "description").text = description

    # SKU -> vendorCode
    sku = variant.get("sku") or str(product["id"])
    ET.SubElement(offer, "vendorCode").text = sku

    # Размер
    ET.SubElement(offer, "g:size").text = variant["title"]

    # Состояние
    ET.SubElement(offer, "g:condition").text = "new"

    # Цвет из метафилдов
    color = "Невідомо"
    for metafield in product_metafields:
        if metafield.get("namespace") == "shopify" and metafield.get("key") == "color-pattern":
            color = metafield.get("value", "Невідомо").capitalize()
            break
    ET.SubElement(offer, "g:color").text = color

    return ET.ElementTree(yml)

if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид для Prom.ua успешно создан: feed.xml")
