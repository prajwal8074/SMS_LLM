# Caller Voice Request-Response Interface
- Plays a prerecorded audio file to the caller and records caller voice input later

## Call Response Interface Demo:
<video src="https://github.com/user-attachments/assets/35e05298-a1ef-47f5-a2ea-d81375fa492e" style="max-width: 100%;">Demo Video</video>

## Logic Flow
<img src="https://github.com/user-attachments/assets/38691b86-39eb-4d6c-9e60-42240da08091" alt="logic flow" height="480">

## Code Flow
<img src="https://github.com/user-attachments/assets/987a0f67-5f7f-4017-b3a8-f101abde1dde" alt="code flow" height="720">

## How to reproduce call response interface
### Requirements: Ubuntu system with PulseAudio, Android device
### Steps:
1. To connect ubuntu as handsfree, [follow this](https://askubuntu.com/a/1512854)
2. Uninstall pipewire [instructions](https://askubuntu.com/a/1441491) and restart ubuntu when done
3. Connect to ubuntu device on android via bluetooth, it shoud appear as an audio device
4. Clone Repository
5. Connect android device to ubuntu system via usb cable, Enble USB Debugging in developer options
6. Open a terminal in the Desktop folder of the cloned repo
7. Create a folder named CallRecordings (```mkdir CallRecordings```)
8. Install [Dialer App](DialerApp/app/build/outputs/apk/core/debug/dialer-core-debug.apk) on connected android device
9. Run ```./call_handler.sh```
10. Now calls on the connected android device should play an audio message and save caller voice message in the CallRecordings folder
