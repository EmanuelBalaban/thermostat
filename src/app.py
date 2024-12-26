import gc, machine, asyncio

import lib.aht as aht
import lib.helpers as helpers
import lib.mqtt_as as mqtt

gc.collect()

import config

# Heating enabled and desired temperature can be set from outside
state = {
    'heating_enabled': True,
    'relay_state': False,
    'gas_detected': False,
    'temperature': 0.0,
    'desired_temperature': 28.0,
}


async def main():
    # Initialize temp sensor
    print('Initializing temperature sensor...')
    i2c = machine.SoftI2C(scl=machine.Pin(9), sda=machine.Pin(8))
    sensor = aht.AHT20(i2c)
    gc.collect()

    # Connect to IoT hub
    print('Connecting to IoT Hub...')
    resource_uri = f"{config.IOT_HUB_HOSTNAME}/devices/{config.IOT_DEVICE_ID}/modules/{config.IOT_MODULE_ID}"
    sas_token = helpers.create_sas_token(resource_uri, config.IOT_SHARED_ACCESS_KEY)
    gc.collect()

    username = '{hostname}/{device_id}/{module_id}/?api-version={api_version}'.format(
        hostname=config.IOT_HUB_HOSTNAME,
        device_id=config.IOT_DEVICE_ID,
        module_id=config.IOT_MODULE_ID,
        api_version=config.IOT_HUB_API_VERSION)
    client_id = '{}/{}'.format(config.IOT_DEVICE_ID, config.IOT_MODULE_ID)

    username = bytes(username, 'utf-8')
    client_id = bytes(client_id, 'utf-8')

    # Set parameters
    mqtt.config['queue_len'] = 10
    mqtt.config['ssid'] = config.WIFI_SSID
    mqtt.config['wifi_pw'] = config.WIFI_PASSWD
    mqtt.config['server'] = config.IOT_HUB_HOSTNAME
    mqtt.config['client_id'] = client_id
    mqtt.config['user'] = username
    mqtt.config['password'] = sas_token
    mqtt.config['ssl'] = True
    gc.collect()

    # TODO: define last will

    mqtt.MQTTClient.DEBUG = True
    mqtt_client = mqtt.MQTTClient(mqtt.config)

    try:
        await mqtt_client.connect(quick=True)
        print('Connected to IoT Hub!')
        gc.collect()

        for coroutine in (up, messages):
            asyncio.create_task(coroutine(mqtt_client))

        # Request device twin
        await request_device_twin(mqtt_client)

        # Main loop
        while True:
            await asyncio.sleep(0)

            state_clone = set(state.items())

            state['temperature'] = sensor.temperature
            if state['heating_enabled']:
                state['relay_state'] = state['temperature'] < state['desired_temperature']

            diff = set(state.items()) - state_clone

            print('Updating device twin: ', diff)
            await update_device_twin(mqtt_client, dict(diff))

            gc.collect()
            await asyncio.sleep(30)
    finally:
        mqtt_client.close()


async def messages(client: mqtt.MQTTClient):
    """ Respond to incoming MQTT messages """
    topic: bytes
    msg: bytes
    retained: bool

    async for topic, msg, retained in client.queue:
        await asyncio.sleep(0)  # Allow other instances to be scheduled

        print(f'Received message from topic {topic}: {msg}')

        topic: str = topic.decode()

        if topic.startswith('$iothub/twin/res/200/') and len(msg) > 0:
            # Make sure it's a GET response

            import json

            device_twin = json.loads(msg)

            print('Got device twin: ', device_twin)

        gc.collect()


async def up(client: mqtt.MQTTClient):
    """ Respond to connection changes with MQTT client """
    while True:
        await client.up.wait()
        client.up.clear()

        # Subscribe to topics
        await client.subscribe('$iothub/twin/res/#')
        await client.subscribe('$iothub/twin/PATCH/properties/reported/#')
        await client.subscribe('$iothub/twin/PATCH/properties/desired/#')


async def request_device_twin(client: mqtt.MQTTClient):
    """ Request device twin """
    # https://learn.microsoft.com/en-us/azure/iot/iot-mqtt-connect-to-iot-hub#retrieving-a-device-twins-properties
    topic = '$iothub/twin/GET/?$rid={}'.format(helpers.uuid())
    await client.publish(topic, b'', qos=1)


async def update_device_twin(client: mqtt.MQTTClient, values: dict):
    """ Update device twin with current state """
    # https://learn.microsoft.com/en-us/azure/iot/iot-mqtt-connect-to-iot-hub#update-device-twins-reported-properties
    import json
    topic = '$iothub/twin/PATCH/properties/reported/?$rid={}'.format(helpers.uuid())
    await client.publish(topic, json.dumps(values), qos=1)
