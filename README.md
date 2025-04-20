# AI Ponybot 라이브러리
![Micro:bit](https://img.shields.io/badge/platform-micro%3Abit-blue?logo=microbit)

AI 포니봇(AI Ponybot)은 **마이크로비트** 기반의 **AI 교육용 로봇, AI Ponybot 제어어**을 위한 파이썬 라이브러리입니다. 이 라이브러리는 **모터 제어**, **서보모터 제어**, **센서 관리** 등 다양한 기능을 제공하며, 교육용 및 실습용 로봇 개발에 유용하게 활용될 수 있습니다. AI 포니봇은 **모터**, **서보모터**, **디스플레이**, **센서** 등 다양한 하드웨어와 쉽게 연동하여 사용할 수 있도록 설계되었습니다.

---

## 라이브러리 구성

### 1. **PonyMotor (모터 제어)**

- **4개의 DC 모터 제어**: 속도와 방향을 설정하여 제어합니다.
- **PWM 제어**: PCA9685 모듈을 사용하여 PWM 신호를 생성하고, 이를 통해 모터의 속도와 방향을 제어합니다.
- **메카넘 휠 제어**: 메카넘 휠 방식으로 다양한 방향으로 모터를 제어할 수 있습니다.

**주요 함수**:
- `move(motor_num, speed_percent)`: 특정 모터를 지정된 속도로 움직입니다.
- `drive(direction, speed)`: 전체 모터를 한 방향으로 움직입니다.
- `mecanum(direction_code, speed)`: 메카넘 휠 제어로 다양한 방향으로 이동합니다.

### 2. **PonyServo (서보모터 제어)**

- **서보모터 제어**: PCA9685 모듈을 사용하여 **8개 서보모터**를 제어합니다.
- **각도 설정**: 서보모터의 각도를 **0~180도** 범위 내에서 설정할 수 있습니다.
- **듀티 사이클**: 서보모터의 제어 신호를 위한 듀티 사이클 값을 조정하여 정밀한 각도 제어가 가능합니다.

**주요 함수**:
- `set_angle(servo_num, angle)`: 서보모터의 각도를 설정합니다.
- `release(servo_num)`: 서보모터의 신호를 해제하여 제어를 멈춥니다.

### 3. **PonyOLED (OLED 디스플레이 제어)**

- **OLED 디스플레이 제어**: **128x64 OLED 디스플레이**를 제어하는 클래스입니다.
- **텍스트 및 도형 출력**: 텍스트, 수평선, 수직선, 사각형, 원 등의 도형을 출력할 수 있습니다.

**주요 함수**:
- `clear()`: 화면을 지웁니다.
- `invert(on)`: 화면 색상을 반전시킵니다.
- `display(on)`: 화면을 켜거나 끕니다.
- `draw_text(x, y, text, color)`: 지정된 위치에 텍스트를 출력합니다.
- `draw_hline(x, y, length, color)`: 수평선을 그립니다.
- `draw_vline(x, y, length, color)`: 수직선을 그립니다.
- `draw_rect(x1, y1, x2, y2, color)`: 사각형을 그립니다.

### 4. **PonyColor (TCS34725 색상 센서 제어)**

- **TCS34725 색상 센서 제어**: **RGB 색상 센서**를 제어하여 색상 값을 읽어옵니다.

**주요 함수**:
- `getLight()`: 밝기 값(Clear 채널)을 읽어옵니다.
- `getRed()`, `getGreen()`, `getBlue()`: 각각 빨간색, 초록색, 파란색 값을 읽어옵니다.
- `setColorIntegrationTime(time)`: 색상 통합 시간을 설정합니다.
- `isColorAdvanced(color, threshold)`: 특정 색상(빨간색, 초록색, 파란색, 노란색)을 감지합니다.
- `isColorInRange(minR, maxR, minG, maxG, minB, maxB)`: RGB 범위 내에 색상이 있는지 판별합니다.

---

## 전원 관리

AI 포니봇은 **18650 3.7V 2000mAh 배터리 2개**를 사용하여 **7.4V**를 공급받습니다. 이 배터리는 **모터**, **서보모터**, **디스플레이** 및 **센서**에 필요한 전력을 공급합니다. 각 하드웨어는 **전압 변환** 및 **배터리 보호 회로**를 통해 안전하게 작동할 수 있습니다.

---

## 사용 방법

### 예시 코드

```python
from microbit import i2c, sleep
from ai_ponybot import PonyMotor, PonyServo, PonyOLED, PonyColor

# 모터와 서보모터 초기화
motor = PonyMotor(i2c)
servo = PonyServo(i2c)
oled = PonyOLED(i2c)
color_sensor = PonyColor(i2c)

# 모터 제어 예시
motor.move(1, 50)  # 모터 1을 50% 속도로 이동
motor.drive("forward", 100)  # 모든 모터를 100% 속도로 전진

# 서보모터 제어 예시
servo.set_angle(1, 90)  # 서보모터 1을 90도 위치로 설정

# OLED 디스플레이 출력 예시
oled.clear()
oled.draw_text(0, 0, "AI Ponybot", 1)
oled.show()

# 색상 센서 예시
light = color_sensor.getLight()
rgb = color_sensor.rgb()
if color_sensor.isColor("red"):
    oled.draw_text(0, 16, "Red Detected!", 1)
oled.show()

sleep(1000)
