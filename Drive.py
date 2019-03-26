#!/usr/bin/env python3

from Constants import *
from Data import *
from enum import Enum

from ev3dev2.sensor.lego import GyroSensor, UltrasonicSensor

import time, sys, syslog

data = Data()

class Drive:
    def __init__(self, drive_left, drive_right, gyro):
        self.drive_left = drive_left
        self.drive_right = drive_right
        self.gyro = gyro

        self.dist_left = 0
        self.dist_right = 0

        self.gyro_integral = 0
        self.gyro_last_error = 0

        self.ultrasonic_integral = 0
        self.ultrasonic_last_error = 0

        self.drive_left.position_p = DRIVE_LEFT_P
        self.drive_right.position_p = DRIVE_RIGHT_P

    def gyro_calibrate(self):
        print('INIT: GYRO CALIBRATION', file = sys.stderr, flush = True)
        time.sleep(1)
        self.gyro_zero()
        time.sleep(2)
        print('END: GYRO CALIBRATION', file = sys.stderr, flush = True)

    def gyro_zero(self):
        self.gyro.mode = 'GYRO-RATE'
        self.gyro.mode = 'GYRO-ANG'

    def drive_zero_position(self):
        self.drive_left.position = 0
        self.drive_right.position = 0

    def drive_speed_update(self, heading_compensate, dist_compensate = 0):
        self.drive_left.on(DRIVE_SPEED - heading_compensate, brake= True)
        self.drive_right.on(DRIVE_SPEED + heading_compensate, brake=True)
        self.drive_dist_update()
        #print(compensate)

    def drive_turn_update(self, heading_compensate):
        self.drive_left.on(-heading_compensate, brake= True)
        self.drive_right.on(heading_compensate, brake=True)

    def gyro_pid_update(self, setpoint):
        error = self.gyro.value() - setpoint
        self.gyro_integral += (error * CYCLE_TIME)

        heading_compensate = error * GYRO_P + self.gyro_integral * GYRO_I

        self.gyro_last_error = error
        print('GYRO_PID: ' + str(heading_compensate), file=sys.stderr, flush = True)

        if (50 <= heading_compensate):
            return 50
        elif (heading_compensate <= -50):
            return -50
        else:
            return heading_compensate

    # def ultrasonic_pid_update(self, setpoint):
    #     error = self.ultrasonic.value() - setpoint
    #     self.ultrasonic_integral += (error * CYCLE_TIME)
    #     derivative = (error - self.ultrasonic_last_error) / CYCLE_TIME

    #     dist_compensate = error * US_P + self.ultrasonic_integral * US_I + derivative * US_D

    #     self.ultrasonic_last_error = error
    #     print(dist_compensate, file=sys.stderr)
    #     return dist_compensate

    def drive_stop(self):
        self.drive_left.off(brake=True)
        self.drive_right.off(brake=True)

    def drive_dist_update(self):
        self.dist_left = (self.drive_left.position * EV3_RIM)
        self.dist_right = (self.drive_left.position * EV3_RIM)
        return ((self.dist_left + self.dist_right) / 2)

    # DRIVE FUNCTIONS
        
    def drive_indef(self):
        while True:
            self.drive_speed_update(self.gyro_pid_update(0))
            time.sleep(CYCLE_TIME)

    def drive_dist(self, desired_dist):
        self.drive_zero_position()
        while True:
            self.drive_speed_update(self.gyro_pid_update(0))
            print('POSITION: ' + str(self.drive_dist_update()) + ' / ' + str(desired_dist), file = sys.stderr, flush=True)
            print('ROTATIONS: ' + str(self.drive_left.position / self.drive_left.count_per_rot), file = sys.stderr, flush = True)
            if desired_dist - DIST_ACC <= int(self.drive_dist_update()) <= desired_dist + DIST_ACC:
                break
            time.sleep(CYCLE_TIME)
        self.drive_stop()

    # def drive_ultrasonic (self, safe_dist):
    #     while True:
    #         self.drive_speed_update(self.gyro_pid_update(Direction.STRAIGHT), self.ultrasonic_pid_update(safe_dist))
    #         if self.ultrasonic <= safe_dist:
    #             break
    #         time.sleep(CYCLE_TIME)
    #     self.drive_stop

    # TURNING FUNCTIONS

    def drive_slow_turn(self, direction):
        current_dir = self.gyro.value()
        setpoint = current_dir + direction        
        while True:
            self.drive_speed_update(self.gyro_pid_update(direction))
            if setpoint - TURNING_ACC <= self.gyro.value() <= setpoint + TURNING_ACC:
                break
            time.sleep(CYCLE_TIME)
        self.drive_stop()

    def drive_spot_turn(self, direction):
        current_dir = self.gyro.value()
        setpoint = current_dir + direction
        while True:
            self.drive_turn_update(self.gyro_pid_update(setpoint))
            if setpoint - TURNING_ACC <= int(self.gyro.value()) <= setpoint + TURNING_ACC:
                break
            time.sleep(CYCLE_TIME)
        self.drive_stop()

    def drive_rescue_logged_turn(self):
        while True:
            self.drive_turn_update(self.gyro_pid_update(Direction.STRAIGHT))

    # def basic_straight(self):
    #     self.drive_left.on_for_rotations(10)
    #     self.drive_right.on_for_rotations(10)

    # def basic_turn_left(self):
    #     self.drive_left.stop()
    #     self.drive_right.on_for_degrees(360)

class Direction(Enum):
    # Turning directions
    LEFT = -90
    RIGHT = 90
    STRAIGHT = 0

