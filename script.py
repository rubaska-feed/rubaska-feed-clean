import time
import json
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import os

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

# BULK API: Запуск экспорта
def start_bulk_export():
    url = f"{BASE_URL}/graphql.json"
    query = {
        "query": """
        mutation {
          bulkOperationRunQuery(
            query: """
            {
              products {
                edges {
                  node {
                    id
                    title
                    handle
                    vendor
                    bodyHtml
                    productType
                    images(first: 10) { edges { node { src } } }
                    variants(first: 10) {
                      edges {
                        node {
                          id
                          title
                          sku
                          price
                          inventoryQuantity
                        }
                      }
                    }
                    metafields(first: 20) {
                      edges {
                        node {
                          namespace
                          key
                          value
                        }
                      }
                    }
                  }
                }
              }
            }
            """
          ) {
            bulkOperation {
              id
              status
            }
            userErrors {
              field
              message
            }
          }
        }
        """
    }

    response = requests.post(url, headers=HEADERS, json=query)
    response.raise_for_status()
    print("📦 Bulk export started.")

# BULK API: Проверка статуса

def get_bulk_operation_status():
    url = f"{BASE_URL}/graphql.json"
    query = {
        "query": """
        {
          currentBulkOperation {
            id
            status
            url
            errorCode
          }
        }
        """
    }

    response = requests.post(url, headers=HEADERS, json=query)
    response.raise_for_status()
    return response.json()["data"]["currentBulkOperation"]

# BULK API: Скачивание готового файла

def download_bulk_file(url):
    response = requests.get(url)
    response.raise_for_status()
    lines = response.text.strip().split("\n")
    products = [json.loads(line)["node"] for line in lines]
    return products

# Генерация XML-фида из Bulk API

