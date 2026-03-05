# Medion Laptop Keyboard RGB

Per-key RGB keyboard lighting tools for Medion laptops (e.g. Erazer Major X20) on Linux, using the sysfs LED interface.

## Requirements

- Linux with sysfs LED support at `/sys/class/leds/rgb:kbd_backlight*`
- Python 3
- sudo access (required for LED writes)

## Installation

### Option 1: Download a release (recommended)

1. Download the latest release archive from the [Releases](https://github.com/gnome41/MedionLaptopKeyboardRGB/releases) page
2. Extract it:
   ```bash
   tar -xzf MedionLaptopKeyboardRGB-v1.0.0.tar.gz
   cd MedionLaptopKeyboardRGB-v1.0.0
   ```
3. Make the scripts executable:
   ```bash
   chmod +x medion-rgb-ui.py medion-rgb-profile medion-key-mapper.py
   chmod +x save-medion-settings.sh restore-medion-settings.sh
   ```
4. Optionally install them to your PATH:
   ```bash
   sudo cp medion-rgb-profile medion-rgb-ui.py medion-key-mapper.py /usr/local/bin/
   ```

### Option 2: Clone the repository

```bash
git clone https://github.com/gnome41/MedionLaptopKeyboardRGB.git
cd MedionLaptopKeyboardRGB
chmod +x medion-rgb-ui.py medion-rgb-profile medion-key-mapper.py
```

### sudo without password (optional)

LED writes require sudo. To avoid being prompted every time, add a sudoers rule:

```bash
sudo visudo -f /etc/sudoers.d/medion-rgb
```

Add the following line (replace `yourusername`):

```
yourusername ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/class/leds/rgb\:kbd_backlight*
```

## Usage

### medion-rgb-ui.py — Web UI

Interactive browser-based per-key colour control.

```bash
./medion-rgb-ui.py
# Opens http://localhost:8080 in your browser automatically
```

- Visual keyboard layout matching the physical keyboard
- Click any key to change its colour
- Ctrl+Click to select multiple keys, then press Enter to apply colour to all selected
- Save and load profiles
- Colour presets: red, green, blue, purple, cyan, yellow, white, rainbow, off

### medion-rgb-profile — CLI Profile Manager

```bash
./medion-rgb-profile save my-profile      # Save current keyboard state
./medion-rgb-profile load my-profile      # Apply a saved profile
./medion-rgb-profile preset rainbow       # Apply a colour preset
./medion-rgb-profile list                 # List saved profiles
./medion-rgb-profile delete my-profile    # Delete a profile
```

Presets: `rainbow`, `red`, `green`, `blue`, `purple`, `cyan`, `yellow`, `white`, `off`

Profiles are saved to `~/.config/medion-rgb-profiles/` and can be shared between tools.

### medion-key-mapper.py — LED Key Mapper

Diagnostic tool for identifying which LED number corresponds to which physical key. Useful if you want to customise the keyboard layout in `medion-rgb-ui.py`.

```bash
./medion-key-mapper.py              # Interactive mode
./medion-key-mapper.py scan         # Auto-scan all keys with a delay
./medion-key-mapper.py quick        # Test a selection of common positions
./medion-key-mapper.py test 42      # Light up a specific LED number
./medion-key-mapper.py off          # Turn all keys off
```

### Backup Scripts

Back up and restore the Tuxedo Control Center session storage (if used alongside the official Medion software):

```bash
./save-medion-settings.sh           # Backup to ~/.medion-control-center-backup/
./restore-medion-settings.sh        # Restore from backup
```

## How It Works

All tools interact with the Linux sysfs LED interface at `/sys/class/leds/`:

- Base LED: `rgb:kbd_backlight` (maps to left Ctrl)
- Individual keys: `rgb:kbd_backlight_{0-125}` (126 keys total)

Each LED has:
- `multi_intensity` — RGB values as space-separated integers (0-255)
- `brightness` — Brightness level (0-50)

Writes are performed via `sudo tee`.

## Profile Format

Profiles are stored as JSON in `~/.config/medion-rgb-profiles/`:

```json
{
  "version": 1,
  "keys": {
    "base": {"rgb": [255, 0, 0], "brightness": 50},
    "42": {"rgb": [0, 0, 255], "brightness": 50}
  }
}
```

The `"base"` key refers to the unnumbered `rgb:kbd_backlight` LED. Keys not listed in a profile are left unchanged when the profile is loaded.

## Compatibility

Tested on the Medion Erazer Major X20 running Arch Linux. Other Medion laptops using the same sysfs LED interface should work. The key-to-LED mapping in the web UI is specific to the Major X20 keyboard layout — use `medion-key-mapper.py` to build a mapping for a different model.

## License

MIT
