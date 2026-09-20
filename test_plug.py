import asyncio
from Backend.SmartPlug import TuyaPlugControl

async def test_connection():
    print("====================================")
    print("  TUYA SMART PLUG TCP TEST RUNNER")
    print("====================================")
    print("Initializing local connection...")
    
    plug = TuyaPlugControl()
    
    # Quick sanity check on the keys
    if plug.DEVICE_ID == "YOUR_DEVICE_ID_HERE":
        print("\n[!] WARNING: You have not injected your real Device ID and Local Key into Backend/SmartPlug.py yet!")
        print("Run 'python -m tinytuya wizard' in your terminal to extract your keys first.")
        print("Exiting test.")
        return

    print(f"\nAttempting to connect to IP: {plug.IP_ADDRESS}...")
    
    try:
        status = plug.device.status()
        print(f"\n[+] CONNECTION SUCCESSFUL! Current Status: {status}")
        
        action = input("\nDo you want to test toggling the plug? (ON / OFF / skip): ").strip().lower()
        if action == "on":
            await plug.turn_on()
            print("Action complete.")
        elif action == "off":
            await plug.turn_off()
            print("Action complete.")
            
    except Exception as e:
        print(f"\n[-] CONNECTION FAILED. Error: {e}")
        print("Check your IP Address and Local Key.")

if __name__ == "__main__":
    asyncio.run(test_connection())
