import keyboard
from robomaster import robot

import threading

move_speed = 30

def move_arm(arm):
    # print(arm)

    # print("init arm movement")
    # arm.move(x=20, y=0).wait_for_completed(timeout=2)
    # print("Arm moved")


    # if arm.move(x=-10, y=10).wait_for_completed(timeout=2):
    #     print("Arm moved")
    # else:
    #     print("Arm move failed")

    # if arm.move(x=-10, y=0).wait_for_completed(timeout=2):
    #     print("Arm moved")
    # else:
    #     print("Arm move failed")

    # return
    print("Arm movement init")

    # if arm.move(x=0, y=0).wait_for_completed(timeout=2):
    if arm.move(x=10.0, y=0.0).wait_for_completed(timeout=2):
        print("Arm init position")
    else:
        print("Arm init failed")
        
    while True:
        if keyboard.is_pressed('q'):
            print("arm up")
            if arm.move(0, 10).wait_for_completed(timeout=1):
                print("Arm moved")
            else:
                print("Arm move failed")
        elif keyboard.is_pressed('a'): 
            print("arm down")
            arm.move(x=0, y=-10).wait_for_completed(timeout=0.5)
        elif keyboard.is_pressed('w'):
            arm.move(x=10, y=0).wait_for_completed(timeout=0.5)
        elif keyboard.is_pressed('r'):
            arm.move(x=-10, y=0).wait_for_completed(timeout=0.5)
        elif keyboard.is_pressed('q'):
            arm.move(x=0, y=10).wait_for_completed(timeout=0.5)
        elif keyboard.is_pressed('a'):
            arm.move(x=0, y=-10).wait_for_completed(timeout=0.5)


        

    print("Arm movement completed")
    return True


def move_arm_up(arm):
    print("move arm up")

    if arm.move(x=0, y=move_speed).wait_for_completed(timeout=1):
        print("Arm moved")
        return True
    else:
        print("Arm move failed")
        return False


def move_arm_down(arm):
    print("move arm down")

    if arm.move(x=0, y=-move_speed).wait_for_completed(timeout=1):
        print("Arm moved")
    else:
        print("Arm move failed")


def move_arm_forward(arm):
    print("move arm forward")

    if arm.move(x=move_speed, y=0).wait_for_completed(timeout=1):
        print("Arm moved")
    else:
        print("Arm move failed")


def move_arm_backward(arm):
    print("move arm backward")

    if arm.move(x=-move_speed, y=0).wait_for_completed(timeout=1):
        print("Arm moved")
    else:
        print("Arm move failed")


def move_arm_dir(arm, dir):
    if dir == "up":
        print("arm up")
        arm.move(x=0, y=10).wait_for_completed(timeout=1)
    elif dir == "down": 
        print("arm down")
        arm.move(x=0, y=-10).wait_for_completed(timeout=1)
    elif dir == "forward":
        print("arm forward")
        arm.move(x=10, y=0).wait_for_completed(timeout=1)
    elif dir == "backward":
        print("arm backward")
        arm.move(x=-10, y=0).wait_for_completed(timeout=1)

    return




if __name__ == '__main__':
    ep_robot = robot.Robot()
    ep_robot.initialize(conn_type="sta")
    arm = ep_robot.robotic_arm

    t1 = threading.Thread(target=move_arm,  args=(arm,))
    t1.start()
    # move_arm(arm)