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
    all_products = []
    page_info = None
    limit = 250  # Максимум разрешённый Shopify

    while True:
        url = f"{BASE_URL}/products.json?limit={limit}&status=active"
        if page_info:
            url += f"&page_info={page_info}"

        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json().get("products", [])
        all_products.extend(data)

        # Проверяем есть ли следующая страница
        link_header = response.headers.get("Link", "")
        if 'rel=\"next\"' in link_header:
            import re
            match = re.search(r'<[^>]+page_info=([^&>]+)[^>]*>; rel=\"next\"', link_header)
            if match:
                page_info = match.group(1)
            else:
                break
        else:
            break

    return all_products

# Получение метафилдов товара
import time
def get_metafields(product_id):
    time.sleep(0.5)  # добавляем 500 мс задержки
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

# Получение метафилдов варианта
import time

def get_variant_metafields(variant_id):
    time.sleep(0.5)  # пауза 500 мс между запросами
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
    import xml.etree.ElementTree as ET
    
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", {"version": "2.0"})
    shop = ET.SubElement(rss, "shop")

    ET.SubElement(shop, "name").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(shop, "company").text = "Rubaska"
    ET.SubElement(shop, "url").text = "https://rubaska.com/"

    # Категории
    category_info = {
        "Сорочка": {
            "category_id": "129880800",
            "parent_id": "129880784",
            "group_name": "Чоловічі сорочки",
            "portal_url": "https://prom.ua/Muzhskie-rubashki",
            "subdivision_id": "348"
        },
        "Теніска": {
            "category_id": "129880800",
            "parent_id": "129880784",
            "group_name": "Чоловічі сорочки",
            "portal_url": "https://prom.ua/Muzhskie-rubashki",
            "subdivision_id": "348"
        },
        "Футболка": {
            "category_id": "129880791",
            "parent_id": "129880784",
            "group_name": "Чоловічі футболки та майки",
            "portal_url": "https://prom.ua/Futbolki-muzhskie",
            "subdivision_id": "35506"
        },
        "Жилет": {
            "category_id": "129883725",
            "parent_id": "129880784",
            "group_name": "Святкові жилети",
            "portal_url": "https://prom.ua/ua/Muzhskie-zhiletki-i-bezrukavki-1",
            "subdivision_id": "35513"
        },
    }



    
    categories = ET.SubElement(shop, "categories")
    for cat in category_info.values():
        ET.SubElement(categories, "category", id=cat["category_id"], parentId=cat["parent_id"]).text = cat["group_name"]

    offers = ET.SubElement(shop, "offers")

    for product in products:
        variant = product["variants"][0]
        safe_id = str(int(product["id"]) % 2147483647)
        product_metafields = get_metafields(product["id"])
        variant_metafields = []  # не запрашиваем, оставляем пустым список

        description = product.get("body_html", "").strip()
        description_ua = get_translation(product["id"], "uk") or description or "Опис відсутній"

        
        # Variant info
        variant_title_parts = variant.get("title", "").split(" / ")
        size = variant_title_parts[0] if len(variant_title_parts) > 0 else "M"
        color = variant_title_parts[1] if len(variant_title_parts) > 1 else "Невідомо"
        collar_type = variant_title_parts[2] if len(variant_title_parts) > 2 else "Класичний"
      
        sku = variant.get("sku") or safe_id
        available = "true" if variant.get("inventory_quantity", 0) > 0 else "false"

        # Определение категории
        product_type = ""
        for metafield in product_metafields:
            if metafield.get("namespace") == "custom" and metafield.get("key") == "product_type":
                product_type = metafield.get("value", "")
                break

        category_id = "129880800"
        portal_category_id = "129880800"
        category_details = None

        if product_type in category_info:
            category = category_info[product_type]
            category_id = category["category_id"]
            portal_category_id = category["category_id"]
            category_details = category


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
        
        # Автозаполнение параметров по розміру
        size_measurements = {
            "S":   {"Обхват шиї": "38", "Обхват грудей": "98",  "Обхват талії": "90", "Довжина рукава": "63", "Розміри чоловічих сорочок": "44"},
            "M":   {"Обхват шиї": "39", "Обхват грудей": "104", "Обхват талії": "96", "Довжина рукава": "64", "Розміри чоловічих сорочок": "46" },
            "L":   {"Обхват шиї": "41", "Обхват грудей": "108", "Обхват талії": "100", "Довжина рукава": "65", "Розміри чоловічих сорочок": "48"},
            "XL":  {"Обхват шиї": "43", "Обхват грудей": "112", "Обхват талії": "108", "Довжина рукава": "66", "Розміри чоловічих сорочок": "50"},
            "XXL": {"Обхват шиї": "45", "Обхват грудей": "120", "Обхват талії": "112", "Довжина рукава": "67", "Розміри чоловічих сорочок": "52"},
            "3XL": {"Обхват шиї": "46", "Обхват грудей": "126", "Обхват талії": "124", "Довжина рукава": "68", "Розміри чоловічих сорочок": "54" },
        }



        if size in size_measurements:
            for label, value in size_measurements[size].items():
                ET.SubElement(offer, "param", name=label).text = value

        

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
        ET.SubElement(offer, "categoryId").text = category_id
        ET.SubElement(offer, "portal_category_id").text = portal_category_id
        ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
        ET.SubElement(offer, "model").text = variant.get("title", "Сорочка Без моделі")
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
            "Манжет сорочки": "shirt_cuff",
            "Стиль": "style",
            "Склад": "fabric_composition",
            "Кишені": "pockets",
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
            ("Стан", "Новий"),
            ("Де знаходиться товар", "Одеса"),
            ("Країна виробник", "Туреччина"),
        ]
        for name, value in constant_params:
            ET.SubElement(offer, "param", name=name).text = value

        # Добавление product_detail по категории
        if category_details:
            for attr_name, attr_value in {
                "Ідентифікатор_підрозділу": category_details["subdivision_id"],
                "Посилання_підрозділу": category_details["portal_url"],
                "Назва_групи": category_details["group_name"]
            }.items():
                detail = ET.SubElement(offer, "{http://base.google.com/ns/1.0}product_detail")
                ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_name").text = attr_name
                ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_value").text = attr_value


    return ET.ElementTree(rss)

# Сохранение
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
