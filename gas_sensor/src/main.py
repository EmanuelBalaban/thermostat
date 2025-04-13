import math
import machine, ubinascii, time, json, neopixel
from umqtt.simple import MQTTClient

import config

client: MQTTClient
sensor: machine.ADC
np: neopixel.NeoPixel

ro_in_air: int = 0
gas_detected: bool = False


def main():
    global np

    # Initialize NeoPixel
    np = neopixel.NeoPixel(machine.Pin(config.NEO_PIXEL_DATA_PIN, machine.Pin.OUT), 1)
    np[0] = set_brightness((0, 0, 0), 0.0)  # Black
    np.write()

    global sensor

    # Initialize sensor
    print("Initializing gas sensor...")
    sensor = machine.ADC(machine.Pin(config.SENSOR_PIN, machine.Pin.IN))
    sensor.atten(machine.ADC.ATTN_11DB)
    sensor.width(13)

    global client

    # Connecting to MQTT
    try:
        client = configure_mqtt_client()
    except OSError as e:
        print(e)

        print("Failed to connect. Restarting...")
        time.sleep(10)
        machine.reset()

    try:
        monitor_gas_sensor()
    except OSError as e:
        print(e)

        print("Something went wrong. Restarting...")
        time.sleep(10)
        machine.reset()


def send_discovery_message(client: MQTTClient):
    print("Sending discovery messages...")
    discovery_messages = [
        (
            config.MQTT_DISCOVERY_TOPIC,
            config.MQTT_DISCOVERY_PAYLOAD,
        ),
        (
            config.MQTT_RAW_DISCOVERY_TOPIC,
            config.MQTT_RAW_DISCOVERY_PAYLOAD,
        ),
        (
            config.MQTT_DETECTED_DISCOVERY_TOPIC, 
            config.MQTT_DETECTED_DISCOVERY_PAYLOAD
        ),
    ]

    for gas in config.GAS_TYPES:
        discovery_messages.append((gas.discovery_topic(), gas.discovery_payload(config.MQTT_DISCOVERY_DEVICE)))

    for topic, payload in discovery_messages:
        discovery_message = json.dumps(payload)
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


def monitor_gas_sensor():
    """ Actively monitors the gas sensor and recalibrates it after a given threshold. """

    global gas_detected

    calibrate_gas_sensor()
    num_reads = 0

    while True:
        if num_reads >= config.SENSOR_RECALIBRATION_THRESHOLD:
            num_reads = 0
            calibrate_gas_sensor()
        num_reads += 1

        # Read the gas sensor. (0-8192)
        raw_value = sensor.read()
        gas_value = raw_value - ro_in_air

        print(f'Raw value: {raw_value}')
        print(f'Gas value (w/o Ro in air): {gas_value}')

        # Send raw value
        msg = str(raw_value)
        client.publish(config.MQTT_RAW_STATE_TOPIC, msg, retain=False)
        client.check_msg()

        # Send gas value (raw - ro_in_air)
        msg = str(gas_value)
        client.publish(config.MQTT_STATE_TOPIC, msg, retain=False)
        client.check_msg()

        # PPM
        Rs = raw_value
        Ro = ro_in_air
        ratio: float = Rs / Ro
        
        for gas in config.GAS_TYPES:
            ppm = gas.calculate_ppm(ratio)

            print(f'{gas.key}: {ppm} ppm')

            # Send PPM reading
            msg = str(ppm)
            client.publish(gas.state_topic(), msg, retain=False)
            client.check_msg()

        # Gas detected logic
        old_gas_detected = gas_detected
        gas_detected = gas_value > config.SENSOR_ALARM_THRESHOLD
        if old_gas_detected != gas_detected:
            react_to_gas_detected()

        time.sleep(config.SENSOR_POLL_TIME)


def calibrate_gas_sensor():
    """ Calibrates the gas sensor by storing the RO in the air. """

    global ro_in_air

    # TODO: add a calibrated flag via MQTT or LED blink pattern when the sensor is still warming up.

    print('Calibrating gas sensor...')

    ro_in_air = 0
    steps = config.SENSOR_CALIBRATION_STEPS

    for _ in range(steps):
        ro_in_air += sensor.read()
        time.sleep(config.SENSOR_CALIBRATION_WAIT_TIME)

    ro_in_air = int(ro_in_air / steps)

    print('Calibrated gas sensor. RO in air: ', ro_in_air)


def react_to_gas_detected():
    """ Reacts to gas detected by setting red color on NeoPixel """

    # Send gas detected flag
    mqtt_payload = b'on' if gas_detected else b'off'
    client.publish(config.MQTT_DETECTED_TOPIC, mqtt_payload, retain=False)
    client.check_msg()

    if gas_detected:
        np[0] = set_brightness((255, 0, 0), 0.1)  # Red
    else:
        np[0] = set_brightness((0, 0, 0), 0.0)  # Black

    np.write()


def set_brightness(color, brightness):
    """ Adjust color with the given brightness. """

    return tuple(int(c * brightness) for c in color)


main()