import requests
class ConfigGetter:
    def __init__(self, url_prefix):
        self.url_prefix = url_prefix

    def get_value(self, section, option):
        request_str = self.url_prefix + "/{}/{}".format(section, option)
        response = requests.get(request_str)
        return response.json()

    def get_active_stream(self, stream_component_id):
        request_str = self.url_prefix+ "/get_active_stream/{}".format(stream_component_id) 
        response = requests.get(request_str)
        return list(response.json())
