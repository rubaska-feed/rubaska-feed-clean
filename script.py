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

# Получение товаров с Shopify
def get_products():
    url = f"{BASE_URL}/products.json?limit=5"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    products = response.json()["products"]

    # Выводим первый товар и его первый вариант (для тестов)
    print(products[0])
    print(products[0]['variants'][0])
    
    return products

# Генерация XML-фида
def generate_xml(products):
    rss = ET.Element("rss", attrib={"xmlns:g": "http://base.google.com/ns/1.0", "version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Інтернет-магазин Rubaska"
    ET.SubElement(channel, "link").text = "https://rubaska.prom.ua/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    if not products:
        return ET.ElementTree(rss)

    # Только 1 товар для теста
    product = products[0]
    variant = product['variants'][0]

    availability = "true" if "available" in variant and variant["available"] else "false"
    offer = ET.SubElement(channel, "offer", id=str(product["id"]), available=availability)

    # Назва позиції
    title = product["title"] if product.get("title") else "Немає назви"
    ET.SubElement(offer, "g:title").text = title

    # Описание
    ET.SubElement(offer, "g:description").text = product.get("body_html", "")

    # Ссылки
    ET.SubElement(offer, "g:link").text = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(offer, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

    # Первое изображение
    if product.get("images"):
        ET.SubElement(offer, "g:image_link").text = product["images"][0]["src"]

    # Цена
    ET.SubElement(offer, "g:price").text = f"{variant['price']} UAH"

    # Остальные поля
    ET.SubElement(offer, "g:product_type").text = product.get("product_type", "")
    ET.SubElement(offer, "g:brand").text = product.get("vendor", "")
    ET.SubElement(offer, "g:identifier_exists").text = "no"
    ET.SubElement(offer, "g:condition").text = "new"

    return ET.ElementTree(rss)

# Запись XML в файл
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
