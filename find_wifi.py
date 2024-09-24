import subprocess

def find_current_wifi():
    wifi = subprocess.check_output(['netsh', 'WLAN', 'show', 'interfaces'])
    data = wifi.decode('utf-8')

    network = data.split('\n')
    ssid  = ''
    for line in network:
        if 'SSID' in line:
            print(line)
            ssid = line.split(':')[-1].strip()
            break

    print(ssid)
    return ssid