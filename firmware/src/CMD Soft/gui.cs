using System;
using System.Drawing;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Globalization;
using System.Linq;

namespace CMDScanner
{
    public partial class Form1 : Form
    {
        private const string DefaultStaIp = "192.168.1.84";
        private const string ApFallbackIp = "192.168.1.50";
        private const int DefaultCmdPort = 8080;
        private const string PrefixStaIp = "STA_IP:";
        private const string PrefixSensor = "SENSOR,";
        private const string PrefixSysInfo = "SYSINFO,";
        private const string PrefixAck = "ACK:";
        private const string PrefixErr = "ERR:";
        private const string PrefixXyz = "X";
        private TcpClient _tcpClient;
        private NetworkStream _stream;
        private StreamReader _reader;
        private CancellationTokenSource _cancellationTokenSource;

        private float _lastRawX = 0, _lastRawY = 0, _lastRawZ = 0;
        private float _offsetX = 0, _offsetY = 0, _offsetZ = 0;
        private bool _isRelativeZeroActive = false;

        // Sensor readings
        private float _lastR = 0, _lastTheta = 0, _lastPhi = 0;
        private int _lastValid = 0;
        private long _lastFrame = 0;

        // Min/Max tracking
        private float _minX = float.MaxValue, _maxX = float.MinValue;
        private float _minY = float.MaxValue, _maxY = float.MinValue;
        private float _minZ = float.MaxValue, _maxZ = float.MinValue;

        // System info
        private System.Windows.Forms.Timer _sysInfoTimer;

        // UI controls
        private TextBox txtIp, txtPort, txtSsid, txtPass;
        private Button btnConnect, btnDisconnect, btnMachineZero, btnWorkZeroAll, btnWifiSave, btnWifiForget;
        private Button btnZeroX, btnZeroY, btnZeroZ, btnResetMinMax;
        private Label lblStatus, lblX, lblY, lblZ, lblRouterIpValue;
        private Label lblR, lblTheta, lblPhi, lblValid, lblFrame;
        private Label lblMinX, lblMaxX, lblMinY, lblMaxY, lblMinZ, lblMaxZ;
        private Label lblRssi, lblHeap, lblUptime;

        public Form1()
        {
            BuildUI();

            if (File.Exists("settings.txt"))
            {
                string[] settings = File.ReadAllLines("settings.txt");
                if (settings.Length >= 4)
                {
                    txtIp.Text = settings[0];
                    txtPort.Text = settings[1];
                    txtSsid.Text = settings[2];
                    txtPass.Text = settings[3];
                }
            }

            this.FormClosing += Form1_FormClosing;
        }

        // Retained for compatibility with the original partial WinForms layout pattern.
        // The legacy Designer file is not included in this repository.
        private void InitializeComponent() {}

