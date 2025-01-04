# Thermostat Server Module

This is the server module. It acts as the main controller for heating logic and a webserver 2 in 1.

## What to upload?

Use the following commands:

```shell
ampy -p COM5 put icons
ampy -p COM5 put web
ampy -p COM5 put app.py
ampy -p COM5 put boot.py
ampy -p COM5 put config.py
ampy -p COM5 put main.py
```

Compile lib using `compile_lib.py` script.

Upload lib using `upload_lib.py` script.

You can also compile the other .py files for efficiency.

Upload the certs, after generating them (follow the doc).