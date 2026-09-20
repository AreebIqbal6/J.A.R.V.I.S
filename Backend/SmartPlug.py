import tinytuya
import asyncio

class TuyaPlugControl:
    def __init__(self):
        # PLACEHOLDERS: Extract these later using `python -m tinytuya wizard`
        self.DEVICE_ID = "YOUR_DEVICE_ID_HERE"
        self.IP_ADDRESS = "YOUR_PLUG_IP_HERE"
        self.LOCAL_KEY = "YOUR_LOCAL_KEY_HERE"
        self.VERSION = 3.3  # usually 3.3 or 3.1
        
        # Initialize the Tuya Device
        self.device = tinytuya.OutletDevice(
            dev_id=self.DEVICE_ID,
            address=self.IP_ADDRESS,
            local_key=self.LOCAL_KEY,
            version=self.VERSION
        )
        
    async def turn_on(self):
        try:
            print(">> [SMART PLUG]: Sending TCP payload to turn ON...")
            self.device.turn_on()
            return "Appliance turned on successfully."
        except Exception as e:
            print(f"!! [SMART PLUG] Error turning on: {e}")
            return f"Failed to turn on appliance: {e}"

    async def turn_off(self):
        try:
            print(">> [SMART PLUG]: Sending TCP payload to turn OFF...")
            self.device.turn_off()
            return "Appliance turned off successfully."
        except Exception as e:
            print(f"!! [SMART PLUG] Error turning off: {e}")
            return f"Failed to turn off appliance: {e}"