        #region 1. UI CONSTRUCTION
        private void BuildUI()
        {
            this.Text = "CMDScanner - Industrial Control Panel";
            this.Size = new Size(500, 780);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.Font = new Font("Segoe UI", 10, FontStyle.Regular);
            this.BackColor = Color.FromArgb(240, 244, 249);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;

            int y = 15;

            // --- Connection Group ---
            GroupBox gbConnection = new GroupBox { Text = "Device Connection", Location = new Point(20, y), Size = new Size(445, 80), Font = new Font("Segoe UI", 9, FontStyle.Bold), ForeColor = Color.FromArgb(64, 64, 64) };
            Label lblIp = new Label { Text = "IP:", Location = new Point(15, 33), AutoSize = true, Font = new Font("Segoe UI", 10), ForeColor = Color.Black };
            txtIp = new TextBox { Text = "192.168.1.50", Location = new Point(45, 30), Width = 115, Font = new Font("Segoe UI", 11), BorderStyle = BorderStyle.FixedSingle };
            Label lblPort = new Label { Text = "Port:", Location = new Point(175, 33), AutoSize = true, Font = new Font("Segoe UI", 10), ForeColor = Color.Black };
            txtPort = new TextBox { Text = DefaultCmdPort.ToString(CultureInfo.InvariantCulture), Location = new Point(215, 30), Width = 55, Font = new Font("Segoe UI", 11), BorderStyle = BorderStyle.FixedSingle };

            btnConnect = new Button { Text = "CONNECT", Location = new Point(285, 27), Size = new Size(70, 32), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(39, 174, 96), ForeColor = Color.White, Font = new Font("Segoe UI", 9, FontStyle.Bold) };
            btnConnect.FlatAppearance.BorderSize = 0;
            btnConnect.Click += BtnConnect_Click;

            btnDisconnect = new Button { Text = "DISCONNECT", Location = new Point(360, 27), Size = new Size(70, 32), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(231, 76, 60), ForeColor = Color.White, Font = new Font("Segoe UI", 8, FontStyle.Bold), Enabled = false };
            btnDisconnect.FlatAppearance.BorderSize = 0;
            btnDisconnect.Click += BtnDisconnect_Click;

            gbConnection.Controls.AddRange(new Control[] { lblIp, txtIp, lblPort, txtPort, btnConnect, btnDisconnect });
            y += 85;

            // --- Status ---
            lblStatus = new Label { Text = "Status: Waiting...", Location = new Point(25, y), ForeColor = Color.FromArgb(192, 57, 43), AutoSize = true, Font = new Font("Segoe UI", 10, FontStyle.Bold) };
            y += 25;

            // --- Position Panel ---
            Panel pnlAxes = new Panel { Location = new Point(20, y), Size = new Size(445, 215), BorderStyle = BorderStyle.FixedSingle, BackColor = Color.White };

            lblX = new Label { Text = "X:   0.00 mm", Location = new Point(15, 10), AutoSize = true, Font = new Font("Consolas", 22, FontStyle.Bold), ForeColor = Color.FromArgb(255, 68, 68) };
            lblMinX = new Label { Text = "Min: --", Location = new Point(15, 42), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.Gray };
            lblMaxX = new Label { Text = "Max: --", Location = new Point(130, 42), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.Gray };
            btnZeroX = new Button { Text = "X=0", Location = new Point(360, 12), Size = new Size(65, 32), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(255, 68, 68), ForeColor = Color.White, Font = new Font("Segoe UI", 10, FontStyle.Bold), Enabled = false };
            btnZeroX.FlatAppearance.BorderSize = 0;
            btnZeroX.Click += BtnZeroX_Click;

            lblY = new Label { Text = "Y:   0.00 mm", Location = new Point(15, 60), AutoSize = true, Font = new Font("Consolas", 22, FontStyle.Bold), ForeColor = Color.FromArgb(39, 174, 96) };
            lblMinY = new Label { Text = "Min: --", Location = new Point(15, 92), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.Gray };
            lblMaxY = new Label { Text = "Max: --", Location = new Point(130, 92), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.Gray };
            btnZeroY = new Button { Text = "Y=0", Location = new Point(360, 62), Size = new Size(65, 32), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(39, 174, 96), ForeColor = Color.White, Font = new Font("Segoe UI", 10, FontStyle.Bold), Enabled = false };
            btnZeroY.FlatAppearance.BorderSize = 0;
            btnZeroY.Click += BtnZeroY_Click;

            lblZ = new Label { Text = "Z:   0.00 mm", Location = new Point(15, 110), AutoSize = true, Font = new Font("Consolas", 22, FontStyle.Bold), ForeColor = Color.FromArgb(68, 136, 255) };
            lblMinZ = new Label { Text = "Min: --", Location = new Point(15, 142), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.Gray };
            lblMaxZ = new Label { Text = "Max: --", Location = new Point(130, 142), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.Gray };
            btnZeroZ = new Button { Text = "Z=0", Location = new Point(360, 112), Size = new Size(65, 32), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(68, 136, 255), ForeColor = Color.White, Font = new Font("Segoe UI", 10, FontStyle.Bold), Enabled = false };
            btnZeroZ.FlatAppearance.BorderSize = 0;
            btnZeroZ.Click += BtnZeroZ_Click;

            btnResetMinMax = new Button { Text = "RESET MIN/MAX", Location = new Point(260, 160), Size = new Size(165, 28), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(149, 165, 166), ForeColor = Color.White, Font = new Font("Segoe UI", 8, FontStyle.Bold), Enabled = false };
            btnResetMinMax.FlatAppearance.BorderSize = 0;
            btnResetMinMax.Click += (s, e) => ResetMinMax();

            pnlAxes.Controls.AddRange(new Control[] { lblX, lblMinX, lblMaxX, btnZeroX, lblY, lblMinY, lblMaxY, btnZeroY, lblZ, lblMinZ, lblMaxZ, btnZeroZ, btnResetMinMax });
            y += 220;

            // --- Sensor Readings Group ---
            GroupBox gbSensor = new GroupBox { Text = "Sensor Readings", Location = new Point(20, y), Size = new Size(445, 75), Font = new Font("Segoe UI", 9, FontStyle.Bold), ForeColor = Color.FromArgb(64, 64, 64) };
            lblR = new Label { Text = "R: --", Location = new Point(15, 25), AutoSize = true, Font = new Font("Consolas", 12, FontStyle.Bold), ForeColor = Color.FromArgb(155, 89, 182) };
            lblTheta = new Label { Text = "\u03B8: --", Location = new Point(15, 48), AutoSize = true, Font = new Font("Consolas", 12, FontStyle.Bold), ForeColor = Color.FromArgb(230, 126, 34) };
            lblPhi = new Label { Text = "\u03C6: --", Location = new Point(200, 48), AutoSize = true, Font = new Font("Consolas", 12, FontStyle.Bold), ForeColor = Color.FromArgb(22, 160, 133) };
            lblValid = new Label { Text = "Valid: --", Location = new Point(200, 25), AutoSize = true, Font = new Font("Consolas", 10), ForeColor = Color.DimGray };
            lblFrame = new Label { Text = "Frame: --", Location = new Point(310, 25), AutoSize = true, Font = new Font("Consolas", 10), ForeColor = Color.DimGray };
            gbSensor.Controls.AddRange(new Control[] { lblR, lblTheta, lblPhi, lblValid, lblFrame });
            y += 80;

            // --- Zero Buttons ---
            btnWorkZeroAll = new Button { Text = "Software Zero (All)", Location = new Point(20, y), Size = new Size(215, 45), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(52, 152, 219), ForeColor = Color.White, Font = new Font("Segoe UI", 10, FontStyle.Bold), Enabled = false };
            btnWorkZeroAll.FlatAppearance.BorderSize = 0;
            btnWorkZeroAll.Click += BtnWorkZeroAll_Click;

            btnMachineZero = new Button { Text = "Hardware Zero (Encoder)", Location = new Point(250, y), Size = new Size(215, 45), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(243, 156, 18), ForeColor = Color.White, Font = new Font("Segoe UI", 10, FontStyle.Bold), Enabled = false };
            btnMachineZero.FlatAppearance.BorderSize = 0;
            btnMachineZero.Click += BtnMachineZero_Click;
            y += 55;

            // --- WiFi Settings Group ---
            GroupBox gbWifi = new GroupBox { Text = "WiFi Settings (ESP32 STA)", Location = new Point(20, y), Size = new Size(445, 80), Font = new Font("Segoe UI", 9, FontStyle.Bold), ForeColor = Color.FromArgb(64, 64, 64) };
            Label lblSsid = new Label { Text = "SSID:", Location = new Point(15, 30), AutoSize = true, Font = new Font("Segoe UI", 10), ForeColor = Color.Black };
            txtSsid = new TextBox { Location = new Point(55, 27), Width = 110, Font = new Font("Segoe UI", 11), BorderStyle = BorderStyle.FixedSingle };
            Label lblPass = new Label { Text = "Pass:", Location = new Point(175, 30), AutoSize = true, Font = new Font("Segoe UI", 10), ForeColor = Color.Black };
            txtPass = new TextBox { Location = new Point(215, 27), Width = 95, Font = new Font("Segoe UI", 11), BorderStyle = BorderStyle.FixedSingle, UseSystemPasswordChar = true };

            btnWifiSave = new Button { Text = "SAVE", Location = new Point(320, 25), Size = new Size(55, 27), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.DeepSkyBlue, ForeColor = Color.White, Font = new Font("Segoe UI", 9, FontStyle.Bold), Enabled = false };
            btnWifiSave.FlatAppearance.BorderSize = 0;
            btnWifiSave.Click += BtnWifiSave_Click;

            btnWifiForget = new Button { Text = "FORGET", Location = new Point(380, 25), Size = new Size(55, 27), Cursor = Cursors.Hand, FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(231, 76, 60), ForeColor = Color.White, Font = new Font("Segoe UI", 8, FontStyle.Bold), Enabled = false };
            btnWifiForget.FlatAppearance.BorderSize = 0;
            btnWifiForget.Click += BtnWifiForget_Click;

            lblRouterIpValue = new Label { Text = "Router IP: --", Location = new Point(15, 55), AutoSize = true, Font = new Font("Segoe UI", 9), ForeColor = Color.FromArgb(41, 128, 185) };
            gbWifi.Controls.AddRange(new Control[] { lblSsid, txtSsid, lblPass, txtPass, btnWifiSave, btnWifiForget, lblRouterIpValue });
            y += 85;

            // --- System Info Group ---
            GroupBox gbSys = new GroupBox { Text = "System Info", Location = new Point(20, y), Size = new Size(445, 55), Font = new Font("Segoe UI", 9, FontStyle.Bold), ForeColor = Color.FromArgb(64, 64, 64) };
            lblRssi = new Label { Text = "RSSI: --", Location = new Point(15, 25), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.DimGray };
            lblHeap = new Label { Text = "Heap: --", Location = new Point(140, 25), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.DimGray };
            lblUptime = new Label { Text = "Uptime: --", Location = new Point(280, 25), AutoSize = true, Font = new Font("Consolas", 9), ForeColor = Color.DimGray };
            gbSys.Controls.AddRange(new Control[] { lblRssi, lblHeap, lblUptime });

            this.Controls.AddRange(new Control[] { gbConnection, lblStatus, pnlAxes, gbSensor, btnWorkZeroAll, btnMachineZero, gbWifi, gbSys });

            // System info polling timer
            _sysInfoTimer = new System.Windows.Forms.Timer { Interval = 5000 };
            _sysInfoTimer.Tick += async (s, e) =>
            {
                await SendCommandAsync("SYSINFO");
                await SendCommandAsync("GET_IP");
            };
        }
        #endregion

