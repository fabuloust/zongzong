# -*- coding:utf-8 -*-
"""
七牛存储服务
参考文档：https://developer.qiniu.com/kodo/sdk/1242/python
"""
import base64
import logging

from qiniu import Auth, put_data, put_file, BucketManager, PersistentFop

DEFAULT_PRIVATE_ASYNC_QUEUE = 'cy_media_queue'  # 私有异步队列,默认可以建立4个,相较于公用队列,性能比较好


class QiniuCloudStorageManager(object):
    # 考虑到不同云可能会有不同的操作, 暂时不抽取基类, 要用别的云服务时再抽取
    _access_key = 'bS1jrra7QasFM8gYVWiNHX_myrUVHczvUvl0pSUU'
    _secret_key = 'Lwzan8E_O1zLE_Sfem0tuwY5WkuONUAtIWG67NLF'

    def __init__(self, bucket, default_host):
        self.bucket = bucket
        self.default_host = default_host
        self.auth = Auth(self._access_key, self._secret_key)
        self.bucket_manager = BucketManager(self.auth)

    def get_upload_token(self, **kwargs):
        """
        kwargs:
            key:     上传的文件名，默认为空
            expires: 上传凭证的过期时间，默认为3600s
            policy:  上传策略，默认为空
        :return: 上传用的token
        """
        return self.auth.upload_token(self.bucket, **kwargs)

    def get_absolute_url(self, path, host=''):
        """
        根据path获取完整url
        :param path: 文件在云上的path, 即key
        :param host: 需要返回的类型域名，默认为chunyu服务器域名
        :return: 完整url
        e.g. host = 'http://media2.chunyu.mobi/'
        get_absolute_url('media/images/abc.jpg') -> 'http://media2.chunyu.mobi/media/images/abc.jpg'
        get_absolute_url('/media/images/abc.jpg') -> 'http://media2.chunyu.mobi/@/media/images/abc.jpg'
        
        note: 
        文件名以“/”开头，访问的时候需要显式的加上@符 (这是由于早期使用又拍云需要以“/”开头，转到七牛之后也沿用了这个逻辑，
        而七牛对于以“/”开头的key，都需要加上@符
        """
        host = host if host else self.default_host
        return 'https://%s/' % host + ("@" if path.startswith('/') else "") + path

    def upload_file(self, target_path, local_file, **extras):
        """
        上传文件到七牛
        :param target_path: 目标路径, 即key
        :param local_file: 本地文件路径
        :param extras: 额外参数, 会传给put_file
            params:           自定义变量，规格参考 http://developer.qiniu.com/docs/v6/api/overview/up/response/vars.html#xvar
            mime_type:        上传数据的mimeType
            check_crc:        是否校验crc32
            progress_handler: 上传进度
        :return: 成功时 dict - {hash, key (target_path)}, string - url
                 失败时 None, ''
                       
        e.g. 
        upload_file('/media/images/abc.jpg', '/tmp/images/abc.jpg') ->
            ({'hash': 'FoKvLQ2X9xBO9aCKsmhmhjJdC4NA', 'key': '/media/images/abc.jpg'},
             'http://media2.chunyuyisheng.com/@/media/images/abc.jpg')
        """
        return self._upload(put_file, target_path, file_path=local_file, **extras)

    def upload_data(self, target_path, data, **extras):
        """
        通过stream上传到七牛
        :param target_path: 目标路径, 即key
        :param data: stream
        :param extras: 额外参数, 会传给put_data
            params:           自定义变量，规格参考 http://developer.qiniu.com/docs/v6/api/overview/up/response/vars.html#xvar
            mime_type:        上传数据的mimeType
            check_crc:        是否校验crc32
            progress_handler: 上传进度
        :return: 成功时 dict - {hash, key (target_path)}, string - url
                 失败时 None, ''
                 
        e.g. 
        upload_file('/media/images/abc.jpg', open('/tmp/images/abc.jpg')) ->
            ({'hash': 'FoKvLQ2X9xBO9aCKsmhmhjJdC4NA', 'key': '/media/images/abc.jpg'},
             'http://media2.chunyuyisheng.com/@/media/images/abc.jpg')
        """
        return self._upload(put_data, target_path, data=data, **extras)

    def _upload(self, upload_func, target_path, **kwargs):
        result, resp = upload_func(self.get_upload_token(), target_path, **kwargs)
        # 失败时result为None
        if not result:
            logging.exception('Failed when uploading (%s), resp: %s' % (target_path, resp))
            return None, ""
        return result, self.get_absolute_url(target_path)

    def delete_file(self, file_path):
        """
        删除七牛的指定文件
        :param file_path：文件路径是七牛的存储路径，比如：/media/images/2015/03/18/e65f32bb8da7_w500_h500_.png
        return: error msg, 成功时返回 None
        """
        # note: delete成功时result为{}而不是docstring中写的NULL
        # note: date:2017-10-02 author:hedongxu
        # delete删除时，如果七牛上面没有目标文件，result返回None，status_code=612
        # http响应状态码说明：
        # 200	删除成功
        # 400	请求报文格式错误
        # 401	管理凭证无效
        # 599	服务端操作失败，如遇此错误，请将完整错误信息（包括所有HTTP响应头部）通过邮件发送给我们
        # 612	待删除资源不存在
        result, info = self.bucket_manager.delete(self.bucket, file_path)
        if info.status_code != 200:
            err_msg = result.get('error', None) if result else None
            logging.error('Failed when deleting (%s), reason: %s , status_code: %s', file_path, err_msg, info.status_code)
            return err_msg
        return None

    def get_file_info(self, file_path):
        """
        获取文件信息
        :param file_path: 文件路径 (key)
        :return: {mimeType, hash, fsize, putTime} / None if file doesn't exist
        """
        result, _ = self.bucket_manager.stat(self.bucket, file_path)
        return result

    def file_exists(self, file_path):
        """
        判断文件是否存在
        :param file_path: 文件路径 (key)
        :return: bool
        """
        return bool(self.get_file_info(file_path))

    def fetch_by_url(self, url, file_path, webp_auto_convert=True):
        """
        从远程url抓取文件
        :param url: 远程url
        :param file_path: 文件存放路径, 为None时使用文件hash
        :param webp_auto_convert: 是否对webp图片文件自动转码
        :return: {mimeType, hash, fsize, key} / None if error happened
        """
        result, resp = self.bucket_manager.fetch(url, self.bucket, file_path)
        # 虽然七牛的文档里写fetch的返回值, 如果error的话会返回{"error": "error_msg"}
        # 但实际我测试了3种error: bucket不存在, url不存在, url返回的状态码不为200
        # 七牛返回的result都是None, 实际的error msg会放在ResponseInfo的text_body中
        # 所以暂认是它的文档不对, error返回的就是None
        if not result:
            logging.info('Fetching (%s) failed with error: %s', url, resp.error)
            return result

        # 如果是webp, ios目前不支持, 进行格式转换
        if webp_auto_convert and result.get('mimeType') == 'image/webp':
            logging.info('Converting %s to jpg' % file_path)
            self.convert_img(file_path, 'jpg', force=1)

        return result

    def convert_img(self, src_path, new_type, dst_path=None, force=0):
        """
        :param src_path: 待转码的源文件
        :param new_type: 新类型
        :param dst_path: 转码后存放的文件名, 为None则覆盖源文件
        :param force: 是否强制覆盖已经存在原来的文件,否则如果new_key对应的文件已经存在就不执行命令了
        :return: result_dict, 类似{"persistentId": 5476bedf7823de4068253bae};
                persistentId可以用于查询异步任务的进度,如:http://api.qiniu.com/status/get/prefop?id=z0.5896682345a2650cfd7733b2
        """

        pfop_instance = PersistentFop(self.auth, self.bucket, DEFAULT_PRIVATE_ASYNC_QUEUE)
        # 如果不传表示覆盖
        dst_path = dst_path or src_path
        encoded_key = base64.b64encode('%s:%s' % (self.bucket, dst_path))
        # 转化格式并进行存储
        fops = ['imageMogr2/format/{new_type}|saveas/{encoded_key}'.format(new_type=new_type, encoded_key=encoded_key)]
        result, _ = pfop_instance.execute(src_path, fops, force=force)

        return result
