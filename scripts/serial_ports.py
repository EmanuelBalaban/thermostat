import sys
import glob
import serial


def list_serial_ports() -> list[str]:
    """ List all serial port names available on the system """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % i for i in range(1, 257)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform: {}'.format(sys.platform))

    available_ports = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            available_ports.append(port)
        except (OSError, serial.SerialException):
            pass
    return available_ports


def select_serial_port() -> str | None:
    """ Select a serial port using the command line interface """

    serial_ports = list_serial_ports()

    if len(serial_ports) == 0:
        print('No serial ports found')
        return None

    print('Available serial ports:')
    for idx, port in enumerate(serial_ports, start=1):
        print(f'{idx}: {port}')

    while True:
        try:
            choice = int(input('Select a port by entering the corresponding number (or 0 to exit): '))
            if choice == 0:
                print('Exiting...')
                return None
            if 1 <= choice <= len(serial_ports):
                return serial_ports[choice - 1]
            else:
                print('Invalid choice. Please select a valid port number.')
        except ValueError:
            print('Invalid input. Please enter a number.')
