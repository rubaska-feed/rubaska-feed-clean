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

# Step 1: Get products
def get_products():
    url = f"{BASE_URL}/products.json?limit=5"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    products = response.json()["products"]
    
    # Временно выводим данные о первом продукте и варианте
    print(products[0])  # Выводим весь продукт
    print(products[0]['variants'][0])  # Выводим первый вариант товара
    
    return products


# Step 2: Generate XML

def generate_xml(products):
    rss = ET.Element("rss", attrib={"xmlns:g": "http://base.google.com/ns/1.0", "version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Інтернет-магазин Rubaska"
    ET.SubElement(channel, "link").text = "https://rubaska.prom.ua/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    for product in products:
        variant = product['variants'][0]  # Берем первый вариант (например, размер M)

        # Определяем наличие товара с проверкой ключа
        availability = "true" if "available" in variant and variant["available"] else "false"

        # Обновляем тег 'offer' с атрибутом 'available'
        offer = ET.SubElement(channel, "offer", id=str(product["id"]), available=availability)

        # Title (Назва позиції)
        if product["title"]:
            ET.SubElement(offer, "g:title").text = product["title"]
        else:
            ET.SubElement(offer, "g:title").text = "Немає назви"  # Вставляем заглушку, если название пустое

        # Description
        ET.SubElement(offer, "g:description").text = product["body_html"]

        # Product link
        ET.SubElement(offer, "g:link").text = f"https://rubaska.com/products/{product['handle']}"
        ET.SubElement(offer, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

        # Images (Все изображения)
        if "images" in product:
            for image in product["images"]:
                image_url = image["src"]
                ET.SubElement(offer, "g:image_link").text = image_url

        # Price
        ET.SubElement(offer, "g:price").text = f"{variant['price']} UAH"

        # Product details
        ET.SubElement(offer, "g:product_type").text = product["product_type"]
        ET.SubElement(offer, "g:brand").text = product["vendor"]
        ET.SubElement(offer, "g:identifier_exists").text = "no"
        ET.SubElement(offer, "g:condition").text = "new"

        # SKU из метафилдов (если есть)
        sku = product['metafields'].get('sku', variant["sku"])  # Берем из метафилдов или вариант SKU
        ET.SubElement(offer, "g:sku").text = sku

        # Additional fields from metafields (Например, материал, страна)
        if 'material' in product['metafields']:
            ET.SubElement(offer, "g:product_detail").text = f"Матеріал: {product['metafields']['material']}"
        
        if 'country_of_origin' in product['metafields']:
            ET.SubElement(offer, "g:product_detail").text = f"Країна виробник: {product['metafields']['country_of_origin']}"
        
        if 'fabric_type' in product['metafields']:
            ET.SubElement(offer, "g:product_detail").text = f"Тип тканини: {product['metafields']['fabric_type']}"

        # Пример дополнительных атрибутов
        ET.SubElement(offer, "g:product_detail").text = f"Розміри чоловічих сорочок: 46"
        ET.SubElement(offer, "g:product_detail").text = f"Міжнародний розмір: M"
        ET.SubElement(offer, "g:product_detail").text = f"Тип сорочкового коміра: Комір-стійка"

    return ET.ElementTree(rss)


if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
