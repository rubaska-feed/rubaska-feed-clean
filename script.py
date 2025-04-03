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

# Получение списка товаров
def get_products():
    url = f"{BASE_URL}/products.json?limit=5&published_status=published"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    products = response.json().get("products", [])

    # Выводим первый товар и его первый вариант (для тестов)
    if products:
        print("Получено товаров:", len(products))
        print("Первый товар:", products[0]["title"])
    return products

# Получение метафилдов товара
def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

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

    # Получаем метафилды товара
    product_metafields = get_metafields(product["id"])

    # Наличие
    availability = "true" if "available" in variant and variant["available"] else "false"
    offer = ET.SubElement(channel, "offer", id=str(product["id"]), available=availability)

    # SKU (или ID товара)
    sku = variant.get("sku")
    if not sku:
        sku = str(product["id"])
    ET.SubElement(offer, "g:id").text = sku

    # Название товара
    ET.SubElement(offer, "g:title").text = product.get("title", "Немає назви")

    # Описание
    ET.SubElement(offer, "g:description").text = product.get("body_html", "")

    # Ссылки
    ET.SubElement(offer, "g:link").text = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(offer, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

    # Все изображения
    if product.get("images"):
        for image in product["images"]:
            if "src" in image:
                ET.SubElement(offer, "g:image_link").text = image["src"]

    # Цена
    ET.SubElement(offer, "g:price").text = f"{variant['price']} UAH"

    # Размер (міжнародний)
    ET.SubElement(offer, "g:size").text = variant["title"]

    # Виробник (бренд)
    ET.SubElement(offer, "g:brand").text = product.get("vendor", "")

    # Стан
    ET.SubElement(offer, "g:condition").text = "new"

    # Тип продукта
    ET.SubElement(offer, "g:product_type").text = product.get("product_type", "")

    # Цвет из метафилда
    color = "Невідомо"
    for metafield in product_metafields:
        if metafield.get("namespace") == "shopify" and metafield.get("key") == "color-pattern":
            color = metafield.get("value", "Невідомо").capitalize()
            break
    ET.SubElement(offer, "g:color").text = color

    return ET.ElementTree(rss)

# Сохраняем фид
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
