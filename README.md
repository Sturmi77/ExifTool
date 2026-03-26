# ExifTool GUI

A lightweight Python GUI to quickly and easily edit **date** and **location (GPS)** metadata of photos in selected folders.

Built on top of [ExifTool by Phil Harvey](https://exiftool.org/) — a powerful, open-source metadata tool licensed under the Perl Artistic License / GPL.

## Features

- 📁 Select one or multiple folders with photos
- 📅 Change the date/time of photos (DateTimeOriginal, CreateDate)
- 📍 Change GPS coordinates (latitude / longitude)
- 🔍 Preview EXIF data before applying changes
- 💾 Automatic backup of original files before writing
- 🖥️ Simple, minimal GUI (Python + Tkinter)

## Requirements

- Python 3.10+
- [ExifTool](https://exiftool.org/) installed and available in `$PATH`
- Python packages: see `requirements.txt`

## Installation

```bash
git clone https://github.com/Sturmi77/ExifTool.git
cd ExifTool
pip install -r requirements.txt
```

Make sure `exiftool` is installed on your system:

```bash
# Debian/Ubuntu
sudo apt install libimage-exiftool-perl

# macOS
brew install exiftool

# Windows: Download from https://exiftool.org/
```

## Usage

```bash
python src/main.py
```

## Project Structure

```
ExifTool/
├── src/
│   ├── main.py          # Entry point, launches GUI
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── app.py       # Main application window
│   │   ├── folder_panel.py   # Folder selection panel
│   │   └── edit_panel.py     # Date/Location edit panel
│   └── core/
│       ├── __init__.py
│       ├── exiftool.py  # Wrapper around ExifTool CLI
│       └── utils.py     # Helper functions
├── tests/
│   └── test_exiftool.py
├── requirements.txt
├── .gitignore
└── README.md
```

## License

MIT License — see [LICENSE](LICENSE)

This project uses [ExifTool](https://exiftool.org/) by Phil Harvey, which is licensed under the Perl Artistic License / GPL.
