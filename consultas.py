import time
from influxdb_client_3 import InfluxDBClient3, Point

HOST = 'http://localhost:8181'
TOKEN = 'dummy-token' # Por '--without-auth' en el compose
DATABASE = 'trafico_raw'
DATABASE_DOWN = 'trafico_5m'

client = InfluxDBClient3(host=HOST, token=TOKEN, database=DATABASE)

def consultas_analiticas():
    
    # 1. Campos y dispositivos que aparecen
    print("\n--- 1. Dispositivos disponibles ---")
    q1 = "SELECT DISTINCT device FROM traffic"
    print(client.query(q1).to_pandas())

    print("\n--- 1.2 Campos ---")
    q12 = "SHOW COLUMNS FROM traffic"
    print(client.query(q12).to_pandas())

    # 2. Filtra solo lecturas de router1
    print("\n--- 2. Lecturas de router1 ---")
    q2 = "SELECT * FROM traffic WHERE device = 'router1' LIMIT 5"
    print(client.query(q2).to_pandas())

    # 3. Filtra solo el tráfico de salida de router2
    print("\n--- 3. Tráfico de salida (router2) ---")
    q3 = "SELECT time, traffic_out FROM traffic WHERE device = 'router2' LIMIT 5"
    print(client.query(q3).to_pandas())

    # 4. Media de tráfico entrante del último minuto por router
    print("\n--- 4. Media de tráfico entrante (último minuto) ---")
    q4 = """
        SELECT device, AVG(traffic_in) as avg_in 
        FROM traffic 
        WHERE time >= now() - INTERVAL '1 minute' 
        GROUP BY device
    """
    print(client.query(q4).to_pandas())

    # 5. Latencia máxima por router (últimos 5 minutos)
    print("\n--- 5. Latencia máxima (últimos 5 minutos) ---")
    q5 = """
        SELECT device, MAX(latency) as max_lat 
        FROM traffic 
        WHERE time >= now() - INTERVAL '5 minutes' 
        GROUP BY device
    """
    print(client.query(q5).to_pandas())

    # 6. Diferencia entre tráfico entrante y saliente de router1 (últimos 10s)
    print("\n--- 6. Diferencia IN/OUT router1 (últimos 10s) ---")
    q6 = """
        SELECT time, (traffic_in - traffic_out) AS diff_traffic 
        FROM traffic 
        WHERE device = 'router1' AND time >= now() - INTERVAL '10 seconds'
    """
    print(client.query(q6).to_pandas())

    # 7. Media cada 10 segundos del tráfico total
    print("\n--- 7. Media en ventanas de 10s (DATE_BIN) ---")
    q7 = """
        SELECT 
            DATE_BIN(INTERVAL '10 seconds', time) as time_window, 
            device, 
            AVG(traffic_in + traffic_out) as avg_total 
        FROM traffic 
        GROUP BY time_window, device 
        ORDER BY time_window DESC 
        LIMIT 10
    """
    print(client.query(q7).to_pandas())

    # 9. Media y desviación estándar de latency (últimos 5 mins)
    print("\n--- 9. Media y Desviación estándar de latencia ---")
    q9 = """
        SELECT 
            MEAN(latency) as media_lat, 
            STDDEV(latency) as std_lat 
        FROM traffic 
        WHERE time >= now() - INTERVAL '5 minutes'
    """
    df_stats = client.query(q9).to_pandas()
    print(df_stats)
    
    # 10. Filtrar anomalías: Latencia > Media + 2*Desviación
    print("\n--- 10. Anomalías de latencia (> Media + 2*StdDev) ---")
    # Subconsulta para calcular el umbral dinámico dentro de la misma query
    q10 = """
        SELECT time, device, latency 
        FROM traffic 
        WHERE time >= now() - INTERVAL '5 minutes' 
          AND latency > (
              SELECT AVG(latency) + (2 * STDDEV(latency)) 
              FROM traffic 
              WHERE time >= now() - INTERVAL '5 minutes'
          )
    """
    print(client.query(q10).to_pandas())

def tarea_downsampling():
    """
    8. Task de downsampling continuo.
    Calcula la media cada 5 min y escribe en el bucket trafico_5m.
    Se ejecuta cada 60 segundos por diseño del requerimiento.
    """
    print("\n--- 8. Iniciando Tarea de Downsampling (CTRL+C para salir) ---")
    query_downsample = """
        SELECT 
            DATE_BIN(INTERVAL '5 minutes', time) as time, 
            device, 
            AVG(traffic_in) as traffic_in, 
            AVG(traffic_out) as traffic_out, 
            AVG(latency) as latency 
        FROM traffic 
        WHERE time >= now() - INTERVAL '5 minutes' 
        GROUP BY time, device
    """
    
    try:
        while True:
            t_inicio = time.time()
            df = client.query(query_downsample).to_pandas()
            
            if not df.empty:
                lote_puntos = [ 
                    Point("traffic__5m") \
                    .tag("device", row['device']) \
                    .field("traffic_in", row['traffic_in']) \
                    .field("traffic_out", row['traffic_out']) \
                    .field("latency", row['latency']) \
                    .time(row['time'])
                    for _, row in df.iterrows()
                ]

                client.write(record=lote_puntos)

                t_fin =time.time()
                t_ejecucion = t_fin - t_inicio
                print(f"[{time.strftime('%H:%M:%S')}] Lote agregado en {t_ejecucion:.2f} segundos")
            
            # Duerme 1 minuto
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("Tarea de downsampling detenida.")

if __name__ == '__main__':
    consultas_analiticas()
    # Descomentar para dejar corriendo el servicio de downsampling
    # tarea_downsampling()