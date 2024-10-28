from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QVBoxLayout, QLabel, QWidget, QLineEdit
from PySide6.QtCore import QTimer, QThread, Qt, Slot, QThreadPool, QRunnable, Signal, QObject
from time import sleep
import cv2
import robot_connect
import get_battery_status
import movement
import arm
import find_wifi
from robomaster import camera
import threading

import keyboard

import sys

class PersonInfo:
    def __init__(self, x, y, w, h):
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    @property
    def pt1(self):
        return int((self._x - self._w / 2) * 1280), int((self._y - self._h / 2) * 720)

    @property
    def pt2(self):
        return int((self._x + self._w / 2) * 1280), int((self._y + self._h / 2) * 720)

    @property
    def center(self):
        return int(self._x * 1280), int(self._y * 720)


class GestureInfo:

    def __init__(self, x, y, w, h, info):
        self._x = x
        self._y = y
        self._w = w
        self._h = h
        self._info = info

    @property
    def pt1(self):
        return int((self._x - self._w / 2) * 1280), int((self._y - self._h / 2) * 720)

    @property
    def pt2(self):
        return int((self._x + self._w / 2) * 1280), int((self._y + self._h / 2) * 720)

    @property
    def center(self):
        return int(self._x * 1280), int(self._y * 720)

    @property
    def text(self):
        return str(self._info)


class ConnectionSignals(QObject):
    result = Signal(object)
    error = Signal(tuple)
    finished = Signal()


class BatterySignals(QObject):
    result = Signal(int)
    error = Signal(tuple)
    finished = Signal()


class ConnectionThread(QRunnable):
    def __init__(self, fn, ssid, password): 
        super().__init__()

        self.fn = fn
        self.ssid = ssid
        self.password = password
        self.signal = ConnectionSignals()

    @Slot()
    def run(self):
        try:
            if self.ssid == '' and self.password == '':
                result = self.fn()
            else:
                result = self.fn(self.ssid, self.password)

        except Exception as e:
            print("Exception (CT) ->> ", e)
            self.signal.error.emit(e)
        else:
            print("Result!")
            self.signal.result.emit(result)
        finally:
            self.signal.finished.emit()


class FindWifiSignals(QObject):
    result = Signal(str)
    error = Signal(tuple)
    finished = Signal()


class FindWifiThread(QRunnable):
    def __init__(self, fn):
        super().__init__()

        self.fn = fn
        self.signal = FindWifiSignals()

    @Slot()
    def run(self):
        try:
            result = self.fn()
        except Exception as e:
            print("Exception (FWT) ->> ", e)
            self.signal.error.emit(e)
        else:
            print("Result!")
            self.signal.result.emit(result)
        finally:
            self.signal.finished.emit()


class BatteryThread(QRunnable):
    def __init__(self, fn, ep_robot):
        super().__init__()

        self.fn = fn
        self.ep_robot = ep_robot
        self.signal = BatterySignals()

    @Slot()
    def run(self):
        try:
            result = self.fn(self.ep_robot)
        except Exception as e:
            print("Exception (BT) ->> ", e)
            self.signal.error.emit(e)
        else:
            print("Result!")
            self.signal.result.emit(result)
        finally:
            self.signal.finished.emit()


class MovementThread(QRunnable):
    def __init__(self, fn, chassis):
        super().__init__()

        self.fn = fn
        self.chassis = chassis
        self.signal = MovementSignals()

    @Slot()
    def run(self):
        try:
            self.fn(self.chassis)
        except Exception as e:
            print("Exception (MT) ->> ", e)
            self.signal.error.emit(e)
        finally:
            self.signal.finished.emit()


class MovementSignals(QObject):
    error = Signal(tuple)
    finished = Signal()


class ArmThread(QRunnable):
    def __init__(self, fn, arm):
        super().__init__()

        self.fn = fn
        self.arm = arm
        self.signal = ArmSignals()

    @Slot()
    def run(self):
        try:
            self.fn(self.arm)
        except Exception as e:
            print("Exception (AT) ->> ", e)
            self.signal.error.emit(e)
        finally:
            self.signal.finished.emit()


class ArmSignals(QObject):
    error = Signal(tuple)
    finished = Signal()


