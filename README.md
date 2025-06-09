# LLM accessibility for farmers

1st week progress:
## Discussion
[Minutes of Discussion](Minutes-of-Discussion.docx)
## Research Results
[Indian Languages Translation Model](Translate-100-languages.zip)

[Text To Speech Model](Text-To-Speech-Unlimited.zip)

## Call Response Interface Demo:
[Demo Video](Demo.mp4)

## How to reproduce call response interface
### Requirements: Ubuntu system with PulseAudio, Android device
### Steps:
1. To connect ubuntu as handsfree, [follow this](https://askubuntu.com/a/1512854)
2. Connect to ubuntu device on android via bluetooth, it shoud appear as an audio device
3. Clone Repository
4. Connect android device to ubuntu system via usb cable, Enble USB Debugging in developer options
5. Open a terminal in the Desktop folder of the cloned repo
6. Create a folder named CallRecordings ('''mkdir CallRecordings''')
7. Run '''./call_handler.sh'''
8. Now calls on the connected android device should play an audio message and save caller voice message in the CallRecordings folder
