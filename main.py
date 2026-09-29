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
response: {"code": "...", "short_url": "..."}

2. GET /<code>

response: 302/404/410

3. DELETE /<code>

response: 204/404

4. PATCH /<code>

request: {"url": "..."}/ {"expires_in": ...}
response: {"code": "...", "original_url": "..."}

"""
from flask import Flask
