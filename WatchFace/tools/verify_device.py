"""Capture the active real-device preview and check tap destinations."""
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
ADB = 'C:/AndroidSdk/platform-tools/adb.exe'

def adb(*args):
    return subprocess.run([ADB, *args], capture_output=True, check=True, timeout=20).stdout

def shell(*args):
    return adb('shell', *args).decode('utf-8', errors='replace')

def capture(name):
    target = ROOT / 'design' / 'round-buttons' / name
    target.write_bytes(adb('exec-out', 'screencap', '-p'))
    print('Captured', target.name)

def home():
    shell('input', 'keyevent', 'KEYCODE_HOME')
    shell('input', 'keyevent', 'KEYCODE_WAKEUP')
    # An AOD tap may only wake the display. Tap the non-interactive date first.
    shell('input', 'tap', '240', '80')
    time.sleep(.7)

home()
capture('device-active.png')
for name, point, expected in [
    ('recorder', (240, 398), 'com.samsung.android.wear.voicerecorder.view.MainActivity'),
    ('heart', (350, 170), 'HeartRateActivity'),
    ('steps', (350, 211), 'com.samsung.android.wear.shealth.app.home.HomeActivity'),
    ('battery', (350, 244), 'BatteryMainActivity'),
    ('weather', (240, 289), 'com.samsung.android.watch.weather')]:
    shell('input', 'tap', str(point[0]), str(point[1]))
    time.sleep(1.5)
    focused = shell('dumpsys', 'window')
    focus = [l.strip() for l in focused.splitlines() if 'mCurrentFocus=' in l]
    print(name, ':', '; '.join(focus))
    capture(f'tap-{name}.png')
    home()
    assert expected in '; '.join(focus), f'{name} opened an unexpected screen: {focus}'

print('Active-mode checks completed; no device settings changed.')
