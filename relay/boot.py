import gc


def connect_to_wifi():
    import network, utime
    import config

    print('Connecting to WiFi...')

    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(config.ENABLE_WIFI)

    if not config.ENABLE_WIFI:
        return

    # Reset connection status
    if wlan.isconnected():
        wlan.disconnect()

    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWD)

    while not wlan.isconnected():
        utime.sleep(0.1)

    if wlan.status() == network.STAT_GOT_IP:
        print("Successfully connected to Wi-Fi network!")
        print("IP Address: {}".format(wlan.ifconfig()[0]))


connect_to_wifi()

gc.collect()

import ntptime

print('Updating time from NTP server...')
ntptime.settime()

gc.collect()

# Power neopixel
import machine

neo_pixel_power_pin = 2
led_pwr = machine.Pin(neo_pixel_power_pin, machine.Pin.OUT)
led_pwr.value(0)
