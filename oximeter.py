#!/usr/bin/env python3
import asyncio
import threading
import queue
import tkinter as tk
from bleak import BleakScanner, BleakClient, AdvertisementData
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

# BLE target and service UUID
FEE0_SVC = "0000fee0-0000-1000-8000-00805f9b34fb"
TARGET = None

# Thread-safe queue for inter-thread communication
data_queue = queue.Queue()

# BLE handling in a background thread
def ble_worker():
    async def run_ble():
        # Find the device by address
        device = await BleakScanner.find_device_by_address(TARGET, timeout=10.0)
        if not device:
            print(f"Device {TARGET} not found.")
            return

        async with BleakClient(device) as client:
            # Discover services and locate the notify characteristic under FEE0
            await client.get_services()
            service = client.services.get_service(FEE0_SVC)
            if not service:
                print("FEE0 service not found.")
                return
            notify_char = next((c for c in service.characteristics if "notify" in c.properties), None)
            if not notify_char:
                print("Notify characteristic not found under FEE0.")
                return

            # Notification callback
            def handle_data(_, data: bytearray):
                chunk = list(data)
                if not chunk:
                    return
                header = chunk[0]
                # Spot-check frame (0xF1)
                if header == 0xF1 and len(chunk) >= 4:
                    bpm   = chunk[1]
                    spo2  = chunk[2]
                    # Send measurement update
                    data_queue.put(("measure", bpm, spo2))
                # Waveform frame (0xF0)
                elif header == 0xF0:
                    for sample in chunk[1:]:
                        data_queue.put(("waveform", sample))

            # Subscribe to notifications
            await client.start_notify(notify_char.uuid, handle_data)

            # Keep running
            await asyncio.Event().wait()

    # Set up and run the BLE asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_ble())

# GUI application using Tkinter and matplotlib
class LiveApp:
    def __init__(self, root):
        self.root = root
        root.title("Live SpO₂ & PPG Monitor")

        # Labels for BPM and SpO₂
        self.bpm_var  = tk.StringVar(value="BPM: --")
        self.spo2_var = tk.StringVar(value="SpO₂: --")
        tk.Label(root, textvariable=self.bpm_var,  font=(None, 16)).pack(pady=5)
        tk.Label(root, textvariable=self.spo2_var, font=(None, 16)).pack(pady=5)

        # Matplotlib figure for waveform
        self.fig = Figure(figsize=(5, 3))
        self.ax  = self.fig.add_subplot(111)
        self.line, = self.ax.plot([], [])
        self.ax.set_ylim(20, 100)
        self.ax.set_xlim(0, 200)
        self.ax.set_title("Plethysmogram (PPG)")
        self.ax.set_xlabel("Sample #")
        self.ax.set_ylabel("Amplitude")

        # Embed in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Buffer for waveform samples
        self.wave_buf = []

        # Start periodic GUI update
        self.update_gui()

    def update_gui(self):
        # Process all queued data
        while not data_queue.empty():
            kind, *vals = data_queue.get()
            if kind == "measure":
                bpm, spo2 = vals
                self.bpm_var.set(f"BPM: {bpm}")
                self.spo2_var.set(f"SpO₂: {spo2}%")
            elif kind == "waveform":
                (sample,) = vals
                self.wave_buf.append(sample)
                # Keep last 200 samples
                if len(self.wave_buf) > 200:
                    self.wave_buf = self.wave_buf[-200:]

        # Update waveform plot
        if self.wave_buf:
            self.line.set_data(range(len(self.wave_buf)), self.wave_buf)
            self.ax.set_xlim(0, max(200, len(self.wave_buf)))
            self.canvas.draw()

        # Schedule next update
        self.root.after(50, self.update_gui)

async def main():
    global TARGET
    # Scan BLE and ask user to select the device
    scanner = BleakScanner()
    discovered = await scanner.discover()
    print(f"Scanning for devices...{len(discovered)} found.")
    # Wait for a few seconds to allow scanning
    time.sleep(5)
    # Show available devices

    if not discovered:
        print("No devices found.")
        exit(1)
    print("Available devices:")
    for i, device in enumerate(discovered):
        print(f"{i}: {device.name} ({device.address})")
    # Ask user to select the device
    selected_device = input("Select device by index: ")
    try:
        selected_device = int(selected_device)
        TARGET = discovered[selected_device].address
        if selected_device < 0 or selected_device >= len(discovered):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        exit(1)


    # Start BLE thread
    ble_thread = threading.Thread(target=ble_worker, daemon=True)
    ble_thread.start()

    # Start GUI
    root = tk.Tk()

    # app
    app = LiveApp(root)
    root.mainloop()


if __name__ == "__main__":
    # Check if running in a terminal
    if not hasattr(tk.Tk, 'mainloop'):
        print("This script requires a GUI environment.")
        exit(1)

    # Run the main function
    asyncio.run(main())