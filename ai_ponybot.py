# ai_ponybot.py

from microbit import sleep, i2c
import math, ustruct
from machine import time_pulse_us
import utime

# PCA9685 레지스터 상수
PCA9685_ADDRESS = 0x40
MODE1 = 0x00
MODE2 = 0x0
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD

# 비트 플래그
RESTART = 0x80
SLEEP = 0x10
ALLCALL = 0x01
OUTDRV = 0x04
RESET = 0x00

class _PWMController:
    """PCA9685 PWM 제어 클래스 (내부용)."""

    def __init__(self, i2c, address=PCA9685_ADDRESS):
        self.address = address
        i2c.write(self.address, bytearray([MODE1, RESET]))
        self.set_all_pwm(0, 0)
        i2c.write(self.address, bytearray([MODE2, OUTDRV]))
        i2c.write(self.address, bytearray([MODE1, ALLCALL]))
        sleep(5)

        # 슬립 해제
        i2c.write(self.address, bytearray([MODE1]))
        mode1 = ustruct.unpack('<B', i2c.read(self.address, 1))[0]
        i2c.write(self.address, bytearray([MODE1, mode1 & ~SLEEP]))
        sleep(5)

    def set_pwm_frequency(self, freq_hz):
        """PWM 주파수 설정"""
        prescaleval = 25000000.0 / 4096 / freq_hz - 1.0
        prescale = int(math.floor(prescaleval + 0.5))

        i2c.write(self.address, bytearray([MODE1]))
        oldmode = ustruct.unpack('<B', i2c.read(self.address, 1))[0]
        newmode = (oldmode & 0x7F) | 0x10
        i2c.write(self.address, bytearray([MODE1, newmode]))
        i2c.write(self.address, bytearray([PRESCALE, prescale]))
        i2c.write(self.address, bytearray([MODE1, oldmode]))
        sleep(5)
        i2c.write(self.address, bytearray([MODE1, oldmode | RESTART]))

    def set_pwm_duty_cycle(self, channel, on, off):
        """PWM 채널 설정"""
        i2c.write(self.address, bytearray([LED0_ON_L + 4 * channel, on & 0xFF]))
        i2c.write(self.address, bytearray([LED0_ON_H + 4 * channel, on >> 8]))
        i2c.write(self.address, bytearray([LED0_OFF_L + 4 * channel, off & 0xFF]))
        i2c.write(self.address, bytearray([LED0_OFF_H + 4 * channel, off >> 8]))

    def set_all_pwm(self, on, off):
        """전체 채널 PWM 설정"""
        i2c.write(self.address, bytearray([ALL_LED_ON_L, on & 0xFF]))
        i2c.write(self.address, bytearray([ALL_LED_ON_H, on >> 8]))
        i2c.write(self.address, bytearray([ALL_LED_OFF_L, off & 0xFF]))
        i2c.write(self.address, bytearray([ALL_LED_OFF_H, off >> 8]))

    def set_duty(self, channel, value):
        """듀티 설정 (0~4095)"""
        if not 0 <= value <= 4095:
            raise ValueError("듀티 값은 0~4095 범위여야 합니다.")
        if value == 0:
            self.set_pwm_duty_cycle(channel, 0, 4096)
        elif value == 4095:
            self.set_pwm_duty_cycle(channel, 4096, 0)
        else:
            self.set_pwm_duty_cycle(channel, 0, value)

