#!/bin/bash

# --- Configuration ---
BLUETOOTH_SINK="" # IMPORTANT: Replace with your actual Bluetooth sink name
BLUETOOTH_SOURCE="" # IMPORTANT: Replace with your actual Bluetooth source name
RECORDING_DIR="CallRecordings"
FILE_PATH="CallRecordings/caller_input_temp.wav"
FINAL_FILE_PATH="CallRecordings/caller_input.wav"
RECORDING_PROCESS_PID=""
PAPLAY_PID=""
LOOP_PROCESS_PID=""

# Define your desired USB microphone source
NULL_SOURCE=""
# Variable to store the original default source
ORIGINAL_DEFAULT_SOURCE=""

# Voice Detection Configuration
SILENCE_THRESHOLD="1%"            # Initial silence threshold (percentage)
CALIBRATION_DURATION=3             # Seconds for initial silence calibration
MAX_RECORDING_DURATION=10
VOICE_RECORDING_PID=""             # PID of the voice detection process
VOICE_RECORDING_ACTIVE=false       # Track if voice recording is active
# SOURCE_STATUS="SUSPENDED"

BLANK_DURATION=0.5 # seconds
BLANK_FILE="temp_blank.wav" # Temporary file for the blank audio

RESPONSE_PATH="output_response.mp3"

# --- Functions ---
# Define the function in your script or shell
extract_bluetooth_devices() {
    BLUETOOTH_SOURCE=$(pactl list short sources | awk '/bluez_source/ {print $2}')
    export BLUETOOTH_SOURCE

    BLUETOOTH_SINK=$(pactl list short sinks | awk '/bluez_sink/ {print $2}')
    export BLUETOOTH_SINK

    if [ -z "$BLUETOOTH_SOURCE" ]; then
        echo "Warning: BLUETOOTH_SOURCE not found."
    else
        echo "BLUETOOTH_SOURCE set to: $BLUETOOTH_SOURCE"
    fi

    if [ -z "$BLUETOOTH_SINK" ]; then
        echo "Warning: BLUETOOTH_SINK not found."
    else
        echo "BLUETOOTH_SINK set to: $BLUETOOTH_SINK"
    fi
}

# Function to play audio to the phone (Bluetooth sink)
play_audio_to_phone() {
    local audio_file="$1"
    echo "Playing audio file: $audio_file to sink: $BLUETOOTH_SINK"

    # Start paplay in the background and store its PID
    paplay --device="$BLUETOOTH_SINK" "$audio_file" &> /dev/null &
    PAPLAY_PID=$! # Store the PID of the last background process
}

