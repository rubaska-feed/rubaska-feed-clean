import json
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
    url = f"{BASE_URL}/products.json?limit=5&status=active"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["products"]

# Получение метафилдов товара
def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

# Получение метафилдов варианта
def get_variant_metafields(variant_id):
    url = f"{BASE_URL}/variants/{variant_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

# Получение перевода описания на украинский
def get_translation(product_id, locale="uk"):
    url = f"{BASE_URL}/translations/products/{product_id}/{locale}.json"
    response = requests.get(url, headers=HEADERS)
    if response.ok:
        data = response.json()
        translations = data.get("translation", {})
        body = translations.get("body_html", "").strip()
        if body:
             if body:
    return ""


# Генерация XML-фида
def generate_xml(products):
    import json
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(channel, "link").text = "https://rubaska.com/"
    ET.SubElement(channel, "{http://base.google.com/ns/1.0}description").text = "RSS 2.0 product data feed"

    if not products:
        return ET.ElementTree(rss)

    product = products[0]
    variant = product["variants"][0]
    product_metafields = get_metafields(product["id"])
    variant_metafields = get_variant_metafields(variant["id"])

    available = "true" if variant.get("inventory_quantity", 0) > 0 else "false"
    safe_id = int(product["id"]) % 2147483647  # Безопасный ID для Prom.ua

    # Категории
    categories = ET.SubElement(channel, "categories")
    ET.SubElement(categories, "category", id="129880800", parentId="129880784").text = "Чоловічі сорочки"

    # Оффер
    item = ET.SubElement(
        channel,
        "offer",
        attrib={
            "id": str(safe_id),
            "available": available,
            "in_stock": "true" if variant.get("inventory_quantity", 0) > 0 else "false",
            "type": "vendor.model",
            "selling_type": "r",
            "group_id": str(safe_id)
        }
    )

    # Название и описание
    title = product.get("title", "Без назви")
    description = product.get("body_html", "").strip()
    description_ua = get_translation(product["id"], locale="uk")
    if not description_ua:
        description_ua = description  # fallback
        

    ET.SubElement(item, "name").text = title
    ET.SubElement(item, "name_ua").text = title
    ET.SubElement(item, "description").text = f"<![CDATA[{description}]]>"
    ET.SubElement(item, "description_ua").text = f"<![CDATA[{description_ua}]]>"

    # Обязательные поля Prom.ua
    ET.SubElement(item, "vendor").text = product.get("vendor", "RUBASKA")
    ET.SubElement(item, "model").text = variant.get("title", "Без моделі")
    ET.SubElement(item, "categoryId").text = "129880800"
    ET.SubElement(item, "portal_category_id").text = "129880800"

    # Ссылка на товар
    link = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(item, "g:link").text = link
    ET.SubElement(item, "g:ads_redirect").text = link

    # Фото
    for i, image in enumerate(product.get("images", [])):
        if i == 0:
            ET.SubElement(item, "g:image_link").text = image["src"]
        else:
            ET.SubElement(item, "g:additional_image_link").text = image["src"]

    # Наличие и цена
    ET.SubElement(item, "g:availability").text = "in stock" if variant.get("inventory_quantity", 0) > 0 else "out of stock"
    ET.SubElement(item, "g:price").text = f'{variant.get("price", "0")} UAH'

    # Категория и бренд
    ET.SubElement(item, "g:product_type").text = product.get("product_type", "")
    ET.SubElement(item, "g:brand").text = product.get("vendor", "RUBASKA")
    ET.SubElement(item, "g:identifier_exists").text = "no"
    ET.SubElement(item, "g:condition").text = "new"

    # Размер и цвет из названия варианта
    variant_title_parts = variant.get("title", "").split(" / ")
    size = variant_title_parts[0] if len(variant_title_parts) > 0 else "M"
    color = variant_title_parts[1] if len(variant_title_parts) > 1 else "Невідомо"

    ET.SubElement(item, "g:size").text = size
    ET.SubElement(item, "g:color").text = color

    # Артикул
    sku = variant.get("sku") or str(safe_id)
    ET.SubElement(item, "g:vendorCode").text = sku

    # Видео
    video_url = ""
    for metafield in product_metafields:
        if metafield.get("namespace") == "custom" and metafield.get("key") == "video_url":
            video_url = metafield.get("value", "")
            break
    if video_url:
        ET.SubElement(item, "g:video_link").text = video_url

    # Постоянные характеристики
    constant_details = [
        ("Країна виробник", "Туреччина"),
        ("Де_знаходиться_товар", "Одеса"),
    ]
    for name, value in constant_details:
        detail = ET.SubElement(item, "g:product_detail")
        ET.SubElement(detail, "g:attribute_name").text = name
        ET.SubElement(detail, "g:attribute_value").text = value

    return ET.ElementTree(rss)

# Сохранение
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
