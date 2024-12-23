import machine, utime, ssl

import lib.aht as aht
import lib.helpers as helpers
# from lib.mqtt_twin_client import MqttTwinClient
from umqtt.simple import MQTTClient

import config

state = {
    'heating_enabled': False,
    'relay_state': False,
    'gas_detected': False,
    'temperature': 0.0,
    'desired_temperature': 22.0,
}
sas_token: str = ''


def main():
    global sas_token

    # Initialize temp sensor
    print('Initializing temperature sensor...')
    i2c = machine.SoftI2C(scl=machine.Pin(9), sda=machine.Pin(8))
    sensor = aht.AHT20(i2c)

    # Connect to IoT hub
    print('Connecting to IoT Hub...')
    resource_uri = f"{config.IOT_HUB_HOSTNAME}/devices/{config.IOT_DEVICE_ID}/modules/{config.IOT_MODULE_ID}"
    sas_token = helpers.create_sas_token(resource_uri, config.IOT_SHARED_ACCESS_KEY)
    mqtt_client = MQTTClient(
        server=config.IOT_HUB_HOSTNAME,
        client_id=f'{config.IOT_DEVICE_ID}/{config.IOT_MODULE_ID}',
        user=f"{config.IOT_HUB_HOSTNAME}/{config.IOT_DEVICE_ID}/{config.IOT_MODULE_ID}/?api-version={config.IOT_HUB_API_VERSION}",
        password=sas_token,
        ssl=ssl,
        keepalive=60
    )
    mqtt_client.set_callback(mqtt_callback)
    mqtt_client.connect()
    print('Connected to IoT Hub!')

    # TODO: subscribe to topics
    mqtt_client.subscribe('$iothub/twin/res/#')
    mqtt_client.publish('$iothub/twin/GET/?$rid=7df99930-c685-4a79-9bb2-e5e7fa50e14c', 'test')

    print('Requested twin...')

    # Main loop
    while True:
        try:
            print('Ping')

            mqtt_client.check_msg()
            mqtt_client.ping()

            state['temperature'] = sensor.temperature
            if state['heating_enabled']:
                state['relay_state'] = state['temperature'] < state['desired_temperature']

            # message = json.dumps(state)
            # mqtt_client.publish(TOPIC_COMMAND, message)
            # mqtt_client.check_msg()

            # update_device_twin()

            utime.sleep(30)
        finally:
            try:
                mqtt_client.disconnect()
            except:
                print('Unable to disconnect from IoT Hub')


def mqtt_callback(topic, msg):
    global state

    print(f'Received message from topic {topic}: {msg}')

    # TODO: update state


def twin_callback(twin: dict):
    print(twin)
