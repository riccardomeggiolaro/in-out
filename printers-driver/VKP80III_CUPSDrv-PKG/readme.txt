
------------------------------------------------------------------------------------

                  Custom Enginnering S.p.A VKP80III CUPS driver 64bit

------------------------------------------------------------------------------------

Package description:

This is the CUPS printer driver package, containing:

1. Compiled printer drivers for VKP80III printer:
   - rastertoVKP80III

2. Printer driver option setting help files, PPD file
   - VKP80III.ppd.gz

3. setup script dor install the driver and the PPD file

Requirements:

This software requires that the following is present on your computer
the CUPS server & architecure (see www.cups.org)

Install Instructions

To begin using this software, please do the following:

1. Open a shell (bash, etc.)

2. Type ./VKP80III_CUPSDrv-202.sh script

3. Goto http://localhost:631 or use your favorite CUPS admin tool.

4. Add a new printer queue for your model.

5. Print test page and see the result

Driver Option Settings

1. Page Sizes:
   - 50mm/60mm/70mm/80mm/82.5mm * 80mm
   - 50mm/60mm/70mm/80mm/82.5mm * 120mm
   - 50mm/60mm/70mm/80mm/82.5mm * 160mm
   - 50mm/60mm/70mm/80mm/82.5mm * 200mm
   - 50mm/60mm/70mm/80mm/82.5mm Roll
   - ZOOM 50mm/60mm/70mm/80mm/82.5mm * 80mm
   - ZOOM 50mm/60mm/70mm/80mm/82.5mm * 120mm
   - ZOOM 50mm/60mm/70mm/80mm/82.5mm * 160mm
   - ZOOM 50mm/60mm/70mm/80mm/82.5mm * 200mm
   - ZOOM 50mm/60mm/70mm/80mm/82.5mm Roll
   the default page is 80mm * 160mm

 2. Halftoning Algorithm:
  - Accurate
  - Radial
  - WTS
  - Standard

3. Print speed:
   - High Quality
   - Normal
   - HighSpeed
   the default is normal

4. Darkness:
   - -25%
   - -12%
   - 0%
   - +12%
   - +25%
   the default is 0%

5. Paper presentation:
   - 30 mm
   - 40 mm
   - 80 mm
   - 120 mm
   - 160 mm
   - 200 mm
   - 240 mm
   the default value is 40 mm

6. Eject-Retract Timeout 
   - None(Hold in Presentation)
   - Eject after 5 sec
   - Eject after 10 sec
   - Eject after 20 sec
   - Eject after 30 sec
   - Eject after 60 sec
   - Eject after 120 sec
   - Retract after 5 sec
   - Retract after 10 sec
   - Retract after 20 sec
   - Retract after 30 sec
   - Retract after 60 sec
   - Retract after 120 sec
   the default value is None(Hold in Presentation)


7. Countinuos Mode:
   - Off
   - On
   the default value is Off


8. Notch/Black Mark Alignment:
   - Off
   - On
   the default value is Off

9. Print Rotation:
	- Disable
	- Rotation 180

10 After cut:
   - Timeout -> Eject -> Delete current doc.
   - Timeout -> Retract--> Delete current doc.
   - Timeout -> Delete document
   - Presentation -> Eject on new page
   - Presentation -> Retract on new page
   - Presentation -> Wait extraction document
   the default is Eject -> Delete current doc

11. Timeout:
   - 5 sec
   - 10 sec
   - 20 sec
   - 30 sec
   - 40 sec
   - 60 sec
   - 120 sec
   the default is 10 sec

Note about Page To Page (After cut Timeoeout-->):
- Page To Page Option (After cut Timeoeout--> ....) is working only  using USB connection
- Please use the USB direct URI for the printer (e.g. usb://....)




