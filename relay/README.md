# Thermostat Relay (Client)

This is the client microcontroller. It connects to the main http server and reacts based on the state.

It also contains a gas sensor and can trigger updates to the main controller for stopping the heating system.

## Upload the project to an ESP32 microcontroller

```shell
ampy -p COM9 put boot.py
ampy -p COM9 put main.py
ampy -p COM9 put app.py
ampy -p COM9 put config.py
```