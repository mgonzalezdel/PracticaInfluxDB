import time, random
from influxdb_client_3 import InfluxDBClient3, Point

HOST = 'http://localhost:8181'
TOKEN = 'dummy-token'
DATABASE = 'trafico_raw'
DEVICES = ['router1', 'router2']

def main():
    print('Simulador InfluxDB 3 Core')
    client = InfluxDBClient3(host=HOST, token=TOKEN, database=DATABASE)
    try:
        while True:
            for dev in DEVICES:
                traffic_in = round(random.uniform(50.0, 200.0), 2)
                traffic_out = round(random.uniform(40.0, 180.0), 2)
                lattency = round(random.uniform(5.0, 50.0), 2)

                p = Point('traffic').tag('device', dev) \
                    .field('traffic_in', traffic_in) \
                    .field('traffic_out', traffic_out) \
                    .field('latency', lattency)

                client.write(record=p)
                print(f'[{dev}] IN={traffic_in} Mbps | OUT={traffic_out} Mbps | Latencia={lattency} ms')
            time.sleep(1)
    except KeyboardInterrupt:
        print('Detenido')
    finally:
        client.close()

if __name__ == '__main__':
    main()
