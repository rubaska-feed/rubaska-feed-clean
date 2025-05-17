import os
import time
import json
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Загрузка переменных
load_dotenv()
TOKEN = os.getenv("SHOPIFY_API_TOKEN")
SHOP_NAME = "676c64"
API_VERSION = "2023-10"

BASE_URL = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}"
HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": TOKEN
}

def start_bulk_export():
    url = f"{BASE_URL}/graphql.json"
    query = {
        "query": '''
        mutation {
          bulkOperationRunQuery(
            query: """
            {
              products {
                id
                title
                handle
                vendor
                bodyHtml
                productType
                variants {
                  id
                  title
                  sku
                  price
                  inventoryQuantity
                }
                images {
                  src
                }
                metafields {
                  namespace
                  key
                  value
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
        '''
    }
    response = requests.post(url, headers=HEADERS, json=query)
    response.raise_for_status()
    print("✅ Bulk product export started.")

def get_bulk_operation_status():
    url = f"{BASE_URL}/graphql.json"
    query = { "query": '{ currentBulkOperation { id status url errorCode } }' }
    response = requests.post(url, headers=HEADERS, json=query)
    response.raise_for_status()
    return response.json()["data"]["currentBulkOperation"]

def download_bulk_file(url):
    response = requests.get(url)
    response.raise_for_status()
    lines = response.text.strip().split("\n")
    print(f"✅ Downloaded bulk data file with {len(lines)} lines.")
    
    products = []
    for line in lines:
        try:
            data = json.loads(line)
            if "title" in data and "variants" in data:
                products.append(data)
        except Exception as e:
            print("❌ Error parsing line:", e)
    print(f"✅ Parsed {len(products)} products from bulk data.")
    return products

def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", {"version": "2.0"})
    shop = ET.SubElement(rss, "shop")
    ET.SubElement(shop, "name").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(shop, "company").text = "Rubaska"
    ET.SubElement(shop, "url").text = "https://rubaska.com/"

    # Категории
    categories = ET.SubElement(shop, "categories")
    ET.SubElement(categories, "category", id="129880800", parentId="129880784").text = "Чоловічі сорочки"
    ET.SubElement(categories, "category", id="129880791", parentId="129880784").text = "Чоловічі футболки та майки"
    ET.SubElement(categories, "category", id="129883725", parentId="129880784").text = "Святкові жилети"

    offers = ET.SubElement(shop, "offers")

    for product in products:
        for variant in product.get("variants", []):
            offer = ET.SubElement(offers, "offer", attrib={
                "id": str(variant["id"].split("/")[-1]),
                "available": "true" if variant.get("inventoryQuantity", 0) > 0 else "false",
                "in_stock": "true",
                "type": "vendor.model",
                "selling_type": "r",
                "group_id": str(product["id"].split("/")[-1])
            })
            ET.SubElement(offer, "name").text = product["title"]
            ET.SubElement(offer, "model").text = variant["title"]
            ET.SubElement(offer, "vendor").text = product.get("vendor", "Rubaska")
            ET.SubElement(offer, "price").text = variant["price"]
            ET.SubElement(offer, "currencyId").text = "UAH"
            ET.SubElement(offer, "categoryId").text = "129880800"
            ET.SubElement(offer, "url").text = f"https://rubaska.com/products/{product['handle']}"
            for img in product.get("images", []):
                ET.SubElement(offer, "picture").text = img["src"]
            ET.SubElement(offer, "description").text = f"<![CDATA[{product['bodyHtml']}]]>"
            ET.SubElement(offer, "description_ua").text = f"<![CDATA[{product['bodyHtml']}]]>"

    return ET.ElementTree(rss)
