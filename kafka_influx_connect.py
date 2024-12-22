from confluent_kafka import Consumer
from influxdb_client import InfluxDBClient, Point, WriteOptions
import json

# Configuración de Kafka + Topics
TOPIC_SAMBORONDON = 'mediciones_samborondon'
TOPIC_DAULE = 'mediciones_daule'

kafka_conf = {
    'bootstrap.servers': 'localhost:9092', 
    'group.id': 'consumo-group',          
    'auto.offset.reset': 'latest'       
}

consumer = Consumer(kafka_conf)

# Verificar asignacion de los topics
def print_assignment(consumer, partitions):
    print(f"Asignado a las particiones: {partitions}")

consumer.subscribe([TOPIC_SAMBORONDON, TOPIC_DAULE], on_assign=print_assignment)

# Configuración de InfluxDB
url = "http://localhost:8086"
token = "OFZU85EUJ_SiT_yQpWQLRgGNV_X9TXJ0Ejl-w8UnpwgM3hIFIrv3AiiLYqnVuR2BrYraN5YY-vXbwTbAASQLYQ=="
org = "christian"
bucket_samborondon = "med_samborondon"
bucket_daule = "med_daule"

client = InfluxDBClient(url=url, token=token)
write_api_samborondon = client.write_api(write_options=WriteOptions(batch_size=500))
write_api_daule = client.write_api(write_options=WriteOptions(batch_size=500))

try:
    print("Esperando mensajes")

    while True:
        msg = consumer.poll(1.0)  
        if msg is None:
            continue
        if msg.error():
            print(f"Error en Kafka: {msg.error()}")
            continue

        try:
            # Imprime el mensaje recibido
            raw_message = msg.value().decode('utf-8')
            print(f"Mensaje recibido: {raw_message}")

            # Mensaje -> JSON 
            data = json.loads(raw_message)  
            print(f"Mensaje parseado: {data}")

            # Establece bucket y region 
            topic = msg.topic()
            bucket = bucket_samborondon if topic == TOPIC_SAMBORONDON else bucket_daule
            region = "samborondon" if topic == TOPIC_SAMBORONDON else "daule"

            # Validar existencia de consumo y ubicacion en el mensaje
            if "consumo_kwh" in data and "ubicacion" in data:
                lat = float(data["ubicacion"]["latitud"])
                lon = float(data["ubicacion"]["longitud"])
                consumo = float(data["consumo_kwh"])

                # Creacion de registro para influxdb
                point = Point("mediciones") \
                    .tag("region", region) \
                    .tag("ciudad", data.get("ciudad", "desconocida")) \
                    .tag("id_medidor", data["id_medidor"]) \
                    .field("consumo_kwh", consumo) \
                    .field("lat", lat) \
                    .field("lon", lon)

                # Escritura para bucket correspondientes
                if topic == TOPIC_SAMBORONDON:
                    write_api_samborondon.write(bucket=bucket, org=org, record=point)
                else:
                    write_api_daule.write(bucket=bucket, org=org, record=point)

                print(f"Datos insertados: {data} en región {region}, bucket {bucket}")

            else:
                print("Mensaje inválido: Faltan campos clave (consumo_kwh, ubicacion).")

        # Manejo de excepciones
        except json.JSONDecodeError as e:
            print(f"Error al parsear JSON: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")

except KeyboardInterrupt:
    print("Proceso detenido por el usuario.")
finally:
    consumer.close()
    print("Conexión a Kafka cerrada.")
