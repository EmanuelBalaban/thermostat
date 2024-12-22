import asyncio, machine, network, utime

from libraries import aht
from libraries.microdot import Microdot

from seg_driver import Seg7Dig4Display

# Global variables
wlan: network.WLAN

i2c = machine.SoftI2C(scl=machine.Pin(9), sda=machine.Pin(8))
sensor = aht.AHT20(i2c)

# 7 Seg -> GPIO
# 1 -> 4
# 2 -> 10
# 3 -> 0
# 4 -> 18
# 5 -> 17
# 6 -> 7
# 7 -> 44
# 8 -> 43
# 9 -> 33
# 10 -> 38
# 11 -> 14
# 12 -> 5

# 7 Seg pins 11, 7, 4, 2, 1, 10, 5, 3 -> A, B, C, D, E, F, G, DP
segments = [14, 44, 18, 10, 4, 38, 17, 0]

# 7 Seg pins 12, 9, 8, 6 -> DIG 1, DIG 2, DIG 3, DIG 4
digits = [5, 33, 43, 7]

seg7dig4 = Seg7Dig4Display(segments, digits)

app = Microdot()


async def main():
    global app

    connect_to_wifi()

    server = asyncio.create_task(app.start_server(port=80, debug=True))

    # TODO: launch tasks to do background work
    asyncio.create_task(test())

    await server

    # Synchronous model
    # app.run(port=80, debug=True)


def connect_to_wifi():
    global wlan

    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(True)

    # Reset connection status
    if wlan.isconnected():
        wlan.disconnect()

    wlan.ifconfig(('192.168.1.200', '255.255.255.0', '192.168.1.1', '8.8.8.8'))
    wlan.connect('TP-Link_4CD8', 'TO_BE_FILLED')

    while not wlan.isconnected():
        utime.sleep(0.1)

    if wlan.status() == network.STAT_GOT_IP:
        print("Successfully connected to Wi-Fi network!")
        print("IP Address: {}".format(wlan.ifconfig()[0]))


@app.get('/')
async def index(request):
    return 'Hello world!'


@app.get('/temperature')
async def temperature(request):
    return f'{sensor.temperature}', 200, {'Content-Type': 'application/json'}


@app.get('/humidity')
async def temperature(request):
    return f'{sensor.relative_humidity}', 200, {'Content-Type': 'application/json'}


async def test():
    # seg7dig4.write_integer(321)

    while True:
        temp = sensor.temperature

        print(f'{temp}')

        await asyncio.sleep(1)


asyncio.run(main())
