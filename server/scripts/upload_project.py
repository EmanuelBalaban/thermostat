import os, subprocess

from serial_ports import select_serial_port


def main():
    serial_port = select_serial_port()

    if serial_port is None:
        return

    files = [file for file in os.listdir() if os.path.isfile(file) and file.endswith('.py')]

    print(f'Uploading {files} to {serial_port}...')

    # TODO: compile project files to .MPY

    for file in files:
        subprocess.run([
            'ampy',
            '-p',
            f'{serial_port}',
            'put',
            f'{file}'
        ])


if __name__ == "__main__":
    main()
