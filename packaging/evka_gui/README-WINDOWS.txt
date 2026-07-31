EVKA Position GUI - Windows
===========================

HOW TO START
------------
Double-click EvkaGUI.exe in this folder.

You do not need Python installed. The first launch may take a few seconds
while Windows scans the files.


KEEP THE FOLDER TOGETHER
------------------------
EvkaGUI.exe needs the other files in this folder to run. Do not move or copy
the .exe out on its own - it will not start.

To put it on your Desktop: right-click EvkaGUI.exe -> Send to -> Desktop
(create shortcut). That makes a shortcut, which is fine. Moving the actual
file is not.


CONNECTING OVER USB (SERIAL)
----------------------------
Windows needs a driver for the USB-to-serial chip on the board. Install it
once, then reboot:

  CH340 / CH341  ->  http://www.wch-ic.com/downloads/CH341SER_EXE.html
  CP210x         ->  https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers

Plug the board in, click "Refresh" next to the port list, and pick the COM
port that appears (COM3, COM4, ...). Baud rate is 115200.

If no COM port shows up, the driver is missing or the cable is charge-only.


CONNECTING OVER WI-FI (TCP / WEBSOCKET)
---------------------------------------
The first time you connect, Windows will ask whether to allow EvkaGUI through
Windows Firewall. Tick "Private networks" and click Allow. If you click Cancel,
network connections will silently fail and you will need to re-enable it in
Windows Defender Firewall settings.


WHERE YOUR FILES GO
-------------------
Exports (snapshots, saved points, session CSV, recordings) default to your
Documents folder. You can pick any location in the save dialog.

Calibration sessions and calibration.json are written to:

  %LOCALAPPDATA%\evka_position\

Paste that path into the Explorer address bar to open it.


IF THE APP CLOSES UNEXPECTEDLY
------------------------------
It writes a crash report to:

  %LOCALAPPDATA%\evka_position\crash.log

Please attach that file to any bug report - without it there is usually
nothing to go on.
