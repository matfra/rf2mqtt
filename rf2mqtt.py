#!/opt/rf2mqtt/venv/bin/python3
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import argparse
import signal
import sys
import time
import logging
import math

from rpi_rf import RFDevice

rfdevice = None

def exithandler(signal, frame):
    rfdevice.cleanup()
    sys.exit(0)

logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s', )
log = logging.getLogger('rc2mqtt')

def on_connect(client, userdata, flags, rc):
    log.info("Connected to MQTT broker with result code " + str(rc))

def mqtt_connect(host, port):
    client = mqtt.Client()
    # client.username_pw_set(username='user', password='pass')  # need this
    client.connect(host,  port=port)
    client.loop_start()  # run in background and free up main thread
    client.on_connect = on_connect  # call these on connect and on message
    return client


def mqtt_send(client, topic, payload):
    client.publish(topic, payload=payload.encode('utf-8'), qos=0, retain=False)

def check_if_allowed(code: int) -> bool:
    ALLOWED_PREFIXES=[
            68,
            533, #etek5
            552, #etek3_bed
            557, #etek3_kitchen
            1654,
            1265,
            526,
            786,
    ]
#    return True
    return int(math.floor(code/10000)) in ALLOWED_PREFIXES

def main():
    parser = argparse.ArgumentParser(description='Receives a decimal code via a 433/315MHz GPIO device and send it to an MQTT broker')
    parser.add_argument('-g', dest='gpio', type=int, default=27,
                        help="GPIO pin (Default: 27)")
    parser.add_argument('-m', dest='mqtt_broker_addr', type=str, default='127.0.0.1',
            help="Address of the MQTT broker (default: 127.0.0.1)")
    parser.add_argument('-p', dest='mqtt_broker_port', type=int, default=1883,
            help="Port of the MQTT broker (default: 1883)")
    parser.add_argument('-t', dest='mqtt_topic', type=str, default='rc',
            help="Topic to send the messages to (default: rc)")
    parser.add_argument('-r', dest='rate_limit', type=int, default=200,
            help="Rate limit in milliseconds to filter burst of codes sent by RF remotes (default: 200)")
    parser.add_argument('-d', dest='dev', action='store_true',
            help="Enable dev mode")
    parser.add_argument('-v', dest='verbose', action='store_true',
            help="More verbose logs")
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    MQTT_CONNECT_TIMEOUT=120
    timeout=0
    while timeout < MQTT_CONNECT_TIMEOUT:
        try:
            mqtt_client = mqtt_connect(args.mqtt_broker_addr, args.mqtt_broker_port)
        except ConnectionRefusedError:
            log.info("Could not connect to mqtt broker, Trying again in 5 sec...")
            time.sleep(5)
            timeout += 5
            continue
        break

    signal.signal(signal.SIGINT, exithandler)
    rfdevice = RFDevice(args.gpio)
    rfdevice.enable_rx()
    timestamp = None
    previous_signal=(0,0)
    log.info("Listening for codes on GPIO " + str(args.gpio))
    while True:
        if rfdevice.rx_code_timestamp != timestamp:
            timestamp = rfdevice.rx_code_timestamp
            code = rfdevice.rx_code
            protocol = rfdevice.rx_proto
            pulselength = rfdevice.rx_pulselength

            log.debug("code: {}, protocol: {}, timestamp: {}, pulselength: {}".format(
                code,
                protocol,
                timestamp,
                pulselength,
            ))
            previous_code, previous_timestamp = previous_signal
            min_delta_t = args.rate_limit * 1000
            if not check_if_allowed(code):
                log.debug("Blocked code {}".format(code))
                continue
            if code == previous_code:
                delta_t = timestamp - previous_timestamp
                if delta_t < min_delta_t:
                    log.debug("Rate limiting, got same code: {} and delta t: {}/{}".format(
                        code,
                        delta_t,
                        min_delta_t,
                        ))
                    continue
            mqtt_send(mqtt_client, args.mqtt_topic, str(code))
            previous_signal=(code,timestamp)

        time.sleep(0.01)
    rfdevice.cleanup()

if __name__ == "__main__":
    main()
