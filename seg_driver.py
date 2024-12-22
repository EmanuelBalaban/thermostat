import machine


class Seg7Dig4Display:
    # Define integer digits
    # Number to 7 Seg Code (ABCDEFG, DP)
    num = {' ': [0, 0, 0, 0, 0, 0, 0, 0],
           '0': [1, 1, 1, 1, 1, 1, 0, 0],
           '1': [0, 1, 1, 0, 0, 0, 0, 0],
           '2': [1, 1, 0, 1, 1, 0, 1, 0],
           '3': [1, 1, 1, 1, 0, 0, 1, 0],
           '4': [0, 1, 1, 0, 0, 1, 1, 0],
           '5': [1, 0, 1, 1, 0, 1, 1, 0],
           '6': [1, 0, 1, 1, 1, 1, 1, 0],
           '7': [1, 1, 1, 0, 0, 0, 0, 0],
           '8': [1, 1, 1, 1, 1, 1, 1, 0],
           '9': [1, 1, 1, 1, 0, 1, 1, 0]}

    def __init__(self, segments: list[int], sel: list[int]):
        """
        Initializes a 4 digit 7 segment display by setting the pins to OUT and resetting the values.
        """

        self.segment_pins = [machine.Pin(gpio, machine.Pin.OUT) for gpio in segments]
        self.sel_pins = [machine.Pin(gpio, machine.Pin.OUT) for gpio in sel]

    def reset(self):
        # Reset segment pins
        for pin in self.segment_pins:
            pin.value(1)

        # Reset sel pins
        for pin in self.sel_pins:
            pin.value(0)

    def select_display(self, index: int):
        """
        Select a given digit by using the selector pins.
        """

        # Reset pins
        for pin in self.sel_pins:
            pin.value(0)

        self.sel_pins[index].value(1)

    def write_integer(self, value: int):
        if value < 0:
            raise ValueError("Value must be non-negative")

        digits = [int(x) for x in str(value)]

        if len(digits) > len(self.sel_pins):
            raise ValueError("Cannot output a value bigger then the number of 7 segments")

        for i in range(len(digits)):
            self.select_display(0)

            bits = self.num[str(digits[i])]

            for j in range(len(bits)):
                self.segment_pins[i].value(1 - bits[j])
