import paho.mqtt.client as mqtt
import json

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

def get_mqtt_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "JARVIS_TerminalVelocity")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        return client
    except Exception as e:
        print(f"!! [IoT MATRIX]: Failed to connect to Mosquitto broker: {e}")
        return None

def TriggerHardware(device_topic: str, payload: str):
    """
    Publishes an MQTT payload to a specific topic to control local hardware (e.g., ESP32, Solar Array).
    """
    print(f">> [IoT MATRIX]: Attempting to trigger hardware on topic '{device_topic}' with payload '{payload}'...")
    
    client = get_mqtt_client()
    if not client:
        return f"Sir, I could not establish a connection to the local Mosquitto MQTT broker on {MQTT_BROKER}:{MQTT_PORT}."
    
    try:
        # Try to parse the payload as JSON to validate it, though it can be just a raw string
        try:
            # If payload is a JSON string, keep it as is
            json.loads(payload)
            final_payload = payload
        except:
            # If it's just a raw command like "ON", wrap it in JSON just in case, or leave as string
            final_payload = payload
            
        result = client.publish(device_topic, final_payload)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f">> [IoT MATRIX]: Successfully dispatched payload to {device_topic}.")
            return f"Hardware trigger successful. Payload '{payload}' dispatched to '{device_topic}'."
        else:
            return f"Hardware trigger failed with MQTT return code {result.rc}."
            
    except Exception as e:
        return f"An error occurred while publishing to MQTT: {str(e)}"
    finally:
        client.disconnect()
