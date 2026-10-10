"""
Shortener Flask应用

接口文档:

|   方法   |    路径    |   作用   |
|----------|-----------|-----------|
|   POST   |  /short |  创建短链  |
|   GET    |  /`code`  |重定向(到源)|
|   DELETE |  /`code`  |  删除短链  |
|   PATCH  |  /`code`  |  修改短链  |

接口细节:
1. POST /short

request: {"url": "...", "expire_in" : ...}
response: {"code": "...", "url": "..."}, 201 Created
        /{"code": "...", "url": "..."}, 200 OK
        /400 Bad Request
        /500 Internal Server Error

2. GET /`code`

response: 302 Found/404 Not Found/410 Gone

3. DELETE /`code`

response: 204 No Content/404 Not Found

4. PATCH /`code`

request: {"url": "..."}/ {"expires_in": ...}
response: {"code": "...", "url": "..."}, 200
        /404 Not Found
        /400 Bad Request
        /415 Unsupported Media Type
        /422 Unprocessable Content
        /410 Gone

"""
import re
from typing import cast, Any
from flask import Flask, request, jsonify, abort, redirect
import mapservice

URL = re.compile(
    r"^https?://"
    r"(?:(?:[A-Za-z0-9._~!$&'()*+,;=:-]|%[0-9A-Fa-f]{2})+@)?"
    r"(?:"
        r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}"
        r"|localhost"
        r"|(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
        r"|\[[0-9A-Fa-f:.]+\]"
    r")"
    r"(?::\d{1,5})?"
    r"(?:[/?#][^\s]*)?"
    r"$"
)

def create_app(service : mapservice.MapService) -> Flask:
    """创建Shortener应用

    Args:
        service (mapservice.MapService): 业务层

    Returns:
        Flask: Shortener 应用
    """

    app = Flask(__name__)

    @app.route("/short", methods = ['POST'])
    def short():
        """
        创建短链

        """
        data = cast(dict[str, Any] | None, request.get_json(silent = True))
        if not data:
            abort(400)

        if len(data.keys()) != 2 :
            abort(400)

        try:
            url = str(data["url"])
            expire_in = int(data["expire_in"])

            if not bool(URL.fullmatch(url)):
                raise ValueError
            if expire_in < 0:
                raise ValueError

            ok, code = service.add(url, expire_in)
            if code == "" :
                raise IndexError
            return jsonify({'code': code, 'url': url}), (201 if (ok) else 200)
        except BaseException:
            abort(400)


    @app.route("/<code>", methods = ['GET'])
    def get(code):
        """
        重定向

        """
        code = str(code)
        if len(code) != 6:
            abort(404)

        res = service.get(code)
        if (res == (mapservice.MapService.
            NoneType.UNKNOWN)):
            abort(404)
        elif (res == (mapservice.MapService.
            NoneType.EXPIRED)):
            abort(410)
        else :
            return redirect(res)

    @app.route("/<code>", methods = ['DELETE'])
    def remove(code):
        """
        删除短链

        """
        code = str(code)
        if len(code) != 6:
            abort(404)

        ok = service.remove(code)
        if ok:
            return '', 204
        abort(404)

    @app.route("/<code>", methods = ['PATCH'])
    def update(code):
        """
        修改短链

        """
        code = str(code)
        if len(code) != 6:
            abort(404)

        data = cast(dict[str, Any] | None, request.get_json())
        if not data:
            abort(400)

        if len(data.keys()) != 1:
            abort(400)
        target, param = data.popitem()
        if target not in ["url", "expire_in"]:
            abort(400)

        try:
            match target:
                case "url":
                    if not URL.fullmatch(param):
                        raise ValueError
                    param = str(param)
                case "expire_in":
                    param = int(param)
            res = service.patch(code, target, param)
            if (res == mapservice.MapService.
                NoneType.UNKNOWN):
                abort(404)
            if (res == mapservice.MapService.
                NoneType.EXPIRED):
                abort(410)
            return jsonify({'code': res[1], 'url': res[0]}), 200
        except (ValueError, TypeError, OverflowError, UnicodeError):
            abort(422)

    return app
