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

# Генерация XML
def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")  # ✅ добавили namespace g
    yml = ET.Element("yml_catalog", date="2025-04-04")
    shop = ET.SubElement(yml, "shop")

    # Базовая информация
    ET.SubElement(shop, "name").text = "Rubaska"
    ET.SubElement(shop, "company").text = "Rubaska"
    ET.SubElement(shop, "url").text = "https://rubaska.com/"

    currencies = ET.SubElement(shop, "currencies")
    ET.SubElement(currencies, "currency", id="UAH", rate="1")

    categories = ET.SubElement(shop, "categories")
    ET.SubElement(categories, "category", id="129880800", parentId="129880784").text = "Чоловічі сорочки"

    offers = ET.SubElement(shop, "offers")

    if not products:
        return ET.ElementTree(yml)

    product = products[0]
    variant = product["variants"][0]
    product_metafields = get_metafields(product["id"])

    availability = "true" if variant.get("inventory_quantity", 0) > 0 else "false"

    offer = ET.SubElement(
        offers, "offer", {
            "id": str(product["id"]),
            "available": availability,
            "in_stock": "true",
            "type": "vendor.model",
            "selling_type": "r",
            "group_id": "348"
        }
    )

    # Название и модель
    ET.SubElement(offer, "name").text = product.get("title", "Без назви")
    ET.SubElement(offer, "name_ua").text = product.get("title", "Без назви")
    ET.SubElement(offer, "model").text = "Сорочка чоловіча"
    ET.SubElement(offer, "typePrefix").text = "Сорочка"

    # Категория и ссылки
    ET.SubElement(offer, "categoryId").text = "129880800"
    ET.SubElement(offer, "portal_category_id").text = "129880800"
    ET.SubElement(offer, "url").text = f"https://rubaska.com/products/{product['handle']}"

    # Описание
    description = product.get("body_html", "").replace("&", "&amp;")
    ET.SubElement(offer, "description").text = description
    ET.SubElement(offer, "description_ua").text = description

    # Цена
    ET.SubElement(offer, "price").text = variant["price"]
    ET.SubElement(offer, "currencyId").text = "UAH"

    # Фото
    for image in product.get("images", []):
        if "src" in image:
            ET.SubElement(offer, "{http://base.google.com/ns/1.0}image_link").text = image["src"]

    # Артикул
    sku = variant.get("sku") or str(product["id"])
    ET.SubElement(offer, "vendorCode").text = sku

    # Производитель и состояние
    ET.SubElement(offer, "vendor").text = product.get("vendor", "Rubaska")
    ET.SubElement(offer, "{http://base.google.com/ns/1.0}brand").text = product.get("vendor", "Rubaska")
    ET.SubElement(offer, "{http://base.google.com/ns/1.0}condition").text = "new"

    # Размер
    ET.SubElement(offer, "{http://base.google.com/ns/1.0}size").text = variant.get("title", "M")

    # Цвет из метафилда
    color = "Невідомо"
    for metafield in product_metafields:
        if metafield.get("namespace") == "shopify" and metafield.get("key") == "color-pattern":
            color = metafield.get("value", "Невідомо").capitalize()
            break
    ET.SubElement(offer, "{http://base.google.com/ns/1.0}color").text = color

    # Характеристики группы
    ET.SubElement(offer, "param", name="Назва_групи").text = "Чоловічі сорочки"
    ET.SubElement(offer, "param", name="Ідентифікатор_підрозділу").text = "348"
    ET.SubElement(offer, "param", name="Посилання_підрозділу").text = "https://prom.ua/Muzhskie-rubashki"

    return ET.ElementTree(yml)

# Сохранение файла
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
