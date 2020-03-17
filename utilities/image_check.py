from qiniu import QiniuMacAuth, http

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
    body["params"]["scenes"] = ['pulp', 'terror', 'politician']
    body["data"]["uri"] = image_url
    ret, res = http._post_with_qiniu_mac(url, body, auth)

    if res.status_code == 200:
        is_valid = ret['result']['suggestion'] == 'pass'
    else:
        is_valid = False
    return is_valid
