import gc, machine, asyncio

import lib.aht as aht
import lib.helpers as helpers
import lib.mqtt_as as mqtt

gc.collect()

import config

state = {
    'heating_enabled': False,
    'relay_state': False,
    'gas_detected': False,
    'temperature': 0.0,
    'desired_temperature': 22.0,
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

    # Set parameters
    mqtt.config['ssid'] = config.WIFI_SSID
    mqtt.config['wifi_pw'] = config.WIFI_PASSWD
    mqtt.config['server'] = config.IOT_HUB_HOSTNAME
    mqtt.config['client_id'] = f'{config.IOT_DEVICE_ID}/{config.IOT_MODULE_ID}'
    mqtt.config[
        'user'] = f"{config.IOT_HUB_HOSTNAME}/{config.IOT_DEVICE_ID}/{config.IOT_MODULE_ID}/?api-version={config.IOT_HUB_API_VERSION}"
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

        # Main loop
        while True:
            await asyncio.sleep(0)

            state['temperature'] = sensor.temperature
            if state['heating_enabled']:
                state['relay_state'] = state['temperature'] < state['desired_temperature']

            print('Current state is ', state, '\n')

            # Request device twin
            await mqtt_client.publish(
                topic='$iothub/twin/GET/?$rid={}'.format(helpers.uuid()),
                msg='',
                qos=1
            )

            # message = json.dumps(state)
            # mqtt_client.publish(TOPIC_COMMAND, message)
            # mqtt_client.check_msg()

            # update_device_twin()

            await asyncio.sleep(30)
    finally:
        mqtt_client.close()


async def messages(client: mqtt.MQTTClient):
    """ Respond to incoming MQTT messages """
    async for topic, msg, retained in client.queue:
        print(f'Received message from topic {topic}: {msg}')


async def up(client: mqtt.MQTTClient):
    """ Respond to connection changes with MQTT client """
    while True:
        await client.up.wait()
        client.up.clear()

        # Subscribe to topics
        await client.subscribe('$iothub/twin/res/#')
