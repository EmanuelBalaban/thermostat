import machine, ubinascii, time, json
from umqtt.simple import MQTTClient

import lib.aht as aht

import config

sensor: aht.AHT20
client: MQTTClient


def send_discovery_message(client: MQTTClient):
    print("Sending discovery messages...")

    for topic, payload in [
        (
            config.MQTT_TEMPERATURE_DISCOVERY_TOPIC,
            config.MQTT_TEMPERATURE_DISCOVERY_PAYLOAD,
        ),
        (config.MQTT_HUMIDITY_DISCOVERY_TOPIC, config.MQTT_HUMIDITY_DISCOVERY_PAYLOAD),
    ]:
        print(topic)

        discovery_message = json.dumps(payload)

        print(discovery_message)

        client.publish(topic, discovery_message.encode(), retain=True)
        client.check_msg()


def configure_mqtt_client() -> MQTTClient:
    print("Connecting to MQTT broker...")

    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, config.MQTT_SERVER, keepalive=60)
    client.connect()

    print("Connected to MQTT broker!")
    send_discovery_message(client)

    return client


def main():
    global sensor

    # Initialize temp sensor
    print("Initializing temperature sensor...")
    i2c = machine.SoftI2C(
        scl=machine.Pin(config.SCL_PIN), sda=machine.Pin(config.SDA_PIN)
    )
    sensor = aht.AHT20(i2c)

    global client

    # Connecting to MQTT
    try:
        client = configure_mqtt_client()
    except OSError as e:
        print(e)

        print("Failed to connect. Restarting...")
        time.sleep(10)
        machine.reset()

    # Main loop
    while True:
        try:
            temperature: float = round(sensor.temperature, 2)
            msg = str(temperature)

            print("Temperature: ", temperature)

            client.publish(config.MQTT_TEMPERATURE_TOPIC, msg, retain=False)
            client.check_msg()

            humidity: float = round(sensor.relative_humidity, 2)
            msg = str(humidity)

            print("Humidity: ", humidity)
            client.publish(config.MQTT_HUMIDITY_TOPIC, msg, retain=False)
            client.check_msg()

            time.sleep(config.SENSOR_POLL_TIME)
        except OSError as e:
            print(e)

            print("Failed to send reading. Restarting...")
            time.sleep(10)
            machine.reset()


main()