stop_playing() {
    echo -e "\nInterruption detected. Stopping audio playback..."
    if [ -n "$PAPLAY_PID" ]; then # Check if PAPLAY_PID is not empty
        kill "$PAPLAY_PID" 2>/dev/null # Send SIGTERM to paplay process
        wait "$PAPLAY_PID" 2>/dev/null # Wait for it to terminate
        PAPLAY_PID=""
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

# get_source_status() {
#     local source_name="$1"
#     # Get the status of the specific source using pactl and awk
#     # awk will look for lines containing the source_name and print the last field (status)
#     pactl list short sources | awk -v name="$source_name" '$0 ~ name {print $NF}'
# }

# Function to calibrate silence threshold
calibrate_silence_threshold() {
    echo "Calibrating silence threshold for ${CALIBRATION_DURATION} seconds..."
    local calibration_file="${RECORDING_DIR}/calibration_temp.wav"
    
    # Record calibration sample from Bluetooth source
    timeout $CALIBRATION_DURATION parecord --device="$BLUETOOTH_SOURCE" "$calibration_file"
    
    # Calculate threshold (1% above calibrated noise floor)
    SILENCE_THRESHOLD=$(sox "$calibration_file" -n stat 2>&1 | awk '/Maximum delta/{print $3 * 1.01 "%"}')
    rm -f "$calibration_file"
    
    if [ -z "$SILENCE_THRESHOLD" ]; then
        SILENCE_THRESHOLD="1%"
        echo "Calibration failed! Using default threshold: $SILENCE_THRESHOLD"
    else
        echo "Calibration complete. New threshold: $SILENCE_THRESHOLD"
    fi
}

# Function to start voice-triggered recording
start_voice_recording() {

    echo "Voice detection ENABLED (Threshold: $SILENCE_THRESHOLD)"

    local output_file="$FILE_PATH"

    echo "Listening for voice input from $BLUETOOTH_SOURCE (max ${MAX_RECORDING_DURATION}s)..."

    # Record with silence detection from Bluetooth source, with an overall timeout
    # Redirect sox's output to /dev/null to keep the console clean
    # The `timeout` command wraps `sox`
    timeout "${MAX_RECORDING_DURATION}" sox -t pulseaudio "$BLUETOOTH_SOURCE" "$output_file" \
        silence 1 0.1 "$SILENCE_THRESHOLD" \
        1 0.5 "$SILENCE_THRESHOLD" &
    VOICE_RECORDING_PID=$! # This PID will now be of the 'timeout' command
    echo "Voice recording started (PID: $VOICE_RECORDING_PID). Output file: $output_file"
}

# Function to stop voice-triggered recording
stop_voice_recording() {
    # Ensure any remaining processes are cleaned up
    if [ -n "$VOICE_RECORDING_PID" ]; then
        kill $VOICE_RECORDING_PID 2>/dev/null
        wait $VOICE_RECORDING_PID 2>/dev/null
        VOICE_RECORDING_PID=""
    fi
    echo "Voice recording stopped"
}

run_main_loop() {
    while true; do
        change_pulseaudio_source "$NULL_SOURCE" # Change source when call is picked up
    
        mkdir "${RECORDING_DIR}"
        play_audio_to_phone "ask.wav"
        wait "$PAPLAY_PID"
    
        # Start voice-triggered recording after audio playback
        start_voice_recording
        wait $VOICE_RECORDING_PID
        echo "Recording Completed"

        if [ -f "$FILE_PATH" ]; then
            echo "File '$FILE_PATH' exists."
            play_audio_to_phone "processing.wav"

            # Get sample rate and number of channels from the input file
            SR=$(soxi -r "$FILE_PATH")
            CH=$(soxi -c "$FILE_PATH")

            sox -n -r "$SR" -c "$CH" "$BLANK_FILE" trim 0.0 "$BLANK_DURATION"

            # 2. Concatenate the blank audio with your input audio file
            # The order depends on whether you want the blank audio at the beginning or end.

            # To add 0.5 seconds of blank audio to the BEGINNING:
            sox "$BLANK_FILE" "$FILE_PATH" "$FINAL_FILE_PATH"
            python3 get_response.py
            rm -r "${RECORDING_DIR}"
            stop_playing
            play_audio_to_phone "$RESPONSE_PATH"
            wait "$PAPLAY_PID"
        else
            echo "File '$FILE_PATH' does NOT exist."
        fi

        # SOURCE_STATUS=$(get_source_status "$BLUETOOTH_SOURCE")
    done
}

stop_main_loop() {
    echo -e "\nMain script interrupted. Cleaning up..."
    if [ -n "$LOOP_PROCESS_PID" ]; then
        pkill -P "$LOOP_PROCESS_PID"
        kill "$LOOP_PROCESS_PID" 2>/dev/null # Send polite termination signal
        wait "$LOOP_PROCESS_PID" 2>/dev/null # Wait for it to terminate
        LOOP_PROCESS_PID=""
        if [ $? -ne 0 ]; then
             echo "Background loop (PID: $LOOP_PROCESS_PID) might not have terminated cleanly."
        else
             echo "Background loop terminated."
        fi
    fi
}

# Function to handle cleanup on script interruption (Ctrl+C, etc.)
cleanup_on_interrupt() {
    echo "Interrupt signal received. Performing cleanup..."
    stop_voice_recording
    stop_playing
    stop_main_loop
    systemctl --user daemon-reload
    systemctl --user --now disable pulseaudio.service pulseaudio.socket
    systemctl --user --now enable pipewire pipewire-pulse
    echo "Cleanup complete. Exiting."
    exit 0
}

# --- Main Logic ---
source venv/bin/activate

# Trap interrupt signals (Ctrl+C, termination)
trap cleanup_on_interrupt INT TERM EXIT

systemctl --user unmask pulseaudio
systemctl --user --now disable pipewire-media-session.service
systemctl --user --now disable pipewire pipewire-pulse
systemctl --user --now enable pulseaudio.service pulseaudio.socket

pactl load-module module-null-sink   sink_name=null_output
NULL_SOURCE="null_output.monitor"

sleep 3

# Call the function to set the variables
extract_bluetooth_devices

# Now you can use the variables
echo "Bluetooth Source is: $BLUETOOTH_SOURCE"
echo "Bluetooth Sink is: $BLUETOOTH_SINK"

echo "Clearing adb logcat buffer..."
adb logcat -c # Clear the logcat buffer

echo "Starting adb logcat monitoring..."

adb logcat -v raw AutoCall:I *:S | while IFS= read -r line; do
    echo "Logcat output: $line"

    if echo "$line" | grep -q "Call picked up"; then
        echo "Delaying audio playback by 1 second..."
        sleep 1

        #play_audio_to_phone "calibration.wav"

        # Calibrate silence threshold from Bluetooth source
        #calibrate_silence_threshold

        SOURCE_STATUS=$(get_source_status "$BLUETOOTH_SOURCE")
        
        # Run the run_main_loop function in a subshell and background it
        ( run_main_loop ) &
        LOOP_PROCESS_PID=$! # Capture the PID of the background subshell

        stop_voice_recording
    else
        if echo "$line" | grep -q "Call ended"; then
            stop_voice_recording
            stop_playing
            stop_main_loop
        fi
    fi

done

echo "adb logcat monitoring stopped."
