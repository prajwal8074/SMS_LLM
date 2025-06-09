#!/bin/bash

# --- Configuration ---
BLUETOOTH_SINK="bluez_sink.60_D4_E9_20_8F_DC.handsfree_audio_gateway" # IMPORTANT: Replace with your actual Bluetooth sink name
BLUETOOTH_SOURCE="bluez_source.60_D4_E9_20_8F_DC.handsfree_audio_gateway" # IMPORTANT: Replace with your actual Bluetooth source name
AUDIO_FILE_TO_PLAY="response.mp3" # IMPORTANT: Replace with your audio file
RECORDING_DIR="CallRecordings"
INCOMING_VOICE_RECORDING_FILENAME=""
RECORDING_PROCESS_PID=""

# Define your desired USB microphone source
USB_MIC_SOURCE="alsa_input.usb-C-Media_Electronics_Inc._C-Media_R__Audio-00.mono-fallback"
# Variable to store the original default source
ORIGINAL_DEFAULT_SOURCE=""

# --- Functions ---

# Function to play audio to the phone (Bluetooth sink)
play_audio_to_phone() {
    local audio_file="$1"
    echo "Playing audio file: $audio_file to sink: $BLUETOOTH_SINK"
    # Using paplay for simplicity, redirecting its output to /dev/null
    paplay --device="$BLUETOOTH_SINK" "$audio_file" &> /dev/null
    if [ $? -ne 0 ]; then
        echo "Error playing audio file."
    fi
}

# Function to start incoming voice recording
start_recording_incoming_voice() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    INCOMING_VOICE_RECORDING_FILENAME="${RECORDING_DIR}/incoming_voice_${timestamp}.wav"

    mkdir -p "$RECORDING_DIR"

    echo "Starting incoming voice recording from source: $BLUETOOTH_SOURCE to: $INCOMING_VOICE_RECORDING_FILENAME"
    # Using parecord, which is more reliable for PulseAudio sources
    # --raw is not needed as --file-format=wav handles it
    parecord --device="$BLUETOOTH_SOURCE" --file-format=wav "$INCOMING_VOICE_RECORDING_FILENAME" &
    RECORDING_PROCESS_PID=$!
    echo "Recording process PID: $RECORDING_PROCESS_PID"
    if [ $? -ne 0 ]; then
        echo "Error starting recording with parecord. Check if pulseaudio-utils is installed and source name is correct."
    fi
}

# Function to stop incoming voice recording
stop_recording_incoming_voice() {
    if [ -n "$RECORDING_PROCESS_PID" ]; then
        echo "Stopping incoming voice recording (PID: $RECORDING_PROCESS_PID)"
        kill "$RECORDING_PROCESS_PID"
        wait "$RECORDING_PROCESS_PID" 2>/dev/null # Wait for the process to terminate
        echo "Recording saved to: $INCOMING_VOICE_RECORDING_FILENAME"
        RECORDING_PROCESS_PID=""
        INCOMING_VOICE_RECORDING_FILENAME=""
    else
        echo "No active recording process to stop."
    fi
}

# Function to change the default PulseAudio source
change_pulseaudio_source() {
    local new_source="$1"
    # Get the current default source before changing it
    ORIGINAL_DEFAULT_SOURCE=$(pactl info | grep "Default Source:" | cut -d ' ' -f3-)
    echo "Current default source: $ORIGINAL_DEFAULT_SOURCE"
    echo "Changing default PulseAudio source to: $new_source"
    pactl set-default-source "$new_source"
    if [ $? -ne 0 ]; then
        echo "Error changing default PulseAudio source to $new_source. Make sure the source name is correct."
    fi
}

# Function to revert to the original PulseAudio source
revert_pulseaudio_source() {
    if [ -n "$ORIGINAL_DEFAULT_SOURCE" ]; then
        echo "Reverting default PulseAudio source to: $ORIGINAL_DEFAULT_SOURCE"
        pactl set-default-source "$ORIGINAL_DEFAULT_SOURCE"
        if [ $? -ne 0 ]; then
            echo "Error reverting default PulseAudio source to $ORIGINAL_DEFAULT_SOURCE."
        fi
        ORIGINAL_DEFAULT_SOURCE="" # Clear the stored original source
    else
        echo "No original default source to revert to."
    fi
}

# --- Main Logic ---

echo "Clearing adb logcat buffer..."
adb logcat -c # Clear the logcat buffer

echo "Starting adb logcat monitoring..."

adb logcat -v raw AutoCall:I *:S | while IFS= read -r line; do
    echo "Logcat output: $line"

    if echo "$line" | grep -q "Call picked up"; then
        echo "Detected: Call picked up"
        stop_recording_incoming_voice # Ensure any previous recording is stopped
        change_pulseaudio_source "$USB_MIC_SOURCE" # Change source when call is picked up
        echo "Delaying audio playback by 2 seconds..."
        sleep 2
        play_audio_to_phone "$AUDIO_FILE_TO_PLAY"
        start_recording_incoming_voice

    elif echo "$line" | grep -q "Call ended"; then
        echo "Detected: Call ended"
        stop_recording_incoming_voice
    fi
done

echo "adb logcat monitoring stopped."
