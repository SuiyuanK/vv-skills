# Vivado/Xilinx Windows Cleanup Checklist

Use this checklist as source material for safe plans and inspection scripts. Do not execute destructive actions from this file unless the user explicitly authorizes them.

## Read-only inspection targets

Processes to check:

- `vivado.exe`
- `xsct.exe`
- `xsim.exe`
- `xlicmgr.exe`
- `uninstall.exe`

Common install and residue locations:

- `C:\Xilinx\`
- `%APPDATA%\Xilinx\`
- `%LOCALAPPDATA%\.Xilinx\`
- `%USERPROFILE%\.Xilinx\`
- `C:\Program Files (x86)\Common Files\Xilinx\`

Common official uninstaller pattern:

- `C:\Xilinx\Vivado\<version>\.xinst\xsetup.exe --uninstall`

Common registry keys:

- `HKEY_LOCAL_MACHINE\SOFTWARE\Xilinx`
- `HKEY_CURRENT_USER\SOFTWARE\Xilinx`
- `HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Xilinx`
- `HKEY_CLASSES_ROOT\.xpr`
- `HKEY_CLASSES_ROOT\.xdc`
- `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Xilinx License Manager`

Common environment variables:

- `XILINX_VIVADO`
- `XILINX_PLATFORMS`
- `XILINX_LOCAL_USER_DATA`
- PATH entries containing `Xilinx\Vivado` or `%XILINX_VIVADO%`

## Recommended staged cleanup plan

1. Back up important Vivado projects and license files before uninstall work.
2. Create a system restore point when possible.
3. Close Vivado-related tools and confirm no related process is running.
4. Run the official Vivado uninstaller if its `xsetup.exe --uninstall` entry still exists.
5. Reboot if the uninstaller requests it or if files are locked.
6. Inspect residue folders and report their sizes before deleting them.
7. Export Xilinx-specific registry keys to `.reg` files before deletion or rename.
8. Remove Xilinx/Vivado environment variables and PATH segments only after saving snapshots.
9. Reboot or open a fresh terminal and verify `vivado` resolution and environment variables.

## Destructive actions that require explicit confirmation

- Ending user processes.
- Running `xsetup.exe --uninstall`.
- Deleting any folder under `C:\Xilinx`, `%APPDATA%`, `%LOCALAPPDATA%`, `%USERPROFILE%`, or `Program Files`.
- Running `reg delete`, editing registry in `regedit`, or deleting license-manager service with `sc delete`.
- Changing user-level or machine-level environment variables.
- Disabling antivirus or real-time protection.

## Safer alternatives

- Rename uncertain registry keys with a backup suffix instead of deleting them.
- Move questionable residue folders to a dated quarantine folder instead of deleting immediately.
- Remove PATH entries interactively through Windows environment-variable UI when system PATH is crowded or contains unusual references.
- If the uninstaller is missing, generate a manual plan rather than attempting broad wildcard deletion.