def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", {"version": "2.0"})
    shop = ET.SubElement(rss, "shop")

    ET.SubElement(shop, "name").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(shop, "company").text = "Rubaska"
    ET.SubElement(shop, "url").text = "https://rubaska.com/"

    # Категории Prom.ua
    category_info = {
        "Сорочка": {"category_id": "129880800", "parent_id": "129880784", "group_name": "Чоловічі сорочки", "portal_url": "https://prom.ua/Muzhskie-rubashki", "subdivision_id": "348"},
        "Футболка": {"category_id": "129880791", "parent_id": "129880784", "group_name": "Чоловічі футболки та майки", "portal_url": "https://prom.ua/Futbolki-muzhskie", "subdivision_id": "35506"},
        "Жилет": {"category_id": "129883725", "parent_id": "129880784", "group_name": "Святкові жилети", "portal_url": "https://prom.ua/ua/Muzhskie-zhiletki-i-bezrukavki-1", "subdivision_id": "35513"},
    }

    categories = ET.SubElement(shop, "categories")
    for cat in category_info.values():
        ET.SubElement(categories, "category", id=cat["category_id"], parentId=cat["parent_id"]).text = cat["group_name"]

    offers = ET.SubElement(shop, "offers")

    for product in products:
        product_type = product.get("productType", "Сорочка")
        category = category_info.get(product_type, category_info["Сорочка"])

        for variant in product.get("variants", {}).get("edges", []):
            v = variant["node"]
            safe_id = str(int(v["id"].split("/")[-1]) % 2147483647)
            title_parts = v.get("title", "").split(" / ")
            size = title_parts[0] if len(title_parts) > 0 else "M"
            color = title_parts[1] if len(title_parts) > 1 else "Невідомо"
            collar = title_parts[2] if len(title_parts) > 2 else "Класичний"

            available = "true" if v.get("inventoryQuantity", 0) > 0 else "false"

            offer = ET.SubElement(offers, "offer", attrib={
                "id": safe_id,
                "available": available,
                "in_stock": "true" if available == "true" else "false",
                "type": "vendor.model",
                "selling_type": "r",
                "group_id": safe_id
            })

            # Размерные характеристики
            measurements = {
                "S":   {"Обхват шиї": "38", "Обхват грудей": "98",  "Обхват талії": "90", "Довжина рукава": "63", "Розміри чоловічих сорочок": "44"},
                "M":   {"Обхват шиї": "39", "Обхват грудей": "104", "Обхват талії": "96", "Довжина рукава": "64", "Розміри чоловічих сорочок": "46"},
                "L":   {"Обхват шиї": "41", "Обхват грудей": "108", "Обхват талії": "100", "Довжина рукава": "65", "Розміри чоловічих сорочок": "48"},
                "XL":  {"Обхват шиї": "43", "Обхват грудей": "112", "Обхват талії": "108", "Довжина рукава": "66", "Розміри чоловічих сорочок": "50"},
                "XXL": {"Обхват шиї": "45", "Обхват грудей": "120", "Обхват талії": "112", "Довжина рукава": "67", "Розміри чоловічих сорочок": "52"},
                "3XL": {"Обхват шиї": "46", "Обхват грудей": "126", "Обхват талії": "124", "Довжина рукава": "68", "Розміри чоловічих сорочок": "54"},
            }
            for label, value in measurements.get(size, {}).items():
                ET.SubElement(offer, "param", name=label).text = value

            ET.SubElement(offer, "name").text = product["title"]
            ET.SubElement(offer, "name_ua").text = product["title"]
            ET.SubElement(offer, "description").text = f"<![CDATA[{product.get('bodyHtml', '')}]]>"
            ET.SubElement(offer, "description_ua").text = f"<![CDATA[{product.get('bodyHtml', '')}]]>"
            ET.SubElement(offer, "url").text = f"https://rubaska.com/products/{product['handle']}"

            for i, img in enumerate(product.get("images", {}).get("edges", [])):
                ET.SubElement(offer, "picture").text = img["node"]["src"]

            ET.SubElement(offer, "price").text = v.get("price", "0")
            ET.SubElement(offer, "currencyId").text = "UAH"
            ET.SubElement(offer, "categoryId").text = category["category_id"]
            ET.SubElement(offer, "portal_category_id").text = category["category_id"]
            ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
            ET.SubElement(offer, "model").text = v.get("title", "Модель")
            ET.SubElement(offer, "vendorCode").text = v.get("sku") or safe_id
            ET.SubElement(offer, "country").text = "Туреччина"
            ET.SubElement(offer, "param", name="Колір").text = color
            ET.SubElement(offer, "param", name="Розмір").text = size
            ET.SubElement(offer, "param", name="Тип сорочкового коміра").text = collar

            field_mapping = {
                "Тип виробу": "product_type",
                "Застежка": "fastening",
                "Тип тканини": "fabric_type",
                "Тип крою": "cut_type",
                "Фасон рукава": "sleeve_style",
                "Манжет сорочки": "shirt_cuff",
                "Стиль": "style",
                "Склад": "fabric_composition",
                "Кишені": "pockets",
            }
            metafields = {m["node"]["key"]: m["node"]["value"] for m in product.get("metafields", {}).get("edges", []) if m["node"]["namespace"] == "custom"}
            for label, key in field_mapping.items():
                if key in metafields:
                    ET.SubElement(offer, "param", name=label).text = metafields[key]

            ET.SubElement(offer, "param", name="Міжнародний розмір").text = size
            ET.SubElement(offer, "param", name="Стан").text = "Новий"
            ET.SubElement(offer, "param", name="Де знаходиться товар").text = "Одеса"
            ET.SubElement(offer, "param", name="Країна виробник").text = "Туреччина"

            for attr_name, attr_value in {
                "Ідентифікатор_підрозділу": category["subdivision_id"],
                "Посилання_підрозділу": category["portal_url"],
                "Назва_групи": category["group_name"]
            }.items():
                detail = ET.SubElement(offer, "{http://base.google.com/ns/1.0}product_detail")
                ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_name").text = attr_name
                ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_value").text = attr_value

    return ET.ElementTree(rss)

# Запуск полного цикла Bulk API + генерация
if __name__ == "__main__":
    start_bulk_export()
    print("⏳ Очікуємо 60 секунд...")
    time.sleep(60)

    status = get_bulk_operation_status()
    if status["status"] == "COMPLETED":
        print("📥 Завантажуємо дані...")
        products = download_bulk_file(status["url"])
        print(f"🔢 Отримано товарів: {len(products)}")

        xml_tree = generate_xml(products)
        xml_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
        print("✔️ Фід створено: feed.xml")
    else:
        print("❗ Операція не завершена. Перевірте статус пізніше.")

