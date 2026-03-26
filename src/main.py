"""Entry point for ExifTool GUI application."""
import sys
from gui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
