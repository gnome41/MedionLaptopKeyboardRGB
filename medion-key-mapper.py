#!/usr/bin/env python3
"""
Medion Keyboard Key Mapper
Tool to identify which LED number corresponds to which physical key
"""

import os
import sys
import time
from pathlib import Path

LED_BASE_PATH = "/sys/class/leds"

def get_led_path(key_num):
    """Get the sysfs path for a specific key LED"""
    if key_num == "base":
        return Path(LED_BASE_PATH) / "rgb:kbd_backlight"
    return Path(LED_BASE_PATH) / f"rgb:kbd_backlight_{key_num}"

def set_key_color(key_num, r, g, b):
    """Set RGB values for a specific key"""
    led_path = get_led_path(key_num)
    try:
        multi_intensity_path = led_path / "multi_intensity"
        os.system(f'echo "{r} {g} {b}" | sudo tee {multi_intensity_path} > /dev/null 2>&1')
        return True
    except:
        return False

def turn_all_off():
    """Turn off all keys"""
    print("Turning off all keys...")

    # Turn off base key
    if get_led_path("base").exists():
        set_key_color("base", 0, 0, 0)

    # Turn off numbered keys
    for i in range(126):
        if get_led_path(i).exists():
            set_key_color(i, 0, 0, 0)

def interactive_mode():
    """Interactive mode to identify keys one by one"""
    print("\n" + "="*60)
    print("  MEDION KEYBOARD KEY MAPPER")
    print("="*60)
    print("\nThis tool will light up one key at a time.")
    print("You identify which physical key is lit up.\n")
    print("Commands:")
    print("  [number] - Light up that LED number")
    print("  'base'   - Light up the special base LED")
    print("  'scan'   - Auto-scan through all keys")
    print("  'off'    - Turn all keys off")
    print("  'quit'   - Exit")
    print("="*60 + "\n")

    while True:
        try:
            cmd = input("Enter command: ").strip().lower()

            if cmd == 'quit' or cmd == 'exit' or cmd == 'q':
                turn_all_off()
                print("Goodbye!")
                break

            elif cmd == 'off':
                turn_all_off()
                print("All keys turned off")

            elif cmd == 'scan':
                scan_mode()

            elif cmd == 'base':
                turn_all_off()
                set_key_color("base", 255, 0, 0)
                print("Base LED is now RED")

            elif cmd.isdigit():
                key_num = int(cmd)
                if 0 <= key_num < 126:
                    turn_all_off()
                    set_key_color(key_num, 255, 0, 0)
                    print(f"LED {key_num} is now RED")
                else:
                    print("Invalid key number (0-125)")

            else:
                print("Unknown command")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Turning off all keys...")
            turn_all_off()
            break
        except Exception as e:
            print(f"Error: {e}")

def scan_mode():
    """Automatically scan through all keys"""
    print("\n" + "="*60)
    print("  AUTO-SCAN MODE")
    print("="*60)
    print("\nThis will light up each key in sequence.")
    print("Watch your keyboard and note which physical key lights up.")
    print("\nPress Ctrl+C to stop scanning\n")

    delay = input("Delay between keys in seconds (default 1.0): ").strip()
    try:
        delay = float(delay) if delay else 1.0
    except:
        delay = 1.0

    print(f"\nStarting scan with {delay}s delay...\n")
    time.sleep(2)

    try:
        # Scan base key
        print("Testing: base LED")
        turn_all_off()
        set_key_color("base", 255, 0, 0)
        time.sleep(delay)

        # Scan numbered keys
        for i in range(126):
            if not get_led_path(i).exists():
                continue

            print(f"Testing: LED {i}")
            turn_all_off()
            set_key_color(i, 255, 0, 0)
            time.sleep(delay)

        turn_all_off()
        print("\nScan complete!")

    except KeyboardInterrupt:
        print("\n\nScan interrupted!")
        turn_all_off()

def quick_test():
    """Quick test to identify a few common keys"""
    print("\n" + "="*60)
    print("  QUICK TEST MODE")
    print("="*60)
    print("\nLighting up keys in common positions...")
    print("Note which physical keys light up:\n")

    test_keys = {
        "base": "Base LED",
        0: "LED 0",
        1: "LED 1",
        10: "LED 10",
        20: "LED 20",
        30: "LED 30",
        40: "LED 40",
        50: "LED 50",
        60: "LED 60",
        70: "LED 70",
        80: "LED 80",
        90: "LED 90",
        100: "LED 100",
        110: "LED 110",
        120: "LED 120",
        125: "LED 125"
    }

    for key, label in test_keys.items():
        if get_led_path(key).exists():
            turn_all_off()
            set_key_color(key, 0, 255, 0)  # Green
            print(f"{label} - Which key is GREEN?")
            input("  Press Enter for next key...")

    turn_all_off()
    print("\nQuick test complete!")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'scan':
            turn_all_off()
            scan_mode()
        elif sys.argv[1] == 'quick':
            quick_test()
        elif sys.argv[1] == 'test':
            if len(sys.argv) > 2:
                key = sys.argv[2]
                if key == 'base':
                    turn_all_off()
                    set_key_color("base", 255, 0, 0)
                    print(f"Base LED is now RED")
                else:
                    try:
                        key_num = int(key)
                        turn_all_off()
                        set_key_color(key_num, 255, 0, 0)
                        print(f"LED {key_num} is now RED")
                    except:
                        print("Invalid key number")
            else:
                print("Usage: medion-key-mapper.py test <key_number|base>")
        elif sys.argv[1] == 'off':
            turn_all_off()
        else:
            print("Usage: medion-key-mapper.py [scan|quick|test <key>|off]")
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
