"""Get / set the primary display resolution (needs pywin32, in the repo .venv).

  python set_display.py            -> prints current mode
  python set_display.py 1920 1080  -> set to 1920x1080 (needed for live runs)
  python set_display.py 3840 2160  -> restore this machine's native 4K

The live pipeline is calibrated for a 1920x1080 primary. The bridge is
per-monitor-DPI-aware, so coordinates are physical pixels; 1920x1080 makes the
model's x<960 boundary the true screen midpoint.
"""
import sys, win32api, win32con

dev = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
print("CURRENT_MODE: %dx%d @ %dHz %dbpp" % (dev.PelsWidth, dev.PelsHeight,
                                            dev.DisplayFrequency, dev.BitsPerPel))
if len(sys.argv) >= 3:
    w, h = int(sys.argv[1]), int(sys.argv[2])
    dev.PelsWidth = w; dev.PelsHeight = h
    dev.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
    code = win32api.ChangeDisplaySettings(dev, win32con.CDS_UPDATEREGISTRY)
    print("SET %dx%d -> code %d (0=SUCCESSFUL)" % (w, h, code))
    dev2 = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
    print("NOW_MODE: %dx%d @ %dHz" % (dev2.PelsWidth, dev2.PelsHeight, dev2.DisplayFrequency))
