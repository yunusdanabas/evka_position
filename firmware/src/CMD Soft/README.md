# CMD Soft — Reference Code (NOT compiled)

This folder contains the original firmware and C# GUI provided by the CMD firm.
It is **excluded from the PlatformIO build** via `build_src_filter = -<src/CMD Soft/>` in `platformio.ini` — it uses `ESP32Encoder.h` which is not in our dependencies.

See `docs/CMD_SOFTWARE_INTEGRATION.md` for the quick integration guide.
See `docs/CMD_INTEGRATION_CHANGELOG.md` for full technical rationale and change history.

## Legacy Windows GUI Build (Single-file EXE)

This folder now includes a standalone WinForms project:

- `CMDScanner.csproj`
- `Program.cs`
- `gui.cs`

From this folder, publish a single-file self-contained Windows binary:

```bash
dotnet publish -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true
```

Expected output:

- `bin/Release/net8.0-windows/win-x64/publish/CMDScanner.exe`
