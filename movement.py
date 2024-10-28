import keyboard
import arm
from robomaster import robot
import xinput
# from controller import XInput
import math
from xinput import XInput
from time import sleep

distance = [0, 0, 0, 0]
gripper_status = ''

def sub_tof_data_handler(sub_info):
    global distance
    distance = sub_info
    # print("tof1:{0}  tof2:{1}  tof3:{2}  tof4:{3}".format(distance[0], distance[1], distance[2], distance[3]))


def sub_gripper_data_handler(sub_info):
    global gripper_status
    status = sub_info
    gripper_status = status
    # print("gripper status:{0}.".format(status))


def get_gamepad_input(x, output, max_speed, ep_robot):
    for button in x.BUTTONS.keys():
        if x.is_button_press(button):
            print("Button Press: ", x.is_button_press(button))
            output[button] = x.is_button_press(button)
            if button == 'A':
                print("Hello")
                ep_robot.play_audio(filename="Hello.wav").wait_for_completed(timeout=0.5)
                # ep_robot.
            elif button == 'B':
                ep_robot.play_audio(filename="Fart.wav").wait_for_completed(timeout=0.5)

    for thumb in x.THUMBS.keys():
        if x.is_thumb_move(thumb):
            output[thumb] = x.get_thumb_value(thumb)
            print("Thumb Move: ", output[thumb], thumb)

    for inp in output:
        speed = max_speed * output[inp] / 32768

        if inp == 'LEFT_THUMB_Y':
            print("forward")
            if gripper_status == 'opened':
                print("gripper opened")
                if distance[0] <= 100:
                        speed = speed * 0.05
            ep_robot.chassis.drive_speed(x=speed, y=0, z=0, timeout=0.5)
        elif inp == "LEFT_THUMB_-Y":
            print("backward")
            ep_robot.chassis.drive_speed(x=speed, y=0, z=0, timeout=0.5)
        elif inp == "LEFT_THUMB_X":
            print("right")
            ep_robot.chassis.drive_speed(x=0, y=speed, z=0, timeout=0.5)
        elif inp == "LEFT_THUMB_-X":
            print("left")
            ep_robot.chassis.drive_speed(x=0, y=speed, z=0, timeout=0.5)
        elif inp == "RIGHT_THUMB_X":
            print("rotate right")
            ep_robot.chassis.drive_speed(x=0, y=0, z=90, timeout=0.5)
        elif inp == "RIGHT_THUMB_-X":
            print("rotate left")
            ep_robot.chassis.drive_speed(x=0, y=0, z=-90, timeout=0.5)

        elif inp == "DPAD_UP":
            print("arm up")
            ep_robot.robotic_arm.move(x=0, y=30).wait_for_completed(timeout=0.3)
        elif inp == "DPAD_DOWN":
            print("arm down")
            ep_robot.robotic_arm.move(x=0, y=-30).wait_for_completed(timeout=0.3)
        elif inp == "DPAD_RIGHT":
            print("arm forward")
            ep_robot.robotic_arm.move(x=30, y=0).wait_for_completed(timeout=0.3)
        elif inp == "DPAD_LEFT":
            print("arm backward")
            ep_robot.robotic_arm.move(x=-30, y=0).wait_for_completed(timeout=0.3)

        elif inp == "LEFT_SHOULDER":
            print("gripper open")
            ep_robot.gripper.open(power=50)
        elif inp == "RIGHT_SHOULDER":
            print("gripper close")
            ep_robot.gripper.close(power=50)


    sleep(0.1)
        

def movement(ep_robot):
        max_speed = 1
        speed = 10

        ep_chassis = ep_robot.chassis
        ep_arm = ep_robot.robotic_arm
        ep_gripper = ep_robot.gripper

        tof = ep_robot.sensor
        tof.sub_distance(freq=5, callback=sub_tof_data_handler)

        ep_gripper.sub_status(freq=5, callback=sub_gripper_data_handler)

        x = XInput('default.ini')
        
        try:
            while True:
                output = {}

                if not x.get_state() and output:
                    continue

                get_gamepad_input(x, output, max_speed, ep_robot)

                # if keyboard.is_pressed('up'):
                #     print("forward")
                #     # ep_chassis.move(x=x_val, y=0, z=0, xy_speed=speed).wait_for_completed()``
                #     ep_chassis.drive_speed(x=max_speed, y=0, z=0, timeout=0.5)
                # elif keyboard.is_pressed('down'):
                #     print("backward")
                #     ep_chassis.drive_speed(x=-max_speed, y=0, z=0, timeout=0.5)
                # elif keyboard.is_pressed('left'):
                #     print("left")
                #     ep_chassis.drive_speed(x=0, y=-max_speed, z=0, timeout=0.5)
                # elif keyboard.is_pressed('right'):
                #     print("right")
                #     ep_chassis.drive_speed(x=0, y=max_speed, z=0, timeout=0.5)
                # elif keyboard.is_pressed('z'):
                #     print("rotate left")
                #     ep_chassis.drive_speed(x=0, y=0, z=-90, timeout=0.5)
                # elif keyboard.is_pressed('x'):
                #     print("rotate right")
                #     ep_chassis.drive_speed(x=0, y=0, z=90, timeout=0.5)
                # elif keyboard.is_pressed('q'):
                #     print("arm up")
                #     ep_arm.move(x=0, y=30).wait_for_completed(timeout=0.5)
                # elif keyboard.is_pressed('a'):
                #     print("arm down")
                #     ep_arm.move(x=0, y=-30).wait_for_completed(timeout=0.5)
                # elif keyboard.is_pressed('w'):
                #     ep_arm.move(x=30, y=0).wait_for_completed(timeout=0.5)
                # elif keyboard.is_pressed('r'):
                #     ep_arm.move(x=-30, y=0).wait_for_completed(timeout=0.5)
                # elif keyboard.is_pressed('f'):
                #     ep_gripper.open(power=50)
                # elif keyboard.is_pressed('s'):
                #     ep_gripper.close(power=50)
                # else:
                #     ep_chassis.drive_speed(x=0, y=0, z=0, timeout=0)

        except Exception as e:
            print("Movement Exception: -> ", e)

if __name__ == '__main__':
    ep_robot = robot.Robot()
    ep_robot.initialize(conn_type="sta")
    
    movement(ep_robot)