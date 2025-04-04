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
    url = f"{BASE_URL}/products.json?status=active&limit=1"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["products"]


def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])


def generate_xml(products):
    yml_catalog = ET.Element("yml_catalog", date="2025-04-04")
    shop = ET.SubElement(yml_catalog, "shop")

    ET.SubElement(shop, "name").text = "Rubaska"
    ET.SubElement(shop, "company").text = "Rubaska"
    ET.SubElement(shop, "url").text = "https://rubaska.com/"
    ET.SubElement(shop, "currencies")
    ET.SubElement(shop, "categories")  # можем добавить позже категории вручную

    offers = ET.SubElement(shop, "offers")

    if not products:
        return ET.ElementTree(yml_catalog)

    product = products[0]
    variant = product["variants"][0]
    metafields = get_metafields(product["id"])

    sku = variant.get("sku") or str(product["id"])
    availability = "true" if variant.get("inventory_quantity", 0) > 0 else "false"
    group_id = str(product["id"])

    offer = ET.SubElement(offers, "offer", {
        "id": sku,
        "available": availability,
        "in_stock": "true",
        "type": "vendor.model",
        "selling_type": "r",
        "group_id": group_id
    })

    # Основные поля
    ET.SubElement(offer, "name").text = product["title"]
    ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
    ET.SubElement(offer, "model").text = variant["title"]
    ET.SubElement(offer, "vendorCode").text = sku
    ET.SubElement(offer, "categoryId").text = "348"  # ID вашей категории на Prom
    ET.SubElement(offer, "price").text = variant["price"]
    ET.SubElement(offer, "currencyId").text = "UAH"
    ET.SubElement(offer, "url").text = f"https://rubaska.com/products/{product['handle']}"

    # Картинки
    for image in product.get("images", []):
        ET.SubElement(offer, "picture").text = image["src"]

    # Описание
    description = product.get("body_html", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    ET.SubElement(offer, "description").text = f"<![CDATA[{description}]]>"
    ET.SubElement(offer, "description_ua").text = f"<![CDATA[{description}]]>"

    # Характеристики
    ET.SubElement(offer, "param", name="Міжнародний розмір").text = variant["title"]
    ET.SubElement(offer, "param", name="Стан").text = "Новий"
    ET.SubElement(offer, "param", name="Країна виробник").text = "Туреччина"

    # Цвет из метафилда
    color = "Невідомо"
    for field in metafields:
        if field["namespace"] == "shopify" and field["key"] == "color-pattern":
            color = field.get("value", "").capitalize()
            break
    ET.SubElement(offer, "param", name="Колір").text = color

    return ET.ElementTree(yml_catalog)


if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успішно створено: feed.xml")
