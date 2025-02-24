import bluetooth

def discover_bluetooth_devices():
    print("Searching for Bluetooth devices...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=False)

    if not nearby_devices:
        print("No Bluetooth devices found.")
    else:
        print("Found {} devices.".format(len(nearby_devices)))
        for addr, name in nearby_devices:
            print("  Address: {}, Name: {}".format(addr, name))

if __name__ == "__main__":
    discover_bluetooth_devices()
