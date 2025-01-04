import asyncio, ujson, machine, neopixel

import config

relay_state = False
gas_detected = False

neo_pixel_pin = 1
relay_pin = 10
gas_sensor_pin = 4

gas_sensor = machine.ADC(machine.Pin(gas_sensor_pin, machine.Pin.IN))


async def main():
    asyncio.create_task(watch_state())
    asyncio.create_task(monitor_gas_sensor())

    while True:
        await asyncio.sleep(1)


async def watch_state():
    global relay_state

    host = config.API_URL.split('://')[1]

    while True:
        try:
            reader: asyncio.StreamReader
            writer: asyncio.StreamWriter

            # TODO: handle server restarts
            reader, writer = await asyncio.open_connection(
                host=host,
                port=443,
                ssl=True
            )

            writer.write(f'GET /state HTTP/1.1\r\nHost: {host}\r\nAccept: text/event-stream\r\n\r\n')

            await writer.drain()

            print('Connected to server!')

            while True:
                line = await reader.readline()
                if line.startswith(b'data:'):
                    event_data = line[5:].strip()
                    updates = ujson.loads(event_data)
                    if 'relay_state' in updates:
                        relay_state = updates['relay_state']
                        react_to_relay_state()

        except Exception as e:
            print(f"Error connecting to /state: {e}")
            await asyncio.sleep(5)  # Retry after a delay


async def monitor_gas_sensor():
    while True:
        print(gas_sensor.read_uv())

        adc_value = gas_sensor.read()  # values between 0 and 4095
        gas_percentage = adc_value * 100 / 4095

        print(f'Gas sensor: {adc_value}\nGas percentage: {gas_percentage}')

        # TODO: send patch

        await asyncio.sleep(config.SENSOR_POLL_TIME)


def set_brightness(color, brightness):
    return tuple(int(c * brightness) for c in color)


def react_to_relay_state():
    relay = machine.Pin(relay_pin, machine.Pin.OUT)
    np = neopixel.NeoPixel(machine.Pin(neo_pixel_pin, machine.Pin.OUT), 1)

    if relay_state:
        np[0] = set_brightness((255, 0, 0), 0.1)  # Red
        relay.on()
        print('Heating is ON')
    else:
        np[0] = set_brightness((0, 0, 0), 0.0)  # Black
        relay.off()
        print('Heating is OFF')

    np.write()