class GripperThread(QRunnable):
    def __init__(self, fn, gripper):
        super().__init__()

        self.fn = fn
        self.gripper = gripper
        self.signal = GripperSignals()

    @Slot()
    def run(self):
        try:
            self.fn(self.gripper)
        except Exception as e:
            print("Exception (GT) ->> ", e)
            self.signal.error.emit(e)
        finally:
            self.signal.finished.emit()


class GripperSignals(QObject):
    error = Signal(tuple)
    finished = Signal()


class CameraThread(QRunnable):
    def __init__(self, fn):
        super().__init__()

        self.fn = fn
        self.signal = CameraSignals()

    @Slot()
    def run(self):
        try:
            self.fn()
        except Exception as e:
            print("Exception (CT) ->> ", e)
            self.signal.error.emit(e)
        finally:
            self.signal.finished.emit()


class CameraSignals(QObject):
    error = Signal(tuple)
    finished = Signal()


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.robot = object
        self.move_speed = 0.5
        self.rotate_speed = 30
        self.movement_timeout = 0.2
        self.wheel_rpm = 100

        self.persons = []

        self.battery_lbl = QLabel("Battery: ")
        self.battery_timer = QTimer()
        self.battery_timer.timeout.connect(self.get_battery_info)

        self.count = 0
        self.timer = QTimer()
        
        self.label = QLabel("Checking robot connection")
        self.label2 = QLabel(str(self.count))
        self.ssid_label = QLabel("SSID")
        self.password_entry = QLineEdit()
        self.button = QPushButton("Connect to robot")
        self.ap_connect_button = QPushButton("Connect to AP")
        self.disconnect_button = QPushButton("Disconnect")
        self.window = QMainWindow()
        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget()

        self.ssid = ''
        self.password = ''

        self.threadpool = QThreadPool()

        self.init_ui()


    def init_ui(self):
        self.button.setEnabled(False)

        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)


        self.button.clicked.connect(self.connect_to_robot)
        self.disconnect_button.clicked.connect(self.disconnect_robot)
        self.ap_connect_button.clicked.connect(self.create_ap_connection_thread)

        self.password_entry.setEchoMode(QLineEdit.Password)
        
        # self.setStyleSheet("background-color: #333; color: white;")
        self.windowTitle = "My App"
        self.setCentralWidget(self.main_widget)

        self.main_widget.setLayout(self.main_layout)

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.ssid_label)
        self.main_layout.addWidget(self.password_entry)
        self.main_layout.addWidget(self.button)
        self.main_layout.addWidget(self.label2)
        self.main_layout.addWidget(self.battery_lbl)
        # self.main_layout.addWidget(self.disconnect_button)
        self.main_layout.addWidget(self.ap_connect_button)

        self.create_connection_thread()


    def disconnect_robot(self):
        print("Disconnecting robot")
        self.robot.close()
        self.label.setText("Robot disconnected")
        self.button.setEnabled(False)

    def connection(self):
        result = robot_connect.check_connection()
        if not result:
            print("No robot connected")
            self.label.setText("No robot connected")
            return
        
        print("Robot already connected")
        self.label.setText("Robot already connected")
        self.button.setEnabled(False)
        self.robot = result
        # self.battery_timer.start(5000)


    def update_info(self):
        self.count += 1
        self.label2.setText(str(self.count))


    def connect_to_robot(self):
        print("Connecting to robot")
        self.label.setText("Connecting to robot")
        self.button.setEnabled(False)
        self.password = self.password_entry.text()
        connection_thread = ConnectionThread(robot_connect.create_connection, self.ssid, self.password)          
        connection_thread.signal.result.connect(self.print_output)
        # connection_thread.signal.finished.connect(self.thread_complete)
        self.threadpool.start(connection_thread)


    def create_connection_thread(self):
        self.button.setEnabled(False)
        connection_thread = ConnectionThread(robot_connect.check_connection, '', '')          
        connection_thread.signal.result.connect(self.print_output)
        # connection_thread.signal.finished.connect(self.thread_complete)
        self.threadpool.start(connection_thread)


    def create_ap_connection_thread(self):
        self.button.setEnabled(False)
        connection_thread = ConnectionThread(robot_connect.create_ap_connection)          
        connection_thread.signal.result.connect(self.print_output)
        # connection_thread.signal.finished.connect(self.thread_complete)
        self.threadpool.start(connection_thread)


    def create_battery_thread(self):
        print("Creating battery thread")
        # battery_thread = BatteryThread(get_battery_status.init_battery_status, self.robot)
        # battery_thread.signal.finished.connect(self.thread_complete)
        # self.threadpool.start(battery_thread)
        # get_battery_status.init_battery_status(self.robot)
        self.battery_timer.start(5000)


    def create_movement_thread(self):
        print("Creating movement thread")
        # ep_chassis = self.robot.chassis
        movement_thread = MovementThread(movement.movement, self.robot)
        # movement_thread.signal.finished.connect(self.thread_complete)
        self.threadpool.start(movement_thread)

    
    def create_arm_thread(self, dir):      
        print("Creating arm thread")
        if dir == "init":
            arm_thread = ArmThread(arm.move_arm, self.robot.robotic_arm)
        elif dir == "up":
            arm_thread = ArmThread(arm.move_arm_up, self.robot.robotic_arm)
        elif dir == "down":
            arm_thread = ArmThread(arm.move_arm_down, self.robot.robotic_arm)
        elif dir == "forward":
            arm_thread = ArmThread(arm.move_arm_forward, self.robot.robotic_arm)
        elif dir == "backward":
            arm_thread = ArmThread(arm.move_arm_backward, self.robot.robotic_arm)
            
        
        arm_thread.signal.finished.connect(self.arm_thread_complete)
        self.threadpool.start(arm_thread)
        # t1 = threading.Thread(target=self.move_arm,  args=(self.robot.robotic_arm,))
        # t1.start()
        # os.system("python arm.py")


    def create_camera_thread(self):
        print("Creating camera thread")
        camera_thread = CameraThread(self.camera_feed)
        camera_thread.signal.finished.connect(self.thread_complete)
        self.threadpool.start(camera_thread)


    def create_find_wifi_thread(self):
        print("Creating find wifi thread")
        find_wifi_thread = FindWifiThread(find_wifi.find_current_wifi)
        find_wifi_thread.signal.result.connect(self.connect_to_network)
        find_wifi_thread.signal.finished.connect(self.thread_complete)
        self.threadpool.start(find_wifi_thread)

    def on_detect_person(self, person_info):
        # number = len(person_info)
        # self.persons.clear()

        # for i in range(0, number):
        #     x, y, w, h = person_info[i]
        #     self.persons.append(PersonInfo(x, y, w, h))
        #     print("person: x:{0}, y:{1}, w:{2}, h:{3}".format(x, y, w, h))

        value_lock = threading.Lock()

        number = len(person_info)
        value_lock.acquire()
        self.persons.clear()
        for i in range(0, number):
            x, y, w, h, info = person_info[i]
            self.persons.append(GestureInfo(x, y, w, h, info))
            print("gesture: info:{0}, x:{1}, y:{2}, w:{3}, h:{4}".format(info, x, y, w, h))
        value_lock.release()


    def camera_feed(self):
        # self.robot.camera.start_video_stream(display=True, resolution=camera.STREAM_360P)
        self.robot.camera.start_video_stream(False)
        ep_vision = self.robot.vision
        result = self.robot.vision.sub_detect_info(name="gesture", callback=self.on_detect_person)
        value_lock = threading.Lock()
        for i in range(0, 1000):
            img = self.robot.camera.read_cv2_image(strategy="newest", timeout=1.5)
            # for j in range(0, len(self.persons)):
            #     cv2.rectangle(img, self.persons[j].pt1, self.persons[j].pt2, (255, 255, 255))
            # cv2.imshow("Persons", img)
            for j in range(0, len(self.persons)):
                value_lock.acquire()
                cv2.rectangle(img, self.persons[j].pt1, self.persons[j].pt2, (255, 255, 255))
                cv2.putText(img, self.persons[j].text, self.persons[j].center, cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
                value_lock.release()
        
            cv2.imshow("Gestures", img)
            cv2.waitKey(1)
        
        cv2.destroyAllWindows()
        result = ep_vision.unsub_detect_info(name="gesture")
        cv2.destroyAllWindows()


    def thread_complete(self):
        print("THREAD COMPLETE!")

    def arm_thread_complete(self):
        print("ARM THREAD COMPLETE!")    


    def print_output(self, s):
        print("Output: ", s)
        if s:
            self.label.setText("Robot connected")
            self.button.setEnabled(False)
            self.robot = s
            self.create_camera_thread()
            get_battery_status.init_battery_status(self.robot)
            self.battery_timer.start(2000)
            # self.create_battery_thread()
            self.create_movement_thread()
            # arm.move_arm_up(self.robot.robotic_arm)
            # self.create_arm_thread("init")
            # self.ssid_label.setText(find_wifi.find_current_wifi())

        else:
            self.label.setText("No robot connected")
            # self.create_find_wifi_thread()
            ssid = find_wifi.find_current_wifi()
            if ssid == '':
                self.ssid_label.setText("Must be connected to a wireless network")
            else:
                print("Network found: ", ssid)
                self.ssid_label.setText(ssid)
                self.ssid = ssid
                self.button.setEnabled(True)
            

    def connect_to_network(self, ssid):
        if ssid != '':
            print("Network found: ", ssid)
            
            self.button.setEnabled(True)

    def get_battery_info(self):
        battery_data = get_battery_status.get_battery_data()
        battery_data = f"{battery_data}%"
        print("Battery: ", battery_data)
        self.battery_lbl.setText(battery_data)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    app.exec()


    # def keyPressEvent(self, event):
    #     key = event.key()
    #     if key == Qt.Key_W:
    #         print("W pressed")
    #         arm.move_arm_up(self.robot.robotic_arm)
    #     elif key == Qt.Key_R:
    #         print("R pressed")
    #         arm.move_arm_down(self.robot.robotic_arm)
    #     elif key == Qt.Key_Q:
    #         print("Q pressed")
    #         arm.move_arm_forward(self.robot.robotic_arm)
    #     elif key == Qt.Key_A:
    #         print("A pressed")
    #         self.robot.robotic_arm.move(x=-10, y=0).wait_for_completed(timeout=1)
    #     elif key == Qt.Key_F:
    #         print("F pressed")
    #         self.robot.gripper.open(power=50)
    #     elif key == Qt.Key_S:
    #         print("S pressed")
    #         self.robot.gripper.close(power=50)
    #     elif key == Qt.Key.Key_U:
    #         print("U pressed")
    #         self.robot.chassis.drive_speed(x=self.move_speed, y=0, z=0, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_E:
    #         print("E pressed")
    #         self.robot.chassis.drive_speed(x=-self.move_speed, y=0, z=0, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_N:
    #         print("N pressed")
    #         self.robot.chassis.drive_speed(x=0, y=-self.move_speed, z=0, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_I:
    #         print("I pressed")
    #         self.robot.chassis.drive_speed(x=0, y=self.move_speed, z=0, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_L:
    #         print("L pressed")
    #         self.robot.chassis.drive_speed(x=0, y=0, z=-self.rotate_speed, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_Y:
    #         print("Y pressed")
    #         self.robot.chassis.drive_speed(x=0, y=0, z=self.rotate_speed, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_G:
    #         if not self.robot.chassis.drive_wheels(w1=self.wheel_rpm, w2=self.wheel_rpm, w3=self.wheel_rpm, w4=self.wheel_rpm, timeout=self.movement_timeout):
    #             print("Wheels failed to move")
    #     elif key == Qt.Key.Key_D:
    #         self.robot.chassis.drive_wheels(w1=-self.wheel_rpm, w2=-self.wheel_rpm, w3=-self.wheel_rpm, w4=-self.wheel_rpm, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_T:
    #         self.robot.chassis.drive_wheels(w1=self.wheel_rpm, w2=-self.wheel_rpm, w3=self.wheel_rpm, w4=-self.wheel_rpm, timeout=0)
    #     elif key == Qt.Key.Key_H:
    #         self.robot.chassis.drive_wheels(w1=-self.wheel_rpm, w2=self.wheel_rpm, w3=-self.wheel_rpm, w4=self.wheel_rpm, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_P:
    #         self.robot.chassis.drive_wheels(w1=self.wheel_rpm, w2=-self.wheel_rpm, w3=-self.wheel_rpm, w4=self.wheel_rpm, timeout=self.movement_timeout)
    #     elif key == Qt.Key.Key_J:
    #         self.robot.chassis.drive_wheels(w1=-self.wheel_rpm, w2=self.wheel_rpm, w3=self.wheel_rpm, w4=-self.wheel_rpm, timeout=self.movement_timeout)
    #     else:
    #         print("Key not recognized")