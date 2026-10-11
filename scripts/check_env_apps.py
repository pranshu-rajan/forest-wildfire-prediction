import os
import subprocess
import sys

# 1. Tableau
tab_exe = r"C:\Program Files\Tableau\Tableau Public 2026.2\bin\tabpublic.exe"
print(f"Tableau Public exists: {os.path.exists(tab_exe)} at {tab_exe}", flush=True)

# 2. Check KNIME lnk
lnk_path = r"C:\Users\pranshu\Desktop\KNIME Analytics Platform.lnk"
if os.path.exists(lnk_path):
    print("Found KNIME desktop shortcut!", flush=True)
    cmd = ["powershell", "-NoProfile", "-Command", 
           f"$w = New-Object -ComObject WScript.Shell; $s = $w.CreateShortcut('{lnk_path}'); Write-Output $s.TargetPath"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    knime_path = p.stdout.strip()
    print(f"KNIME TargetPath: {knime_path}", flush=True)
    print(f"KNIME Target exists: {os.path.exists(knime_path)}", flush=True)
else:
    print("No KNIME desktop shortcut found.", flush=True)

# 3. Check installer in Downloads
dl_installer = r"C:\Users\pranshu\Downloads\KNIME 5.12.0 Installer (64bit).exe"
print(f"KNIME Installer exists in Downloads: {os.path.exists(dl_installer)}", flush=True)
