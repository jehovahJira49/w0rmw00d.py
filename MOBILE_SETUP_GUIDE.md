# Mobile Development Setup Guide

## 1. Remote Development (Access VS Code from Phone)

### Option A: GitHub Codespaces
1. Push your project to GitHub
2. Open GitHub on your phone's browser
3. Navigate to your repository
4. Press `.` (period key) or change `.com` to `.dev` in URL
5. This opens VS Code in your browser

### Option B: VS Code Server (Tunnels)
Run on your PC:
```powershell
code tunnel
```
Then access from your phone browser using the provided URL.

---

## 2. File Transfer Setup (ADB for Android)

### Install ADB
```powershell
# Using winget
winget install Google.PlatformTools

# Or using Chocolatey
choco install adb
```

### Enable USB Debugging on Phone
1. Go to Settings → About Phone
2. Tap "Build Number" 7 times to enable Developer Options
3. Go to Developer Options → Enable "USB Debugging"
4. Connect phone via USB

### ADB Commands
```powershell
# Check connected devices
adb devices

# Push files to phone
adb push <local_file> /sdcard/

# Pull files from phone
adb pull /sdcard/<file> <local_destination>

# Install APK
adb install app.apk
```

---

## 3. Mobile Game Development (Pygame to Mobile)

### Option A: Pygame Subset for Android (pgs4a)
**Note**: This is outdated. Use Buildozer instead.

### Option B: Buildozer (Recommended for Android)

#### Setup Buildozer
```powershell
# Install Python dependencies
pip install buildozer cython

# For Windows, use WSL (Windows Subsystem for Linux)
wsl --install
```

#### After WSL is installed:
```bash
# In WSL terminal
sudo apt update
sudo apt install -y python3-pip build-essential git zip unzip openjdk-11-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
pip3 install buildozer cython
```

#### Create buildozer.spec file
```bash
buildozer init
```

#### Build APK
```bash
buildozer -v android debug
```

### Option C: Kivy (Cross-platform: Android & iOS)

#### Install Kivy
```powershell
pip install kivy kivymd
```

#### Convert Pygame to Kivy
Kivy uses a different architecture than Pygame. You'll need to rewrite your game using Kivy widgets and events.

Example Kivy game structure:
```python
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock

class GameWidget(Widget):
    def update(self, dt):
        # Game logic here
        pass

class MyGameApp(App):
    def build(self):
        game = GameWidget()
        Clock.schedule_interval(game.update, 1.0/60.0)
        return game

if __name__ == '__main__':
    MyGameApp().run()
```

---

## Quick Start Recommendation

1. **For Testing on Phone**: Use VS Code Tunnels (easiest)
2. **For File Transfer**: Install ADB
3. **For Mobile Game**: Start with Kivy (best cross-platform support)

---

## Next Steps

Would you like me to:
- Set up VS Code tunnel for remote access?
- Install ADB and help with file transfer?
- Convert your pygame game to Kivy?
- Set up WSL and Buildozer for Android development?
