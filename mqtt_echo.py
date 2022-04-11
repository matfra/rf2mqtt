#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import argparse
import logging
logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',                        
                        format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s', )
log = logging.getLogger('mqtt_echo')


def main():
    parser = argparse.ArgumentParser(description='Subscribe to MQTT server and display messages')
    parser.add_argument('-m', dest='mqtt_broker_addr', type=str, default='127.0.0.1',
            help="Address of the MQTT broker (default: 127.0.0.1)")
    parser.add_argument('-p', dest='mqtt_broker_port', type=int, default=1883,
            help="Port of the MQTT broker (default: 1883)")
    parser.add_argument('-t', dest='mqtt_topic', type=str, default='rc',
            help="Topic to send the messages to (default: rc)")
    parser.add_argument('-v', dest='verbose', action='store_true',
            help="More verbose logs")
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(args.mqtt_broker_addr, args.mqtt_broker_port, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
    client.loop_forever()
# The callback for when the client receives a CONNACK response from the server.

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(args.mqtt_topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


if __name__ == "__main__":
    main()
