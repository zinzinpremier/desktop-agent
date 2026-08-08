#!/usr/bin/env python3
"""
kdeconnect_sms.py - SMS helper using KDE Connect D-Bus API directly.
No external scripts needed.

Usage:
    python kdeconnect_sms.py received [count]  # Get recent SMS
    python kdeconnect_sms.py send <phone> <message>  # Send SMS
    python kdeconnect_sms.py devices  # List paired devices
"""

import sys
import json
import dbus

def get_kdeconnect_bus():
    """Get KDE Connect D-Bus connection."""
    try:
        return dbus.SessionBus().get_object(
            "org.kde.kdeconnect.daemon",
            "/modules/sms"
        )
    except dbus.DBusException as e:
        print(f"Error: KDE Connect not available or not paired: {e}", file=sys.stderr)
        sys.exit(1)

def list_devices():
    """List all paired devices that support SMS."""
    try:
        daemon = dbus.SessionBus().get_object(
            "org.kde.kdeconnect.daemon",
            "/"
        )
        devices = daemon.devices()
        
        result = []
        for device_id in devices:
            device_obj = dbus.SessionBus().get_object(
                "org.kde.kdeconnect.daemon",
                f"/devices/{device_id}"
            )
            name = str(device_obj.name())
            sms_supported = device_obj.hasPlugin("sms")
            
            if sms_supported:
                result.append({
                    "id": device_id,
                    "name": name,
                    "type": "phone"
                })
        
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"Error listing devices: {e}", file=sys.stderr)
        return []

def get_recent_sms(count=10):
    """Get recent SMS messages from KDE Connect."""
    try:
        sms_module = get_kdeconnect_bus()
        
        # Get conversations (returns array of conversation objects)
        conversations = sms_module.conversations()
        
        messages = []
        for conv in conversations:
            # Each conversation has messages
            conv_messages = conv.get('messages', [])
            for msg in conv_messages[:count]:
                messages.append({
                    'body': msg.get('body', ''),
                    'address': msg.get('address', ''),
                    'date': msg.get('date', 0),
                    'type': msg.get('type', 'inbox'),  # inbox or sent
                    'read': msg.get('read', False)
                })
        
        print(json.dumps(messages[:count], indent=2, ensure_ascii=False))
        return messages
    except Exception as e:
        print(f"Error getting SMS: {e}", file=sys.stderr)
        return []

def send_sms(phone_or_thread, message):
    """Send SMS via KDE Connect."""
    try:
        sms_module = get_kdeconnect_bus()
        
        # Check if it's a thread ID or phone number
        if phone_or_thread.startswith("--thread="):
            thread_id = phone_or_thread.replace("--thread=", "")
            # Reply to existing conversation
            sms_module.replyConversation(thread_id, message)
        else:
            # Send new SMS to phone number
            sms_module.sendSms(phone_or_thread, message)
        
        result = {"success": True, "message": "SMS sent successfully"}
        print(json.dumps(result))
        return True
    except Exception as e:
        error_msg = f"Error sending SMS: {e}"
        print(json.dumps({"success": False, "error": error_msg}), file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "received":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        get_recent_sms(count)
    
    elif command == "send":
        if len(sys.argv) < 4:
            print("Usage: kdeconnect_sms.py send <phone_number> <message>", file=sys.stderr)
            sys.exit(1)
        phone = sys.argv[2]
        message = " ".join(sys.argv[3:])
        send_sms(phone, message)
    
    elif command == "devices":
        list_devices()
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
