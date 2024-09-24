import time
import robomaster
import find_wifi
from robomaster import conn, robot
from MyQR import myqr
from PIL import Image



QRCODE_NAME = "qrcode.png"


def check_connection():
    ep_robot = robot.Robot()
    
    try: 
        if not ep_robot.initialize(conn_type="sta"):
            print("No robot")
            return False
    except BaseException as err:
        print("Error:->", err)
        return False

    print("robot connected")
    SN = ep_robot.get_sn()
    print("Robot SN:", SN)
    return ep_robot


def create_connection(ssid, password):
    print("connection helper")
    if not check_connection():
        helper = conn.ConnectionHelper()
        # info = helper.build_qrcode_string(ssid="AVENGER-MANSE_optout", password="catdogpigcow")
        # info = helper.build_qrcode_string(ssid="Anh-iPhone", password="dromana1234")
        # info = helper.build_qrcode_string(ssid="DJITest", password="admin1234")
        # info = helper.build_qrcode_string(ssid="CyFi", password="SecurityA40")
        print("password: ", password)
        info = helper.build_qrcode_string(ssid=ssid, password=password)
        myqr.run(words=info)
        time.sleep(1)
        img = Image.open(QRCODE_NAME)
        img.show()

        if helper.wait_for_connection():
            print("Connected!")
            ep_robot = robot.Robot()
            return ep_robot
        else:
            print("Connect failed!")
            return False
    else:
        print("Robot already connected")
        return ep_robot


def create_ap_connection():
    print("AP connection")
   
    result = check_connection()
    print("AP result ", result)
    if not result:
        print("Creating AP connection")
        ep_robot = robot.Robot()
        ep_robot.initialize(conn_type="ap")
        return ep_robot
    else:
        print("robot already connected")
        return result



if __name__ == '__main__':
    if not check_connection():
        create_connection()
    else:
        print("Robot already connected")
