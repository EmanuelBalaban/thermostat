import asyncio
import gc
import machine

import config
import lib.aht as aht
from lib.microdot.microdot import Microdot, abort, send_file, Response
from lib.microdot.sse import with_sse

gc.collect()

# Heating enabled and desired temperature can be set from outside
state = {
    'heating_enabled': True,
    'relay_state': False,
    'gas_detected': False,
    'temperature': 0.0,
    'desired_temperature': 24.0,
}
state_updates = asyncio.Event()

app = Microdot()

sensor: aht.AHT20


async def main():
    global sensor

    # Initialize temp sensor
    print('Initializing temperature sensor...')
    i2c = machine.SoftI2C(scl=machine.Pin(9), sda=machine.Pin(8))
    sensor = aht.AHT20(i2c)
    gc.collect()

    # Run web app
    print('Initializing web server...')
    ssl_ctx = None
    if config.USE_SSL:
        import ssl
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.load_cert_chain('certs/cert.der', 'certs/key.der')
    port = 443 if config.USE_SSL else 80
    asyncio.create_task(app.start_server(port=port, ssl=ssl_ctx, debug=True))
    gc.collect()

    try:
        while True:
            await asyncio.sleep(0)

            update_state(
                temperature=round(sensor.temperature, 2)
            )

            gc.collect()
            await asyncio.sleep(30)
    finally:
        app.shutdown()


@app.get('/')
async def index(_):
    update_state(
        temperature=round(sensor.temperature, 2)
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Thermostat Project</title>
        
        <link rel="icon" href="/favicon.ico" type="image/x-icon">
        
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
                color: #333;
                text-align: center;
            }}
            header {{
                background-color: #007bff;
                color: white;
                padding: 20px 0;
                font-size: 24px;
            }}
            .content {{
                margin: 50px auto;
                padding: 20px;
                max-width: 600px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }}
            .temperature {{
                font-size: 48px;
                color: #007bff;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <header>Thermostat Project</header>
        <div class="content">
            <p>Current temperature:</p>
            <div class="temperature">{state["temperature"]}°C</div>
        </div>
    </body>
    </html>
    """

    return Response(
        body=html_content,
        headers={'Content-Type': 'text/html'},
    )


@app.get('/state')
@with_sse
async def watch_state(_, sse):
    await sse.send(state)

    while True:
        state_clone = set(state.items())

        # TODO: check if should send heartbeat
        await state_updates.wait()
        state_updates.clear()

        diff = set(state.items()) - state_clone

        if len(diff) != 0:
            updates = dict(diff)
            await sse.send(updates)

        await asyncio.sleep(0)


@app.put('/state/heating_enabled')
async def update_heating_enabled(request):
    import struct
    update_state(
        heating_enabled=struct.unpack('?', request.body)[0],
    )


@app.put('/state/desired_temperature')
async def update_desired_temperature(request):
    update_state(
        desired_temperature=request.json['desired_temperature'],
    )


@app.patch('/state')
async def patch_state(request):
    if request.json is None:
        abort(400)

    update_state(
        heating_enabled=request.json.get('heating_enabled'),
        gas_detected=request.json.get('gas_detected'),
        desired_temperature=request.json.get('desired_temperature'),
    )


def update_state(
        heating_enabled: bool | None = None,
        gas_detected: bool | None = None,
        temperature: float | None = None,
        desired_temperature: float | None = None,
):
    old_state = set(state.items())

    if heating_enabled is not None:
        state['heating_enabled'] = heating_enabled
    if gas_detected is not None:
        state['gas_detected'] = gas_detected
    if temperature is not None:
        state['temperature'] = temperature
    if desired_temperature is not None:
        state['desired_temperature'] = desired_temperature

    state['relay_state'] = (state['heating_enabled']
                            and not state['gas_detected']
                            and state['temperature'] < state['desired_temperature'])

    if old_state != set(state.items()):
        print(state)
        state_updates.set()


@app.get('/android-chrome-192x192.png')
async def favicon(_):
    return send_file('icons/android-chrome-192x192.png')


@app.get('android-chrome-512x512.png')
async def favicon(_):
    return send_file('icons/android-chrome-512x512.png')


@app.get('apple-touch-icon.png')
async def favicon(_):
    return send_file('icons/apple-touch-icon.png')


@app.get('/favicon.ico')
async def favicon(_):
    return send_file('icons/favicon.ico')


@app.get('favicon-16x16.png')
async def favicon(_):
    return send_file('icons/favicon-16x16.png')


@app.get('favicon-32x32.png')
async def favicon(_):
    return send_file('icons/favicon-32x32.png')
