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
            return body
    return ""


# Генерация XML-фида
def generate_xml(products):
    import json
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", {"version": "2.0"})
    shop = ET.SubElement(rss, "shop")

    ET.SubElement(shop, "name").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(shop, "company").text = "Rubaska"
    ET.SubElement(shop, "url").text = "https://rubaska.com/"

    # Категории
    categories = ET.SubElement(shop, "categories")
    ET.SubElement(categories, "category", id="129880800", parentId="129880784").text = "Чоловічі сорочки"

    offers = ET.SubElement(shop, "offers")

    for product in products:
        variant = product["variants"][0]
        safe_id = str(int(product["id"]) % 2147483647)
        product_metafields = get_metafields(product["id"])
        variant_metafields = get_variant_metafields(variant["id"])

        description = product.get("body_html", "").strip()
        description_ua = get_translation(product["id"], "uk") or description or "Опис відсутній"

        # Variant info
        variant_title_parts = variant.get("title", "").split(" / ")
        size = variant_title_parts[0] if len(variant_title_parts) > 0 else "M"
        color = variant_title_parts[1] if len(variant_title_parts) > 1 else "Невідомо"
        collar_type = variant_title_parts[2] if len(variant_title_parts) > 2 else "Класичний"
        
        # Автозаполнение параметров по розміру
        size_measurements = {
            "S":   {"Обхват шиї": "38", "Обхват грудей": "98",  "Обхват талії": "90"},
            "M":   {"Обхват шиї": "39", "Обхват грудей": "104", "Обхват талії": "96"},
            "L":   {"Обхват шиї": "41", "Обхват грудей": "108", "Обхват талії": "100"},
            "XL":  {"Обхват шиї": "43", "Обхват грудей": "112", "Обхват талії": "108"},
            "XXL": {"Обхват шиї": "45", "Обхват грудей": "120", "Обхват талії": "112"},
            "3XL": {"Обхват шиї": "46", "Обхват грудей": "126", "Обхват талії": "124"},
        }

        if size in size_measurements:
            for label, value in size_measurements[size].items():
                ET.SubElement(offer, "param", name=label).text = value


        
        sku = variant.get("sku") or safe_id
        available = "true" if variant.get("inventory_quantity", 0) > 0 else "false"

        offer = ET.SubElement(
            offers,
            "offer",
            attrib={
                "id": safe_id,
                "available": available,
                "in_stock": "true" if available == "true" else "false",
                "type": "vendor.model",
                "selling_type": "r",
                "group_id": safe_id
            }
        )

        ET.SubElement(offer, "name").text = product.get("title", "Без назви")
        ET.SubElement(offer, "name_ua").text = product.get("title", "Без назви")
        ET.SubElement(offer, "description").text = f"<![CDATA[{description}]]>"
        ET.SubElement(offer, "description_ua").text = f"<![CDATA[{description_ua}]]>"

        link = f"https://rubaska.com/products/{product['handle']}"
        ET.SubElement(offer, "url").text = link

        # Фото
        for i, image in enumerate(product.get("images", [])):
            ET.SubElement(offer, "picture").text = image["src"]

        # Видео
        for metafield in product_metafields:
            if metafield.get("namespace") == "custom" and metafield.get("key") == "video_url":
                ET.SubElement(offer, "video").text = metafield.get("value", "")
                break

        # Цены и обязательные поля
        ET.SubElement(offer, "price").text = variant.get("price", "0")
        ET.SubElement(offer, "currencyId").text = "UAH"
        ET.SubElement(offer, "categoryId").text = "129880800"
        ET.SubElement(offer, "portal_category_id").text = "129880800"
        ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
        ET.SubElement(offer, "model").text = variant.get("title", "Без моделі")
        ET.SubElement(offer, "vendorCode").text = sku
        ET.SubElement(offer, "country").text = "Туреччина"

        # Характеристики
        ET.SubElement(offer, "param", name="Колір").text = color
        ET.SubElement(offer, "param", name="Розмір").text = size
        ET.SubElement(offer, "param", name="Тип сорочкового коміра").text = collar_type

        # Характеристики из метафилдов
        field_mapping = {
            "Тип виробу": "product_type",
            "Застежка": "fastening",
            "Тип тканини": "fabric_type",
            "Тип крою": "cut_type",
            "Фасон рукава": "sleeve_style",
            "Візерунки і принти": "pattern_and_prints",
        }

        for label, key in field_mapping.items():
            value = ""
            for metafield in product_metafields:
                if metafield.get("namespace") == "custom" and metafield.get("key") == key:
                    value = metafield.get("value", "")
                    break
            if value:
                ET.SubElement(offer, "param", name=label).text = value


        # Постоянные характеристики
        constant_params = [
            ("Міжнародний розмір", size),
            ("Обхват шиї", ""),
            ("Обхват грудей", ""),
            ("Обхват талії", ""),
            ("Розміри чоловічих сорочок", ""),
            ("Стан", "Новий"),
            ("Довжина рукава", ""),
        ]
        for name, value in constant_params:
            ET.SubElement(offer, "param", name=name).text = value

    return ET.ElementTree(rss)

# Сохранение
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
