from qiniu import QiniuMacAuth, http
import json

from utilities.upload_utils import QINIU_ACCESS_KEY, QINIU_SECRET_KEY


def is_image_valid(image_url):
    url = 'http://ai.qiniuapi.com/v3/image/censor'
    auth = QiniuMacAuth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    body = {
        "data": {
            "uri": "<uri>"
        },
        "params": {
            "scenes": []
        }
    }
    scenes = {
        'censor': ['pulp', 'terror', 'politician', 'ads'],
        'pulp': ['pulp'],
        'terror': ['terror'],
        'politician': ['politician'],
            'ads': ['ads']
    }
    body["params"]["scenes"] = ['pulp', 'terror', 'politician']
    body["data"]["uri"] = image_url
    ret, res = http._post_with_qiniu_mac(url, body, auth)
    headers = {"code": res.status_code, "reqid": res.req_id, "xlog": res.x_log}
    print(json.dumps(headers, indent=4, ensure_ascii=False))
    print(json.dumps(ret, indent=4, ensure_ascii=False))