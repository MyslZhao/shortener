"""
Flask应用入口
接口文档:
方法        路径        作用
POST    /shorten    创建短链
GET     /<code>     重定向(到源)
DELETE  /<code>     删除短链
PATCH   /<code>     修改短链

接口细节:
1. POST /short

request: {"url": "...", "expire_in" : ...}
response: {"code": "...", "short_url": "..."}, 201 Created

2. GET /<code>

response: 302 Found/404 Not Found/410 Gone

3. DELETE /<code>

response: 204 No Content/404 Not Found

4. PATCH /<code>

request: {"url": "..."}/ {"expires_in": ...}
response: {"code": "...", "original_url": "..."}, 200
        /404 Not Found
        /400 Bad Request
        /410 Gone

"""
from flask import Flask, request, jsonify, abort, redirect

app = Flask(__name__)

@app.route("/")
def hello():
    """
    测试

    """

    return "ok"

@app.route("/short", methods = ['POST'])
def short():
    """
    创建短链

    """
    abort(503, 'Service Unavailable')

@app.route("/<code>", methods = ['GET'])
def get():
    """
    重定向

    """
    abort(503, 'Service Unavailable')

@app.route("/<code>", methods = ['DELETE'])
def remove():
    """
    删除短链

    """
    abort(503, 'Service Unavailable')

@app.route("/<code>", methods = ['PATCH'])
def update():
    """
    修改短链

    """
    abort(503, 'Service Unavailable')

if __name__ == "__main__":
    app.run(debug = True)
