from Adafruit_IO import MQTTClient
import sys

AIO_FEED_ID = ['schedules']

def connected(client):
    print("Ket noi thanh cong ...")
    for topic in AIO_FEED_ID:
        client.subscribe(topic)

def subscribe(client , userdata , mid , granted_qos):
    print("Subscribe thanh cong ...")

def disconnected(client):
    print("Ngat ket noi ...")
    sys.exit (1)

def create_client(USER_NAME,KEY,message,connected=connected,disconnected=disconnected,subscribe=subscribe):
    client = MQTTClient(USER_NAME , KEY)
    client.on_connect = connected
    client.on_disconnect = disconnected
    client.on_message = message
    client.on_subscribe = subscribe
    client.connect()
    client.loop_background() # for_blocking  (stop in heres)
    
    return client

