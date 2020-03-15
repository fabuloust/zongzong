import qiniu
import requests

from qiniu_cloud import ServerBucket

QINIU_ACCESS_KEY = 'bS1jrra7QasFM8gYVWiNHX_myrUVHczvUvl0pSUU'
QINIU_SECRET_KEY = 'Lwzan8E_O1zLE_Sfem0tuwY5WkuONUAtIWG67NLF'

ACTION = 'https://up-z1.qiniup.com'


def get_upload_token():
    q = qiniu.Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    return q.upload_token('zonez')


def upload_image(file):

    server_bucket = ServerBucket
    result = server_bucket.upload_data('/image/temp', file)
    print(result)
    # return result
    # headers = {'content-type': 'multipart/form-data'}
    # result = requests.post('http://upload.qiniup.com', {'action': ACTION, 'resource_key': 'test',
    #                                                     'upload_token': upload_token, 'file': file}, headers=headers)
    # print(result.content)
    #
    # # return url