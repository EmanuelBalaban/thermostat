import asyncio, urequests, machine, neopixel
from urequests import Response

import config

relay_state = False
gas_detected = False

neo_pixel_pin = 1
relay_pin = 10
gas_sensor_pin = 4

gas_sensor = machine.ADC(machine.Pin(gas_sensor_pin, machine.Pin.IN))
gas_sensor.atten(machine.ADC.ATTN_11DB)
gas_sensor.width(13)

relay = machine.Pin(relay_pin, machine.Pin.OUT)
np = neopixel.NeoPixel(machine.Pin(neo_pixel_pin, machine.Pin.OUT), 1)

ro_in_air: int = 0


async def main():
    relay.off()
    np[0] = set_brightness((0, 0, 0), 0.0)  # Black
    np.write()

    asyncio.create_task(watch_state())
    asyncio.create_task(monitor_gas_sensor())

    while True:
        await asyncio.sleep(1)


async def watch_state():
    """ Actively watches the relay state and reacts to updates. """

    global relay_state

    endpoint = f'{config.API_URL}/state/relay_state'

    while True:
        try:
            response: Response = urequests.get(endpoint)
            new_relay_state = response.json()

            if relay_state != new_relay_state:
                relay_state = new_relay_state
                react_to_relay_state()
        except Exception as e:
            print(f"Error fetching relay_state: {e}")

        # Request state every X seconds
        await asyncio.sleep(config.STATE_POLL_TIME)


async def monitor_gas_sensor():
    """ Actively monitors the gas sensor and recalibrates it after a given threshold. """

    global gas_detected

    await calibrate_gas_sensor()
    num_reads = 0

    while True:
        if num_reads >= config.GAS_SENSOR_RECALIBRATION_THRESHOLD:
            num_reads = 0
            await calibrate_gas_sensor()

        num_reads += 1
        gas_value = read_gas_sensor()

        print(f'Gas sensor: {gas_value}')

        old_gas_detected = gas_detected
        gas_detected = gas_value > config.GAS_SENSOR_ALARM_THRESHOLD

        if old_gas_detected != gas_detected:
            await react_to_gas_detected()

        await asyncio.sleep(config.GAS_SENSOR_POLL_TIME)


async def calibrate_gas_sensor():
    """ Calibrates the gas sensor by storing the RO in the air. """

    global ro_in_air

    print('Calibrating gas sensor...')

    ro_in_air = 0
    steps = config.GAS_SENSOR_CALIBRATION_STEPS

    for _ in range(steps):
        ro_in_air += gas_sensor.read()
        await asyncio.sleep(config.GAS_SENSOR_CALIBRATION_WAIT_TIME)

    ro_in_air /= steps

    print('Calibrated gas sensor. RO in air: ', ro_in_air)


def read_gas_sensor():
    """ Reads the gas sensors and subtracts the RO in air. Values between 0 and 8192 - RO """

    return gas_sensor.read() - ro_in_air


async def react_to_gas_detected():
    """ Reacts to gas detected updates. """

    import ujson

    global relay_state

    # Stop the heating system
    if gas_detected:
        relay_state = False
        react_to_relay_state()

    endpoint = f'{config.API_URL}/state'

    try:
        _ = await urequests.patch(
            endpoint,
            headers={'content-type': 'application/json'},
            data=ujson.dumps({'gas_detected': gas_detected}),
        )
    except:
        return


def react_to_relay_state():
    """ React to the new relay state. """

    if relay_state:
        np[0] = set_brightness((255, 0, 0), 0.1)  # Red
        relay.on()
        print('Heating is ON')
    else:
        np[0] = set_brightness((0, 0, 0), 0.0)  # Black
        relay.off()
        print('Heating is OFF')

    np.write()


def set_brightness(color, brightness):
    """ Adjust color with the given brightness. """

    return tuple(int(c * brightness) for c in color)