class PonyMotor:
    """포니봇의 DC 모터 제어 클래스."""

    def __init__(self, i2c, motor_channels=None, pwm_freq=1000):
        self.pwm = _PWMController(i2c)
        self.pwm.set_pwm_frequency(pwm_freq)

        if motor_channels is None:
            self.motor_channels = {
                1: (7, 6),
                2: (5, 4),
                3: (2, 3),
                4: (0, 1)
            }
        else:
            self.motor_channels = motor_channels

    def move(self, motor_num, speed_percent):
        """
        모터를 이동시킵니다.
        모터 번호: 1~4
        속도 비율: -100 ~ 100
        """
        if motor_num not in self.motor_channels:
            raise ValueError("정의되지 않은 모터 번호: {}".format(motor_num))

        speed_percent = max(-100, min(100, speed_percent))
        pwm_value = int(abs(speed_percent) * 40.95)

        ch1, ch2 = self.motor_channels[motor_num]

        if speed_percent > 0:
            self.pwm.set_duty(ch1, pwm_value)
            self.pwm.set_duty(ch2, 0)
        elif speed_percent < 0:
            self.pwm.set_duty(ch1, 0)
            self.pwm.set_duty(ch2, pwm_value)
        else:
            self.pwm.set_duty(ch1, 0)
            self.pwm.set_duty(ch2, 0)

    def drive(self, direction, speed=0):
        """기본 방향 주행 함수.
        direction: "forward", "backward", "left", "right", "stop"
        speed: 0~100
        """
        speed = max(0, min(100, speed))
        if direction == "forward":
            self.move(1, speed)
            self.move(2, speed)
            self.move(3, speed)
            self.move(4, speed)
        elif direction == "backward":
            self.move(1, -speed)
            self.move(2, -speed)
            self.move(3, -speed)
            self.move(4, -speed)
        elif direction == "left":
            self.move(1, speed)
            self.move(2, speed)
            self.move(3, -speed)
            self.move(4, -speed)
        elif direction == "right":
            self.move(1, -speed)
            self.move(2, -speed)
            self.move(3, speed)
            self.move(4, speed)
        elif direction == "stop":
            for i in range(1, 5):
                self.move(i, 0)
        else:
            raise ValueError("direction must be one of: 'forward', 'backward', 'left', 'right', 'stop'")
            
    def mecanum(self, direction_code, speed=0):
        """
        메카넘휠 특수 방향 이동.
        direction_code:
          7=좌상단, 9=우상단, 4=좌로, 6=우로,
          1=좌하단, 3=우하단,
          8=직진, 2=후진, 5=정지
        speed: 0~100 (5번 정지 시 생략 가능)
        """
        speed = max(0, min(100, speed))
    
        if direction_code == 7:  # 좌상단 대각선
            self.move(1, speed)
            self.move(2, 0)
            self.move(3, speed)
            self.move(4, 0)
        elif direction_code == 9:  # 우상단 대각선
            self.move(1, 0)
            self.move(2, speed)
            self.move(3, 0)
            self.move(4, speed)
        elif direction_code == 4:  # 좌로 수평 이동
            self.move(1, speed)
            self.move(2, -speed)
            self.move(3, speed)
            self.move(4, -speed)
        elif direction_code == 6:  # 우로 수평 이동
            self.move(1, -speed)
            self.move(2, speed)
            self.move(3, -speed)
            self.move(4, speed)
        elif direction_code == 1:  # 좌하단 대각선
            self.move(1, 0)
            self.move(2, -speed)
            self.move(3, 0)
            self.move(4, -speed)
        elif direction_code == 3:  # 우하단 대각선
            self.move(1, -speed)
            self.move(2, 0)
            self.move(3, -speed)
            self.move(4, 0)
        elif direction_code == 8:  # 직진
            self.move(1, speed)
            self.move(2, speed)
            self.move(3, speed)
            self.move(4, speed)
        elif direction_code == 2:  # 후진
            self.move(1, -speed)
            self.move(2, -speed)
            self.move(3, -speed)
            self.move(4, -speed)
        elif direction_code == 5:  # 정지
            for i in range(1, 5):
                self.move(i, 0)
        else:
            raise ValueError("direction_code는 1, 2, 3, 4, 5, 6, 7, 8, 9 중 하나여야 합니다.")
            

class PonyServo:
    """포니봇 서보모터 제어 클래스 (PCA9685 기반)."""

    def __init__(self, pwm, min_us=600, max_us=2400, degrees=180):
        self.pwm = pwm
        self.degrees = degrees
        self.min_duty = self._us_to_duty(min_us)
        self.max_duty = self._us_to_duty(max_us)

    def _us_to_duty(self, us):
        return int(4095 * us / 20000)  # 50Hz 기준 20ms 주기

    def set_angle(self, servo_num, angle):
        """
        서보 번호: 1~8 (S1~S8)
        각도: 0~180도
        """
        if not 1 <= servo_num <= 8:
            raise ValueError("서보 번호는 1~8 사이여야 합니다.")
        angle = max(0, min(self.degrees, angle))
        duty_range = self.max_duty - self.min_duty
        duty = int(self.min_duty + duty_range * angle / self.degrees)
        channel = servo_num + 7  # S1~S8 → 채널 8~15
        self.pwm.set_duty(channel, duty)

    def release(self, servo_num):
        """서보 해제 (신호 제거)"""
        if not 1 <= servo_num <= 8:
            raise ValueError("서보 번호는 1~8 사이여야 합니다.")
        channel = servo_num + 7
        self.pwm.set_duty(channel, 0)

from machine import time_pulse_us
from microbit import sleep
import utime

class PonySonar:
    """초음파 센서 거리 측정 클래스 (정수 cm 반환)"""

    def __init__(self, timeout_us=30000):
        self.timeout = timeout_us

    def measure(self, trig_pin, echo_pin):
        """
        trig_pin: 송신 핀 (예: pin13)
        echo_pin: 수신 핀 (예: pin14)
        반환값: 거리(cm, 정수형), 실패 시 -1
        """
        trig_pin.write_digital(0)
        utime.sleep_us(2)
        trig_pin.write_digital(1)
        utime.sleep_us(10)
        trig_pin.write_digital(0)

        try:
            duration = time_pulse_us(echo_pin, 1, self.timeout)
        except OSError:
            return -1  # 타임아웃

        distance = duration * 0.017  # 거리 계산 (cm)
        distance = int(distance)     # 소수점 제거 → 정수 cm

        if distance < 2 or distance > 400:
            return -1

        return distance
