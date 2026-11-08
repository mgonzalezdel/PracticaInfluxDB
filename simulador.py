import time
import random
from influxdb_client_3 import InfluxDBClient3, Point

HOST = "http://localhost:8086"
TOKEN = "EFWerM3TXUxogUZ78D1AL_dqC4RNJhIkvO1DhSJkXT40DMWtZfVsvOWbZ0ilKCIxQHU_1S7YZewNMEdhxvL_VQ=="
ORG = "iespsur"
DATABASE = "trafico_raw"

DEVICES = ["router1", "router2"]

print("Ingestando telemetría de red ({', '.join(DEVICES)}) en la base de datos '{DATABASE}'...")

client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG, database=DATABASE)

try:
    while True:
        for dev in DEVICES:

            traffic_in = round(random.uniform(50.0, 200.0), 2)
            traffic_out = round(random.uniform(40.0, 180.0), 2)
            latency = round(random.uniform(5.0, 50.0), 2)
            
            p = (Point("traffic") \
                .tag("device", dev) \
                .field("traffic_in", traffic_in) \
                .field("traffic_out", traffic_out) \
                .field("latency", latency))
            
            client.write(p)
            print(f"[{dev}] Ingestado -> IN: {traffic_in} Mbps | OUT={traffic_out} Mbps | Latencia: {latency} ms")

        time.sleep(1) # Cada segundo

except KeyboardInterrupt:
    print("\n Simulación detenida por el usuario.")
    client.close()