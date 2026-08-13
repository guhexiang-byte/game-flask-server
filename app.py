from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许TurboWarp跨域访问

# 内存存储
store_data = {}

# 获取全部数据 / 获取单个key数据
@app.route("/api/store", methods=["GET"])
def get_store():
    key = request.args.get("key")
    if key:
        res = store_data.get(key, {})
        return jsonify({"status":"success", "data": res})
    return jsonify({"status":"success", "data": store_data})

# 保存数据
@app.route("/api/store", methods=["POST"])
def save_store():
    body = request.get_json()
    key = body.get("key")
    value = body.get("value")
    if key is None:
        return jsonify({"status":"fail","msg":"缺少key"}),400
    store_data[key] = value
    return jsonify({"status":"success"})

# 删除key
@app.route("/api/store", methods=["DELETE"])
def del_store():
    key = request.args.get("key")
    if key and key in store_data:
        del store_data[key]
    return jsonify({"status":"success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)