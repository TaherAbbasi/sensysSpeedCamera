import time
import base64
import logging
from io import BytesIO
from PIL import Image
from pystalkd.Beanstalkd import Connection
from .exceptions import *
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class plateReader():
    def __init__(self, host='localhost', port=14714):

        try:
            self.image_producer = Connection(host, port)
            self.image_producer.use("image")
            self.result_consumer = Connection(host, port)
            self.result_consumer.watch("result")
        except ALPRConnectionError as e:
            logging.exception(f'{e}')

    def run(self, cvImage):
        while True:
            message = self.result_consumer.reserve(timeout=0)
            if message:
                message.delete()
            else:
                break
        image = Image.fromarray(cvImage)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        # time.sleep(1)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        self.image_producer.put(img_str)
        ## sample snippet code for recieving result
        # print("data wait")
        message = self.result_consumer.reserve(timeout=10)
        if message:
            data = message.body
            message.delete()
            return data
        else:
            return None
    

    # def 