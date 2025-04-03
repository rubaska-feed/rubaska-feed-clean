from flask import Flask, Response
from script import get_products, generate_xml

app = Flask(__name__)

@app.route("/feed.xml")
def feed():
    products = get_products()
    xml_tree = generate_xml(products)
    xml_string = '<?xml version="1.0" encoding="UTF-8"?>\\n' + ET.tostring(xml_tree.getroot(), encoding="unicode")
    return Response(xml_string, mimetype='application/xml')
