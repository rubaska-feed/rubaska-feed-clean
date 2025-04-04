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

def get_products():
    url = f"{BASE_URL}/products.json?limit=10&status=active"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["products"]

def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", attrib={"version": "2.0", "xmlns:g": "http://base.google.com/ns/1.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = ' "Rubaska"'
    ET.SubElement(channel, "link").text = "https://rubaska.com/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    for product in products:
        product_metafields = get_metafields(product["id"])
        for variant in product.get("variants", []):
            item = ET.SubElement(channel, "item")
            sku = variant.get("sku") or str(product["id"])
            ET.SubElement(item, "g:id").text = sku
            ET.SubElement(item, "g:title").text = product.get("title", "Без назви")
            ET.SubElement(item, "g:description").text = product.get("body_html", "")
            link = f"https://rubaska.com/products/{product['handle']}"
            ET.SubElement(item, "g:link").text = link
            ET.SubElement(item, "g:ads_redirect").text = link

            for idx, image in enumerate(product.get("images", [])):
                tag = "g:image_link" if idx == 0 else "g:additional_image_link"
                ET.SubElement(item, tag).text = image["src"]

            availability = "in stock" if variant.get("inventory_quantity", 0) > 0 else "out of stock"
            ET.SubElement(item, "g:availability").text = availability
            ET.SubElement(item, "g:price").text = f"{variant['price']} UAH"
            ET.SubElement(item, "g:product_type").text = "одяг та взуття > чоловічий одяг > чоловічі сорочки"
            ET.SubElement(item, "g:brand").text = product.get("vendor", "RUBASKA")
            ET.SubElement(item, "g:identifier_exists").text = "no"
            ET.SubElement(item, "g:condition").text = "new"
            ET.SubElement(item, "g:size").text = variant.get("title", "L")

            color = "Невідомо"
            for metafield in product_metafields:
                if metafield.get("namespace") == "shopify" and metafield.get("key") == "color-pattern":
                    color = metafield.get("value", "Невідомо").capitalize()
                    break
            ET.SubElement(item, "g:color").text = color

            details = [
                ("Країна виробник", "Туреччина"),
                ("Вид виробу", "Сорочка"),
                ("Розміри чоловічих сорочок", "48"),
                ("Обхват шиї", "41 см"),
                ("Обхват грудей", "108 см"),
                ("Обхват талії", "100 см"),
                ("Тип крою", "Приталена"),
                ("Тип сорочкового коміра", "Класичний"),
                ("Фасон рукава", "Довгий"),
                ("Манжет сорочки", "З двома гудзиками"),
                ("Тип тканини", "Бавовна"),
                ("Стиль", "Casual"),
                ("Візерунки і принти", "Без візерунків і принтів"),
                ("Склад", "стретч -котон"),
                ("Ідентифікатор_підрозділу", "348"),
                ("Посилання_підрозділу", "https://prom.ua/Muzhskie-rubashki"),
                ("Назва_групи", "Чоловічі сорочки"),
                ("Міжнародний розмір", variant.get("title", "L"))
            ]
            for name, value in details:
                detail = ET.SubElement(item, "g:product_detail")
                ET.SubElement(detail, "g:attribute_name").text = name
                ET.SubElement(detail, "g:attribute_value").text = value

    return ET.ElementTree(rss)

if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("prom_feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: prom_feed.xml")
