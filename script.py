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

# Получение медиафайлов товара (видео)
def get_media(product_id):
    url = f"{BASE_URL}/products/{product_id}/media.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("media", [])

# Генерация XML
def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", attrib={"xmlns:g": "http://base.google.com/ns/1.0", "version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Интернет-магазин \"Rubaska\""
    ET.SubElement(channel, "link").text = "https://rubaska.com/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    if not products:
        return ET.ElementTree(rss)

    product = products[0]  # Один товар для теста
    variant = product["variants"][0]
    product_metafields = get_metafields(product["id"])
    media_files = get_media(product["id"])

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "g:id").text = str(product["id"])
    ET.SubElement(item, "g:title").text = product.get("title", "Без назви")
    ET.SubElement(item, "g:description").text = product.get("body_html", "")
    ET.SubElement(item, "g:link").text = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(item, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

    # Картинки
    for i, image in enumerate(product.get("images", [])):
        tag = "g:image_link" if i == 0 else "g:additional_image_link"
        ET.SubElement(item, tag).text = image["src"]

    # Видео
    for media in media_files:
        if media.get("media_type") == "external_video":
            ET.SubElement(item, "g:video_link").text = media.get("src")
            break

    ET.SubElement(item, "g:availability").text = "in stock" if variant.get("inventory_quantity", 0) > 0 else "out of stock"
    ET.SubElement(item, "g:price").text = f"{variant['price']} UAH"
    ET.SubElement(item, "g:product_type").text = product.get("product_type", "")
    ET.SubElement(item, "g:brand").text = product.get("vendor", "Rubaska")
    ET.SubElement(item, "g:identifier_exists").text = "no"
    ET.SubElement(item, "g:condition").text = "new"

    # Цвет (ищем по метафилду color-pattern, значение из metaobject)
    color = "Невідомо"
    for metafield in product_metafields:
        if metafield.get("namespace") == "shopify" and metafield.get("key") == "color-pattern":
            color = metafield.get("value", "Невідомо").capitalize()
            break
    ET.SubElement(item, "g:color").text = color

    # Размер
    ET.SubElement(item, "g:size").text = variant.get("title", "")

    # Артикул
    ET.SubElement(item, "g:vendorCode").text = variant.get("sku", str(product["id"]))

    # Постоянные характеристики
    for name, value in [
        ("Країна виробник", "Туреччина"),
        ("Де_знаходиться_товар", "Одеса"),
    ]:
        detail = ET.SubElement(item, "g:product_detail")
        ET.SubElement(detail, "g:attribute_name").text = name
        ET.SubElement(detail, "g:attribute_value").text = value

    return ET.ElementTree(rss)

# Сохранение файла
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("\u2714\ufe0f XML-фид успешно создан: feed.xml")
