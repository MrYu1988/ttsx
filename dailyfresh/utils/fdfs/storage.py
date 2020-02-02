from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings
class FDFSStorage(Storage):
    def __init__(self, client_conf = None, base_url=None):
        '''初始化'''
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        if base_url is None:
            base_url = settings.FDFS_URL
        self.client_conf = client_conf
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        #创建一个fdfs客户端对象
        client = Fdfs_client(self.client_conf)
        #上传文件到fast——dfs系统中
        res = client.upload_by_buffer(content.read())


        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }

        if res.get('Status') != 'Upload successed.':
            raise Exception('上传文件到fast_dfs失败')

        #获取返回到文件id
        filename = res.get('Remote file_id')
        return filename

    def exists(self, name):
        '''判断django文件是否可用'''
        return False

    def url(self, name):
        return self.base_url+name






