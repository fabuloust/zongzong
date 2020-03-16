import qiniu
import requests

from qiniu_cloud import ServerBucket

QINIU_ACCESS_KEY = 'bS1jrra7QasFM8gYVWiNHX_myrUVHczvUvl0pSUU'
QINIU_SECRET_KEY = 'Lwzan8E_O1zLE_Sfem0tuwY5WkuONUAtIWG67NLF'

ACTION = 'https://up-z1.qiniup.com'


def get_upload_token():
    q = qiniu.Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    return q.upload_token('zonez')


def upload_image(file, file_name):

    server_bucket = ServerBucket
    result, url = server_bucket.upload_data('back_admin/{}'.format(file_name), file)
    return url
