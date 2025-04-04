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
    url = f"{BASE_URL}/products.json?limit=5&status=active"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    products = response.json().get("products", [])

    if products:
        print("Товар:", products[0].get("title"))
        print("Вариант:", products[0].get("variants", [{}])[0])

    return products

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

    product = products[0]
    variant = product['variants'][0]
    product_metafields = get_metafields(product["id"])

    availability = "true" if variant.get("inventory_quantity", 0) > 0 else "false"
    offer = ET.SubElement(channel, "offer", id=str(product["id"]), available=availability, in_stock="true", type="vendor.model", selling_type="r")

    sku = variant.get("sku") or str(product["id"])
    ET.SubElement(offer, "g:id").text = sku
    ET.SubElement(offer, "vendorCode").text = sku

    title = product.get("title") or "Немає назви"
    ET.SubElement(offer, "g:title").text = title
    ET.SubElement(offer, "name").text = title

    ET.SubElement(offer, "g:description").text = product.get("body_html", "")
    ET.SubElement(offer, "description").text = product.get("body_html", "")

    ET.SubElement(offer, "g:link").text = f"https://rubaska.com/products/{product['handle']}"
    ET.SubElement(offer, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}"

    if product.get("images"):
        for image in product["images"][:10]:
            if "src" in image:
                ET.SubElement(offer, "g:image_link").text = image["src"]
                ET.SubElement(offer, "picture").text = image["src"]

    ET.SubElement(offer, "g:price").text = f"{variant['price']} UAH"
    ET.SubElement(offer, "g:size").text = variant.get("title", "")
    ET.SubElement(offer, "g:brand").text = product.get("vendor", "")
    ET.SubElement(offer, "g:condition").text = "new"
    ET.SubElement(offer, "g:product_type").text = product.get("product_type", "")

    color = "Невідомо"
    for metafield in product_metafields:
        if metafield.get("namespace") == "shopify" and metafield.get("key") == "color-pattern":
            color = metafield.get("value", "Невідомо").capitalize()
            break
    ET.SubElement(offer, "g:color").text = color

    # Привязка к категории Prom.ua
    if product.get("product_type") == "одяг та взуття > чоловічий одяг > чоловічі сорочки":
        ET.SubElement(offer, "categoryId").text = "129880800"
        ET.SubElement(offer, "portal_category_id").text = "129880800"
        ET.SubElement(offer, "portal_category_url").text = "https://prom.ua/Muzhskie-rubashki"
        ET.SubElement(offer, "param", name="Ідентифікатор_підрозділу").text = "348"
        ET.SubElement(offer, "model").text = "Сорочка чоловіча"

    return ET.ElementTree(rss)

# Запись XML в файл
if __name__ == "__main__":
    products = get_products()
    xml_tree = generate_xml(products)
    xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("✔️ XML-фид успешно создан: feed.xml")
