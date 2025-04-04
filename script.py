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

def get_variant_metafields(variant_id):
    url = f"{BASE_URL}/variants/{variant_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])


# Генерация XML-фида

def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(channel, "link").text = "https://rubaska.com/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    if not products:
        return ET.ElementTree(rss)

    product = products[0]
    variant = product["variants"][0]
    product_metafields = get_metafields(product["id"])

    available = "true" if variant.get("inventory_quantity", 0) > 0 else "false"
    item = ET.SubElement(channel, "item", attrib={"available": available})

    ET.SubElement(item, "g:id").text = str(product["id"])
    ET.SubElement(item, "g:title").text = product.get("title", "Без назви")
    ET.SubElement(item, "g:description").text = product.get("body_html", "")
    ET.SubElement(item, "g:link").text = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(item, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

    for i, image in enumerate(product.get("images", [])):
        if i == 0:
            ET.SubElement(item, "g:image_link").text = image["src"]
        else:
            ET.SubElement(item, "g:additional_image_link").text = image["src"]

    ET.SubElement(item, "g:availability").text = "in stock" if variant.get("inventory_quantity", 0) > 0 else "out of stock"
    ET.SubElement(item, "g:price").text = f'{variant.get("price", "0")} UAH'
    ET.SubElement(item, "g:product_type").text = product.get("product_type", "")
    ET.SubElement(item, "g:brand").text = product.get("vendor", "RUBASKA")
    ET.SubElement(item, "g:identifier_exists").text = "no"
    ET.SubElement(item, "g:condition").text = "new"

    # Размер (только название варианта)
    size = variant.get("title", "M").split(" / ")[0]
    ET.SubElement(item, "{http://base.google.com/ns/1.0}size").text = size

    # Артикул
    sku = variant.get("sku") or str(product["id"])
    ET.SubElement(item, "g:vendorCode").text = sku

    # Цвет (украинское название цвета из metaobject color.title_ua)
    # Получаем цвет из метаобъекта, связанного с вариантом
    color = "Невідомо"
    for metafield in variant_metafields:
        if metafield.get("namespace") == "custom" and metafield.get("key") == "color":
            # Получаем GID ссылки на metaobject
            metaobject_id = metafield.get("value")
            meta_url = f"{BASE_URL}/metaobjects.json?ids={metaobject_id}"
            response = requests.get(meta_url, headers=HEADERS)
            if response.ok:
                metaobjects = response.json().get("metaobjects", [])
                if metaobjects:
                    fields = metaobjects[0].get("fields", {})
                    color = fields.get("title_ua", "Невідомо")
            break
        
    ET.SubElement(item, "{http://base.google.com/ns/1.0}color").text = color



    # Видео (если есть)
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

# Сохранение файла
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
