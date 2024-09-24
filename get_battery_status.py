import time
import robomaster
from robomaster import robot

battery_data = 0

def sub_battery_handler(battery_info, ep_robot):
    global battery_data
    percent = battery_info
    # print("Battery: {0}%.".format(percent))
    battery_data = percent


def init_battery_status(ep_robot):
    global battery_data
    ep_battery = ep_robot.battery
    ep_battery.sub_battery_info(50, sub_battery_handler, ep_robot)

def get_battery_data():
    global battery_data
    return battery_data