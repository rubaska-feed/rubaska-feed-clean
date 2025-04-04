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
    products = response.json()["products"]
    print("Получено товаров:", len(products))
    return products

def get_metafields(product_id):
    url = f"{BASE_URL}/products/{product_id}/metafields.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("metafields", [])

def generate_xml(products):
    rss = ET.Element("rss", attrib={"xmlns:g": "http://base.google.com/ns/1.0", "version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Інтернет-магазин Rubaska"
    ET.SubElement(channel, "link").text = "https://rubaska.prom.ua/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    if not products:
        return ET.ElementTree(rss)

    product = products[0]
    variant = product['variants'][0]
    product_metafields = get_metafields(product["id"])

    availability = "true" if variant.get("inventory_quantity", 0) > 0 else "false"
    offer = ET.SubElement(channel, "offer", id=str(product["id"]), available=availability, in_stock="true", type="vendor.model", selling_type="r", group_id="129880800")

    sku = variant.get("sku") or str(product["id"])
    ET.SubElement(offer, "vendorCode").text = sku

    title = product.get("title") or "Немає назви"
    ET.SubElement(offer, "name").text = title
    ET.SubElement(offer, "name_ua").text = title

    product_type = product.get("product_type", "")
    if product_type == "Чоловічі сорочки":
        model_value = "Сорочка чоловіча"
    else:
        model_value = variant.get("sku") or product.get("handle") or title
    ET.SubElement(offer, "model").text = model_value

    ET.SubElement(offer, "typePrefix").text = product_type
    ET.SubElement(offer, "categoryId").text = "129880800"

    ET.SubElement(offer, "price").text = f"{variant['price']}"
    ET.SubElement(offer, "currencyId").text = "UAH"

    for image in product.get("images", []):
        if "src" in image:
            ET.SubElement(offer, "picture").text = image["src"]

    ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
    ET.SubElement(offer, "country").text = "Туреччина"
    ET.SubElement(offer, "g:condition").text = "new"

    ET.SubElement(offer, "g:size").text = variant["title"]

    color = "Невідомо"
    for metafield in product_metafields:
        if metafield.get("namespace") == "shopify" and metafield.get("key") == "color-pattern":
            color = metafield.get("value", "Невідомо").capitalize()
            break
    ET.SubElement(offer, "g:color").text = color

    ET.SubElement(offer, "description").text = f"<![CDATA[{product.get('body_html', '')}]]>"
    ET.SubElement(offer, "description_ua").text = f"<![CDATA[{product.get('body_html', '')}]]>"

    return ET.ElementTree(rss)

if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
