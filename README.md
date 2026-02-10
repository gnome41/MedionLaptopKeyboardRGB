# Medion Laptop Keyboard RGB

Per-key RGB keyboard lighting tools for Medion laptops (e.g. Erazer Major X20) on Linux, using the sysfs LED interface.

## Requirements

- Linux with sysfs LED support at `/sys/class/leds/rgb:kbd_backlight*`
- Python 3
- sudo access (required for LED writes)

## Tools

### medion-rgb-ui.py — Web UI

Interactive browser-based per-key colour control.

```bash
./medion-rgb-ui.py
# Opens http://localhost:8080
```

- Visual keyboard layout matching the physical keyboard
- Click any key to change its colour
- Ctrl+Click to select multiple keys, then press Enter to apply
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

### medion-key-mapper.py — LED Key Mapper

Diagnostic tool for identifying which LED number corresponds to which physical key.

```bash
./medion-key-mapper.py              # Interactive mode
./medion-key-mapper.py scan         # Auto-scan all keys
./medion-key-mapper.py quick        # Test common positions
./medion-key-mapper.py test 42      # Light up a specific LED
```

### Backup Scripts

```bash
./save-medion-settings.sh           # Backup control centre config
./restore-medion-settings.sh        # Restore from backup
```

## How It Works

All tools interact with the Linux sysfs LED interface at `/sys/class/leds/`:

- Base LED: `rgb:kbd_backlight`
- Individual keys: `rgb:kbd_backlight_{0-125}` (126 keys total)

Each LED has:
- `multi_intensity` — RGB values as space-separated integers (0-255)
- `brightness` — Brightness level (0-50)

Writes are performed via `sudo tee`.

## Profiles

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

The `"base"` key refers to the unnumbered `rgb:kbd_backlight` LED.

## License

MIT
