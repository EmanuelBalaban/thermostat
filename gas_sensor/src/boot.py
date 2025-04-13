import gc

import config

def connect_to_wifi():
    import network, time

    print('Connecting to WiFi')

    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(config.ENABLE_WIFI)

    if not config.ENABLE_WIFI:
        return
    
    # Reset connection status
    if wlan.isconnected():
        # wlan.disconnect()
        return
    
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWD)

    while not wlan.isconnected():
        time.sleep(0.1)

    
    if wlan.status() == network.STAT_GOT_IP:
        print("Successfully connected to Wi-Fi network!")
        print("IP Address: {}".format(wlan.ifconfig()[0]))

connect_to_wifi()

gc.collect()

import ntptime

print('Updating time from NTP server...')
ntptime.settime()

import machine

# Power neopixel
neo_pixel_power_pin = config.NEO_PIXEL_POWER_PIN
led_pwr = machine.Pin(neo_pixel_power_pin, machine.Pin.OUT)
led_pwr.value(0)
