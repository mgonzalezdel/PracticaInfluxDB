import time, random, sys
from influxdb3_client import InfluxDBClient3, Point

HOST = 'http://localhost:8181'
TOKEN = ''
DATABASE = 'trafico_raw'
DEVICES = ['router1', 'router2']

def main():
    print('Simulador InfluxDB 3 Core')
    client = InfluxDBClient3(host=HOST, token=TOKEN, database=DATABASE)
    try:
        while True:
            for dev in DEVICES:
                tin = round(random.uniform(50.0, 200.0), 2)
                tout = round(random.uniform(40.0, 180.0), 2)
                lat = round(random.uniform(5.0, 50.0), 2)
                p = Point('traffic').tag('device', dev).field('traffic_in', tin).field('traffic_out', tout).field('latency', lat)
                client.write(record=p)
                print(f'[{dev}] IN={tin} Mbps | OUT={tout} Mbps | Latencia={lat} ms')
            time.sleep(1)
    except KeyboardInterrupt:
        print('Detenido')
    finally:
        client.close()

if __name__ == '__main__':
    main()
