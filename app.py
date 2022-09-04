from json import dumps
import logging
import os

from flask import (Flask,g,request,Response,jsonify,)
from neo4j import (GraphDatabase,basic_auth,)


app = Flask(__name__)

url = os.getenv("NEO4J_URI", "bolt://localhost:6677")
username = os.getenv("NEO4J_USER", "")
password = os.getenv("NEO4J_PASSWORD", "")
neo4j_version = os.getenv("NEO4J_VERSION", "3.3.0")
database = os.getenv("NEO4J_DATABASE", "kuwaiba")

# url = os.getenv("NEO4J_URI", "neo4j+s://demo.neo4jlabs.com")
# username = os.getenv("NEO4J_USER", "movies")
# password = os.getenv("NEO4J_PASSWORD", "movies")
# neo4j_version = os.getenv("NEO4J_VERSION", "4")
# database = os.getenv("NEO4J_DATABASE", "movies")

port = os.getenv("PORT", 8080)

driver = GraphDatabase.driver(url, auth=basic_auth(username, password))


def get_db():
    if not hasattr(g, "neo4j_db"):
        if neo4j_version.startswith("4"):
            g.neo4j_db = driver.session(database=database)
        else:
            g.neo4j_db = driver.session()
    return g.neo4j_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "neo4j_db"):
        g.neo4j_db.close()


@app.route("/")
def get_index():
    return "hello"

def serialize_data(record):
    return {
        "Device": record["n.name"],
        "Interface": record["m.name"],
        "Port Type": record["c.name"],
        "RouterType": record["v.name"]
    }

def serialize_port_data(record):
    return {
        "name": record["name"],
        "className": record["className"],
        "state": record["p.state"],
        "ipAddress": record["p.ipAddress"],
        "interfaceSpeed": record["p.interfaceSpeed"],
        "interfaceDescription": record["p.interfaceDescription"],
        "parentAggreagationPort": record["p.parentAggreagationPort"],
    }

@app.route('/query', methods=['POST'])
def get_search():
    getQuery = request.json['query']
    def work(tx):
        return list(tx.run(getQuery))

    db = get_db()
    results = db.read_transaction(work)

    return Response(
        dumps([serialize_data(record) for record in results]),
        mimetype="application/json"
    )

@app.route('/getPortList', methods=['POST'])
def get_port_list():
    className = request.json['className']
    deviceId = request.json['deviceId']
    # deviceName = request.json['deviceName']
    def work(tx,className,deviceId):
        return list (tx.run("match (c:classes)<-[:INSTANCE_OF]-(d:inventoryObjects)<-[:CHILD_OF]-(p:inventoryObjects)-[:INSTANCE_OF]->(pc:classes) where c.name contains $className and d._uuid = $deviceId return p.name as name,pc.name as className,p.state,p.ipAddress,p.interfaceSpeed,p.interfaceDescription,p.parentAggreagationPort",
            {"className": className,"deviceId":deviceId}))



    db = get_db()
    results = db.read_transaction(work,className,deviceId)

    return Response(
        dumps([serialize_port_data(record) for record in results]),
        mimetype="application/json"
    )

if __name__ == "__main__":
    logging.root.setLevel(logging.INFO)
    logging.info("Starting on port %d, database is at %s", port, url)
    app.run(debug=True,port=port)