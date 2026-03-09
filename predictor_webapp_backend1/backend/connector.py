import asyncio
import httpx
from datetime import datetime
from bleak import BleakScanner, BleakClient

# --- 1. IMPORT YOUR SCHEMAS ---
# Assuming schemas.py is in the same directory
from schemas import MetricInput

FLASK_API_URL = "http://127.0.0.1:5000/api/live_vitals"
DEVICE_CONFIGS = [
    {"name": "h6m 49836", "athlete_id": "1"},
    {"name": "h6m 49850", "athlete_id": "2"},
    {"name": "h6m 49838", "athlete_id": "3"}
]
LOG_INTERVAL = 180  # 3 minutes (180 seconds)
TRIAL_DURATION = 5400  # 90 minutes (5400 seconds)

# Standard Heart Rate Characteristic UUID
HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


buffers = {cfg["athlete_id"]: [] for cfg in DEVICE_CONFIGS}

def classify_fatigue(bpm):
    if bpm <= 100:
        return "Not Fatigued"
    elif 101 <= bpm <= 140:
        return "Moderate"
    else:
        return "Fatigued"

def parse_heart_rate(data):
    """
    Extracts BPM from the Coospo H6 signal based on GATT flags.
    """
    flags = data[0]
    is_16_bit = flags & 0x01
    if is_16_bit:
        return int.from_bytes(data[1:3], byteorder='little')
    else:
        return data[1]

def make_notification_handler(athlete_id):
    def handler(sender, data):
        bpm = parse_heart_rate(data)
        buffers[athlete_id].append(bpm)
        fatigue_status = classify_fatigue(bpm)
        # Store latest status for each athlete
        if not hasattr(handler, "latest_status"):
            handler.latest_status = {}
        handler.latest_status[athlete_id] = (bpm, fatigue_status)
        # Build output for all athletes
        output = ""
        for aid in sorted(buffers.keys()):
            if aid in handler.latest_status:
                bpm_val, status_val = handler.latest_status[aid]
                output += f"Athlete {aid} | Live Signal: {bpm_val} BPM | Status: {status_val}\n"
            else:
                output += f"Athlete {aid} | Live Signal: -- BPM | Status: --\n"
        # Clear terminal and print
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        print(output, end="")
    return handler

async def send_to_backend():
    """
    Background loop that averages and POSTs data to your Flask server.
    """
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(LOG_INTERVAL)
            for cfg in DEVICE_CONFIGS:
                athlete_id = cfg["athlete_id"]
                buffer = buffers[athlete_id]
                if buffer:
                    avg_bpm = round(sum(buffer) / len(buffer))
                    fatigue_status = classify_fatigue(avg_bpm)
                    print(f"\n[STATUS] Athlete {athlete_id}: {fatigue_status} (Avg BPM: {avg_bpm})")
                    if avg_bpm > 140:
                        print(f"\n[FATIGUE ALERT] Athlete {athlete_id} likely fatigued! Avg BPM: {avg_bpm}")

                    try:
                        metric_data = MetricInput(
                            athlete_id=athlete_id,
                            bpm=avg_bpm,
                            hrv=0.0,
                            rmssd=0.0
                        )
                        response = await client.post(
                            FLASK_API_URL,
                            json=metric_data.model_dump()
                        )
                        if response.status_code == 201 or response.status_code == 200:
                            print(f"\n[SYNCED] Avg {avg_bpm} BPM for Athlete {athlete_id} saved.")
                        else:
                            print(f"\n[ERROR] Backend rejected data: {response.status_code}")
                    except Exception as e:
                        print(f"\n[SCHEMA ERROR] Data failed validation or connection: {e}")

                    buffers[athlete_id] = []

async def run_connector():
    print("--- SYNQ Connector: Initializing Multiple Athletes ---")
    print("Scanning for Coospo H6 devices...")

    # Find all devices
    found_devices = {}
    for cfg in DEVICE_CONFIGS:
        device = await BleakScanner.find_device_by_filter(
            lambda d, ad, name=cfg["name"]: d.name and name in d.name.lower()
        )
        if device:
            found_devices[cfg["athlete_id"]] = device
        else:
            print(f"COOSPO H6 ({cfg['name']}) NOT FOUND. Ensure:")
            print("1. Strap pads are wet. 2. Bluetooth Dongle is plugged in. 3. Phone Bluetooth is OFF.")

    if not found_devices:
        print("No devices found. Exiting.")
        return

    # Start clients for all found devices
    clients = {}
    for athlete_id, device in found_devices.items():
        clients[athlete_id] = BleakClient(device)
    # Connect all clients
    await asyncio.gather(*(client.connect() for client in clients.values()))
    for athlete_id, client in clients.items():
        device = found_devices[athlete_id]
        print(f"CONNECTED: {device.name} [{device.address}] as Athlete {athlete_id}")
        await client.start_notify(HR_UUID, make_notification_handler(athlete_id))

    print(f"Commencing 90-minute trial at {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)

    # Start the 3-minute averaging & POST task in the background
    sync_task = asyncio.create_task(send_to_backend())

    try:
        await asyncio.sleep(TRIAL_DURATION)
        print("\nTrial Duration Reached (90 Minutes).")
    except asyncio.CancelledError:
        pass
    finally:
        sync_task.cancel()
        await asyncio.gather(*(client.stop_notify(HR_UUID) for client in clients.values()))
        await asyncio.gather(*(client.disconnect() for client in clients.values()))
        print("Session disconnected safely.")

def classify_fatigue(bpm):
    if bpm <= 100:
        return "Not Fatigued"
    elif 101 <= bpm <= 140:
        return "Moderate"
    else:
        return "Fatigued"

if __name__ == "__main__":
    try:
        asyncio.run(run_connector())
    except KeyboardInterrupt:
        print("\nTrial stopped manually by supervisor.")