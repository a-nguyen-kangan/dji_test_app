from configparser import ConfigParser
import ctypes
import controller
import time
import os



class XInput:
    def __init__(self, config_file, gamepad_number=0):
        self.gamepad_number = gamepad_number
        self.state = controller.XInputState()
        self.gamepad = self.state.Gamepad
        config = ConfigParser()
        config.read(config_file)
        self.config = config['gamepad']

    API = ctypes.windll.xinput1_4
    TRIGGERS = {
        'LEFT_TRIGGER': 'bLeftTrigger',
        'RIGHT_TRIGGER': 'bRightTrigger',
    }
    THUMBS = {
        'LEFT_THUMB_X': 'sThumbLX',
        'LEFT_THUMB_-X': 'sThumbLX',
        'LEFT_THUMB_Y': 'sThumbLY',
        'LEFT_THUMB_-Y': 'sThumbLY',
        'RIGHT_THUMB_X': 'sThumbRX',
        'RIGHT_THUMB_-X': 'sThumbRX',
        'RIGHT_THUMB_Y': 'sThumbRY',
        'RIGHT_THUMB_-Y': 'sThumbRY',
    }
    AXES = {
        **TRIGGERS,
        **THUMBS
    }
    BUTTONS = {
        'DPAD_UP': 0x0001,
        'DPAD_DOWN': 0x0002,
        'DPAD_LEFT': 0x0004,
        'DPAD_RIGHT': 0x0008,
        'START': 0x0010,
        'BACK': 0x0020,
        'LEFT_THUMB': 0x0040,
        'RIGHT_THUMB': 0x0080,
        'LEFT_SHOULDER': 0x0100,
        'RIGHT_SHOULDER': 0x0200,
        'A': 0x1000,
        'B': 0x2000,
        'X': 0x4000,
        'Y': 0x8000
    }
    TRIGGER_MAGNITUDE = 256
    THUMB_MAGNITUDE = 32768
    MOTOR_MAGNITUDE = 65535
    ERROR_SUCCESS = 0


    def get_state(self):
        previous_state = self.state.dwPacketNumber
        error_code = self.API.XInputGetState(
            ctypes.wintypes.WORD(self.gamepad_number), 
            ctypes.pointer(self.state)
        )
        if error_code != self.ERROR_SUCCESS:
            raise Exception('Gamepad number {} is not connected'.format(self.gamepad_number))
        return previous_state != self.state.dwPacketNumber
    

    def is_button_press(self, button):
        if button not in self.BUTTONS:
            raise Exception('Invalid button. Got: "{}"'.format(button))
        return bool(self.BUTTONS[button] & self.gamepad.wButtons)
    

    def get_axis_value(self, axis):
        if axis not in self.AXES:
            raise Exception('Invalid axis, Got: {}'.format(axis))
        return getattr(self.gamepad, self.AXES[axis])
    

    def get_trigger_value(self, trigger):
        return self.get_axis_value(trigger) & 0xFF


    def get_thumb_value(self, thumb):
        return self.get_axis_value(thumb)
    

    def get_magnitude(self, axis_type):
        return getattr(self, axis_type + '_MAGNITUDE')

    def get_sensitivity(self, axis_type):
        return self.config.getfloat(axis_type + '_SENSITIVITY')

    def get_normalized_value(self, axis: str):
        if axis not in self.AXES.keys():
            raise Exception('Invalid axis. Got: "{}"'.format(axis))
        axis_type = axis.split('_')[1]
        raw_value = getattr(
            self,
            'get_{}_value'.format(axis_type.lower()))(axis)
        magnitude = self.get_magnitude(axis_type)
        sensitivity = self.get_sensitivity(axis_type)
        return (raw_value / magnitude) * sensitivity


    def get_dead_zone(self, axis_type):
        return self.config.getfloat(axis_type + '_DEAD_ZONE')

    def is_axis_change(self, axis):
        if axis not in self.AXES.keys():
            raise Exception('Invalid axis. Got: "{}"'.format(axis))
        axis_type = axis.split('_')[1]
        axis_value = self.get_normalized_value(axis) / self.get_sensitivity(axis_type)
        if '-' in axis and axis_value > 0 or '-' not in axis and axis_value < 0:
            return False
        dead_zone = self.get_dead_zone(axis_type)
        return abs(axis_value) > dead_zone
    
    def is_thumb_move(self, thumb):
        return self.is_axis_change(thumb)

    def is_trigger_press(self, trigger):
        return self.is_axis_change(trigger)
    

if __name__ == '__main__':
    x = XInput('default.ini')

    while True:
        output = {}
        
        if (not x.get_state()) and output:
            # print('\n'.join(['{} = {}'.format(key, value) for key, value in output.items()]))
            print("output (nostate): ", output)
            # time.sleep(0.2)
            # os.system('cls')
            continue

        if output:
            print("There is output")

        for thumb in x.THUMBS.keys():
            if x.is_thumb_move(thumb):
                output[thumb] = x.get_thumb_value(thumb)
        for trigger in x.TRIGGERS.keys():
            if x.is_trigger_press(trigger):
                output[trigger] = x.get_trigger_value(trigger)
        for button in x.BUTTONS.keys():
            if x.is_button_press(button):
                output[button] = x.is_button_press(button)
            # x.set_debounce_vibration(0.3, 0.3, 0.1)
        print('\n'.join(['{} = {}'.format(key, value) for key, value in output.items()]))
        print("output: ", output)
        time.sleep(2)
        # os.system('cls') 