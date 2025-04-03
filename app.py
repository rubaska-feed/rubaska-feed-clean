from flask import Flask, Response
from script import get_products, generate_xml
import xml.etree.ElementTree as ET
import traceback

app = Flask(__name__)

@app.route("/feed.xml")
def feed():
    try:
        products = get_products()
        xml_tree = generate_xml(products)
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(xml_tree.getroot(), encoding="unicode")
        return Response(xml_string, mimetype='application/xml')
    except Exception as e:
        error_trace = traceback.format_exc()
        print(error_trace)  # Это выведет в логи Render
        return Response(f"<h1>Internal Server Error</h1><pre>{error_trace}</pre>", status=500, mimetype='text/html')