        #region 2. COMMUNICATION AND ASYNC LOOP
        private async void BtnConnect_Click(object sender, EventArgs e)
        {
            try
            {
                lblStatus.Text = "Status: Connecting...";
                lblStatus.ForeColor = Color.Orange;

                _tcpClient = new TcpClient();
                await _tcpClient.ConnectAsync(txtIp.Text, int.Parse(txtPort.Text));

                _stream = _tcpClient.GetStream();
                _reader = new StreamReader(_stream, Encoding.ASCII);
                _cancellationTokenSource = new CancellationTokenSource();

                lblStatus.Text = "Status: Connected! Data streaming.";
                lblStatus.ForeColor = Color.Green;
                SetControlsEnabled(true);
                _sysInfoTimer.Start();

                _ = ListenAsync(_cancellationTokenSource.Token);
                await SendCommandAsync("GET_IP");
                await SendCommandAsync("SYSINFO");
            }
            catch (Exception ex)
            {
                MessageBox.Show("Connection Error: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                CleanupConnection();
            }
        }

        private async Task ListenAsync(CancellationToken token)
        {
            try
            {
                while (!token.IsCancellationRequested && _tcpClient.Connected)
                {
                    string line = await _reader.ReadLineAsync();

                    if (!string.IsNullOrEmpty(line))
                    {
                        if (line.StartsWith(PrefixStaIp))
                        {
                            string ip = line.Substring(7).Trim();
                            this.Invoke(new Action(() =>
                            {
                                bool notConnected =
                                    ip == "NOT_CONNECTED" ||
                                    ip == "BAGLI_DEGIL";
                                lblRouterIpValue.Text = "Router IP: " + (notConnected ? "Not Connected" : ip);
                            }));
                        }
                        else if (line.StartsWith(PrefixSensor))
                        {
                            if (TryParseSensorLine(line, out float r, out float theta, out float phi, out int valid, out long frame))
                            {
                                _lastR = r; _lastTheta = theta; _lastPhi = phi;
                                _lastValid = valid; _lastFrame = frame;

                                // When software zero is active, R/theta/phi are
                                // re-derived from display XYZ in the XYZ branch to
                                // stay in the same reference frame. Only update from
                                // raw firmware SENSOR data when zero is inactive.
                                bool zeroing = _isRelativeZeroActive;
                                this.Invoke(new Action(() =>
                                {
                                    if (!zeroing)
                                    {
                                        lblR.Text     = $"R: {r,8:F2} mm";
                                        lblTheta.Text = $"\u03B8: {theta,8:F3}\u00B0";
                                        lblPhi.Text   = $"\u03C6: {phi,8:F3}\u00B0";
                                    }
                                    lblValid.Text = $"Valid: {(valid == 1 ? "YES" : "NO")}";
                                    lblFrame.Text = $"Frame: {frame}";
                                }));
                            }
                        }
                        else if (line.StartsWith(PrefixSysInfo))
                        {
                            string[] parts = line.Substring(8).Split(',');
                            if (parts.Length >= 4)
                            {
                                int rssi = int.Parse(parts[0]);
                                long heap = long.Parse(parts[1]);
                                long uptime = long.Parse(parts[2]);

                                long h = uptime / 3600, m = (uptime % 3600) / 60, s = uptime % 60;

                                this.Invoke(new Action(() =>
                                {
                                    lblRssi.Text = $"RSSI: {rssi} dBm";
                                    lblHeap.Text = $"Heap: {heap / 1024} KB";
                                    lblUptime.Text = $"Uptime: {h:D2}:{m:D2}:{s:D2}";
                                }));
                            }
                        }
                        else if (line.StartsWith(PrefixXyz))
                        {
                            if (TryParseXyzLine(line, out float rawX, out float rawY, out float rawZ))
                            {
                                _lastRawX = rawX; _lastRawY = rawY; _lastRawZ = rawZ;

                                float finalX = _isRelativeZeroActive ? (rawX - _offsetX) : rawX;
                                float finalY = _isRelativeZeroActive ? (rawY - _offsetY) : rawY;
                                float finalZ = _isRelativeZeroActive ? (rawZ - _offsetZ) : rawZ;

                                // Min/Max tracking
                                if (finalX < _minX) _minX = finalX; if (finalX > _maxX) _maxX = finalX;
                                if (finalY < _minY) _minY = finalY; if (finalY > _maxY) _maxY = finalY;
                                if (finalZ < _minZ) _minZ = finalZ; if (finalZ > _maxZ) _maxZ = finalZ;

                                this.Invoke(new Action(() =>
                                {
                                    lblX.Text = $"X: {finalX,7:F2} mm";
                                    lblY.Text = $"Y: {finalY,7:F2} mm";
                                    lblZ.Text = $"Z: {finalZ,7:F2} mm";

                                    lblMinX.Text = $"Min: {_minX:F1}";  lblMaxX.Text = $"Max: {_maxX:F1}";
                                    lblMinY.Text = $"Min: {_minY:F1}";  lblMaxY.Text = $"Max: {_maxY:F1}";
                                    lblMinZ.Text = $"Min: {_minZ:F1}";  lblMaxZ.Text = $"Max: {_maxZ:F1}";

                                    // Recompute R/θ/φ from zeroed Cartesian so both
                                    // panels share the same reference frame.
                                    if (_isRelativeZeroActive)
                                    {
                                        float dr, dTheta, dPhi;
                                        CartesianToSpherical(finalX, finalY, finalZ,
                                                             out dr, out dTheta, out dPhi);
                                        lblR.Text     = $"R: {dr,8:F2} mm";
                                        lblTheta.Text = $"\u03B8: {dTheta,8:F3}\u00B0";
                                        lblPhi.Text   = $"\u03C6: {dPhi,8:F3}\u00B0";
                                    }
                                }));
                            }
                        }
                        else if (line.StartsWith(PrefixAck))
                        {
                            this.Invoke(new Action(() =>
                            {
                                lblStatus.Text = "Status: " + line;
                                lblStatus.ForeColor = Color.Green;
                            }));
                        }
                        else if (line.StartsWith(PrefixErr))
                        {
                            this.Invoke(new Action(() =>
                            {
                                lblStatus.Text = "Status: " + line;
                                lblStatus.ForeColor = Color.Red;
                            }));
                        }
                    }
                }
            }
            catch (Exception)
            {
                this.Invoke(new Action(() => CleanupConnection()));
            }
        }

        private async Task SendCommandAsync(string command)
        {
            if (_tcpClient != null && _tcpClient.Connected)
            {
                byte[] data = Encoding.ASCII.GetBytes(command + "\n");
                await _stream.WriteAsync(data, 0, data.Length);
            }
        }

        private static bool TryParseSensorLine(
            string line,
            out float r,
            out float theta,
            out float phi,
            out int valid,
            out long frame)
        {
            r = 0f; theta = 0f; phi = 0f; valid = 0; frame = 0;
            if (!line.StartsWith(PrefixSensor))
            {
                return false;
            }

            string[] parts = line.Substring(PrefixSensor.Length).Split(',');
            if (parts.Length < 5)
            {
                return false;
            }

            return
                float.TryParse(parts[0], NumberStyles.Float, CultureInfo.InvariantCulture, out r) &&
                float.TryParse(parts[1], NumberStyles.Float, CultureInfo.InvariantCulture, out theta) &&
                float.TryParse(parts[2], NumberStyles.Float, CultureInfo.InvariantCulture, out phi) &&
                int.TryParse(parts[3], NumberStyles.Integer, CultureInfo.InvariantCulture, out valid) &&
                long.TryParse(parts[4], NumberStyles.Integer, CultureInfo.InvariantCulture, out frame);
        }

        private static bool TryParseXyzLine(
            string line,
            out float x,
            out float y,
            out float z)
        {
            x = 0f; y = 0f; z = 0f;
            if (!line.StartsWith(PrefixXyz))
            {
                return false;
            }

            string[] parts = line.Split(',');
            if (parts.Length != 3 ||
                parts[0].Length < 2 ||
                parts[1].Length < 2 ||
                parts[2].Length < 2)
            {
                return false;
            }

            return
                float.TryParse(parts[0].Substring(1), NumberStyles.Float, CultureInfo.InvariantCulture, out x) &&
                float.TryParse(parts[1].Substring(1), NumberStyles.Float, CultureInfo.InvariantCulture, out y) &&
                float.TryParse(parts[2].Substring(1), NumberStyles.Float, CultureInfo.InvariantCulture, out z);
        }

        private static void CartesianToSpherical(
            float x, float y, float z,
            out float r, out float theta, out float phi)
        {
            r = (float)Math.Sqrt(x * x + y * y + z * z);
            if (r < 1e-6f) { theta = 0f; phi = 0f; return; }
            theta = (float)(Math.Atan2(y, x) * 180.0 / Math.PI);
            phi   = (float)(Math.Asin(Math.Max(-1.0, Math.Min(1.0, z / r)))
                            * 180.0 / Math.PI);
        }
        #endregion

        #region 3. BUTTON EVENTS
        private void BtnZeroX_Click(object sender, EventArgs e) { _offsetX = _lastRawX; _isRelativeZeroActive = true; ResetMinMax(); }
        private void BtnZeroY_Click(object sender, EventArgs e) { _offsetY = _lastRawY; _isRelativeZeroActive = true; ResetMinMax(); }
        private void BtnZeroZ_Click(object sender, EventArgs e) { _offsetZ = _lastRawZ; _isRelativeZeroActive = true; ResetMinMax(); }

        private void BtnWorkZeroAll_Click(object sender, EventArgs e)
        {
            _offsetX = _lastRawX; _offsetY = _lastRawY; _offsetZ = _lastRawZ;
            _isRelativeZeroActive = true;
            ResetMinMax();
        }

        private async void BtnMachineZero_Click(object sender, EventArgs e)
        {
            DialogResult dr = MessageBox.Show("WARNING: This will reset encoder calibration.\nIs the probe at the mechanical home position?", "Hardware Zero", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (dr == DialogResult.Yes)
            {
                _isRelativeZeroActive = false;
                _offsetX = 0; _offsetY = 0; _offsetZ = 0;
                ResetMinMax();
                await SendCommandAsync("ZERO");
            }
        }

        private async void BtnWifiSave_Click(object sender, EventArgs e)
        {
            if (string.IsNullOrWhiteSpace(txtSsid.Text) || txtPass.Text.Length < 8)
            {
                MessageBox.Show("SSID is required and password must be at least 8 characters.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }
            await SendCommandAsync($"WIFI_SET:{txtSsid.Text},{txtPass.Text}");
            MessageBox.Show("WiFi credentials sent to ESP32. Device will reboot.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
            CleanupConnection();
        }

        private async void BtnWifiForget_Click(object sender, EventArgs e)
        {
            DialogResult dr = MessageBox.Show("This will erase stored WiFi credentials and the device will return to AP-only mode. Continue?", "Forget Network", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (dr == DialogResult.Yes && _tcpClient != null && _tcpClient.Connected)
            {
                await SendCommandAsync("WIFI_SET:,");
                MessageBox.Show("Credentials cleared. Device rebooting. Connect to CMDCNC WiFi.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                CleanupConnection();
            }
        }

        private void BtnDisconnect_Click(object sender, EventArgs e) { CleanupConnection(); }

        private void ResetMinMax()
        {
            _minX = float.MaxValue; _maxX = float.MinValue;
            _minY = float.MaxValue; _maxY = float.MinValue;
            _minZ = float.MaxValue; _maxZ = float.MinValue;
            lblMinX.Text = "Min: --"; lblMaxX.Text = "Max: --";
            lblMinY.Text = "Min: --"; lblMaxY.Text = "Max: --";
            lblMinZ.Text = "Min: --"; lblMaxZ.Text = "Max: --";
        }
        #endregion

        #region 4. CLEANUP AND CONTROL MANAGEMENT
        private void CleanupConnection()
        {
            _sysInfoTimer.Stop();
            _cancellationTokenSource?.Cancel();
            _reader?.Close();
            _stream?.Close();
            _tcpClient?.Close();

            lblStatus.Text = "Status: Disconnected.";
            lblStatus.ForeColor = Color.Red;
            SetControlsEnabled(false);
            lblRouterIpValue.Text = "Router IP: --";
        }

        private void SetControlsEnabled(bool connected)
        {
            btnConnect.Enabled = !connected;
            btnDisconnect.Enabled = connected;
            btnWorkZeroAll.Enabled = connected;
            btnMachineZero.Enabled = connected;
            btnWifiSave.Enabled = connected;
            btnWifiForget.Enabled = connected;
            btnZeroX.Enabled = connected;
            btnZeroY.Enabled = connected;
            btnZeroZ.Enabled = connected;
            btnResetMinMax.Enabled = connected;
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            string[] settings = { txtIp.Text, txtPort.Text, txtSsid.Text, txtPass.Text };
            File.WriteAllLines("settings.txt", settings);
            CleanupConnection();
        }
        #endregion
    }
}
