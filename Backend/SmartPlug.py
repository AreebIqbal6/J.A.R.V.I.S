import asyncio
import os
from typing import Dict, Any, Optional
from dotenv import dotenv_values, load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
env_path = os.path.join(root_dir, ".env")
env_vars = dotenv_values(env_path)

class KasaPlugControl:
    """
    Direct physical hardware controller for TP-Link Kasa Smart Plug.
    Zero mock, zero virtual simulation.
    """
    _device_state = {"is_on": False, "connected": False, "hardware": "disconnected"}

    def __init__(self, plug_ip: Optional[str] = None):
        self.plug_ip = plug_ip or env_vars.get("SMART_PLUG_IP")
        if not self.plug_ip:
            load_dotenv(env_path)
            self.plug_ip = os.getenv("SMART_PLUG_IP", "192.168.1.100")

    async def get_state(self) -> Dict[str, Any]:
        """Reads current physical hardware state directly."""
        try:
            from kasa import SmartPlug
            plug = SmartPlug(self.plug_ip)
            await asyncio.wait_for(plug.update(), timeout=0.8)
            self._device_state["is_on"] = plug.is_on
            self._device_state["connected"] = True
            self._device_state["hardware"] = "physical"
            return {"ok": True, "data": {"is_on": plug.is_on, "ip": self.plug_ip, "connected": True, "hardware": "physical"}, "error": None}
        except Exception as e:
            self._device_state["connected"] = False
            self._device_state["hardware"] = "disconnected"
            return {"ok": False, "data": {"is_on": False, "ip": self.plug_ip, "connected": False, "hardware": "disconnected"}, "error": f"Physical hardware at {self.plug_ip} unreachable: {e}"}

    async def turn_on(self) -> Dict[str, Any]:
        """Turns on plug and performs state readback verification on physical hardware."""
        try:
            from kasa import SmartPlug
            print(f">> [SMART PLUG]: Sending UDP payload to {self.plug_ip} to turn ON...")
            plug = SmartPlug(self.plug_ip)
            await asyncio.wait_for(plug.update(), timeout=1.0)
            await plug.turn_on()
            await asyncio.wait_for(plug.update(), timeout=1.0)
            if plug.is_on:
                self._device_state["is_on"] = True
                self._device_state["connected"] = True
                return {"ok": True, "data": {"state": "on", "verified": True, "ip": self.plug_ip, "hardware": "physical"}, "error": None}
            else:
                return {"ok": False, "data": None, "error": f"Verification failed: device at {self.plug_ip} is_on is False after turn_on."}
        except Exception as e:
            print(f"!! [SMART PLUG]: Physical device unreachable ({e}).")
            self._device_state["connected"] = False
            return {"ok": False, "data": {"state": "offline", "verified": False, "ip": self.plug_ip, "connected": False}, "error": f"Hardware unreachable at {self.plug_ip}: {e}"}

    async def turn_off(self) -> Dict[str, Any]:
        """Turns off plug and performs state readback verification on physical hardware."""
        try:
            from kasa import SmartPlug
            print(f">> [SMART PLUG]: Sending UDP payload to {self.plug_ip} to turn OFF...")
            plug = SmartPlug(self.plug_ip)
            await asyncio.wait_for(plug.update(), timeout=1.0)
            await plug.turn_off()
            await asyncio.wait_for(plug.update(), timeout=1.0)
            if not plug.is_on:
                self._device_state["is_on"] = False
                self._device_state["connected"] = True
                return {"ok": True, "data": {"state": "off", "verified": True, "ip": self.plug_ip, "hardware": "physical"}, "error": None}
            else:
                return {"ok": False, "data": None, "error": f"Verification failed: device at {self.plug_ip} is_on is True after turn_off."}
        except Exception as e:
            print(f"!! [SMART PLUG]: Physical device unreachable ({e}).")
            self._device_state["connected"] = False
            return {"ok": False, "data": {"state": "offline", "verified": False, "ip": self.plug_ip, "connected": False}, "error": f"Hardware unreachable at {self.plug_ip}: {e}"}
