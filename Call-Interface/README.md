# Caller Voice Request-Response Interface
- Creates a IVR like system on personal phone number

## Call Response Interface Demo:
<video src="https://github.com/user-attachments/assets/bdf1b9fc-4d9a-46a4-a681-0865b633da2c" style="max-width: 100%;">Demo Video</video>


## Logic Flow
<img src="https://github.com/user-attachments/assets/369847e9-734c-467c-8f95-6144d89d8d53" alt="logic flow" height="720">

## How to reproduce
### Requirements: Ubuntu system, Android device
### Steps:
1. To connect ubuntu as handsfree, [follow this](https://askubuntu.com/a/1512854)
2. Connect to ubuntu device on android via bluetooth, it shoud appear as an audio device
3. Clone Repository
4. Open terminal in the 'Call-Interface' folder
5. Connect android device to ubuntu system via usb, enble USB Debugging in developer options
6. Install 'Dialer App' on connected android device (```adb install DialerApp/app/build/outputs/apk/core/debug/dialer-core-debug.apk```)
7. Create a folder named CallRecordings in the 'Desktop' folder (```mkdir Desktop/CallRecordings```)
8. Run ```./Desktop/call_handler.sh```
9. Now calls on the connected android device should interact as shown in the demo video
