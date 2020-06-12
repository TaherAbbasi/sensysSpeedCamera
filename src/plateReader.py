import time
import base64
from io import BytesIO
from PIL import Image
from pystalkd.Beanstalkd import Connection

class plateReader():
    def __init__(self):
        self.image_producer = Connection("localhost", 14714)
        self.image_producer.use("image")
        self.result_consumer = Connection("localhost", 14714)
        self.result_consumer.watch("result")


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
        ## sample snipet code for recieving result
        # print("data wait")
        message = self.result_consumer.reserve(timeout=10)
        if message:
            data = message.body
            message.delete()
            return data
        else:
            return None
            