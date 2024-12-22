import time
import random
import json
from kafka import KafkaProducer

# Configuraciones de Kafka
KAFKA_BROKER = 'localhost:9092'  
TOPIC_SAMBORONDON = 'mediciones_samborondon'
TOPIC_DAULE = 'mediciones_daule'

# Configuración del Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Cabecera Cantonal Sambo
SAMBORONDON_COORDS_1 = {
    'lat_min': -1.9650, 'lat_max': -1.9550,  
    'lon_min': -79.7325, 'lon_max': -79.7220  
}

# Inicio Via-Entrerios
SAMBORONDON_COORDS_2 = {
    'lat_min': -2.1550, 'lat_max': -2.1245,  
    'lon_min': -79.8700, 'lon_max': -79.8600  
}

# Isla Mocoli
SAMBORONDON_COORDS_3 = {
    'lat_min': -2.112, 'lat_max': -2.0920,  
    'lon_min': -79.8640, 'lon_max': -79.8555  
}

# Plaza Lagos - Batan
SAMBORONDON_COORDS_4 = {
    'lat_min': -2.1050, 'lat_max': -2.0700,
    'lon_min': -79.8800, 'lon_max': -79.8710  
}

#Puente Nuevo - Bellagio
SAMBORONDON_COORDS_5 = {
    'lat_min': -2.1280, 'lat_max': -2.1070,  
    'lon_min': -79.8725, 'lon_max': -79.8690 
}

# Este Via
SAMBORONDON_COORDS_6 = {
    'lat_min': -2.0770, 'lat_max': -2.0700,  
    'lon_min': -79.8600, 'lon_max': -79.8300 
}

# Cabecera Cantonal Daule
DAULE_COORDS = {
    'lat_min': -1.8700, 'lat_max': -1.8500,
    'lon_min': -79.9800, 'lon_max': -79.9675
}

# Faltante Cabecera
DAULE_COORDS_2 = {
    'lat_min': -1.877, 'lat_max': -1.868,  
    'lon_min': -79.9900, 'lon_max': -79.9795 
}

#Urbanizaciones + Aurora
DAULE_COORDS_3 = {
    'lat_min': -2.0525, 'lat_max': -2.0250,  
    'lon_min': -79.9236, 'lon_max': -79.8733 
}

# Generación de coordenadas 
def generate_coordinates(region):
    if region == "Samborondon":
        coords = random.choice([SAMBORONDON_COORDS_1, SAMBORONDON_COORDS_2, SAMBORONDON_COORDS_3, SAMBORONDON_COORDS_4, SAMBORONDON_COORDS_5, SAMBORONDON_COORDS_6])  
        lat = random.uniform(coords['lat_min'], coords['lat_max'])
        lon = random.uniform(coords['lon_min'], coords['lon_max'])
    elif region == "Daule":
        coords = random.choice([DAULE_COORDS, DAULE_COORDS_2, DAULE_COORDS_3])
        lat = random.uniform(coords['lat_min'], coords['lat_max'])
        lon = random.uniform(coords['lon_min'], coords['lon_max'])
    else:
        raise ValueError("Región desconocida")
    
    return lat, lon

# Genera información inicial de un medidor
def generate_initial_data(medidor_id):
    region = random.choice(["Samborondon", "Daule"])
    lat, lon = generate_coordinates(region)
    return {
        "region": region,
        "ubicacion": {"latitud": lat, "longitud": lon},
        "id_medidor": medidor_id
    }

# Genera la informacion de consumo y timestamp x segundo
def generate_data(medidor_info):
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "consumo_kwh": round(random.uniform(0.1, 500.0), 2),
        "id_medidor": medidor_info["id_medidor"],
        "region": medidor_info["region"],
        "ubicacion": medidor_info["ubicacion"]
    } 

def main():
    # Genera los 1000 medidores
    medidores = [f"medidor_{i}" for i in range(1, 1001)]
    medidor_data = {} 

    # Invoca la funcion para generar la region y coordenadas para cada medidor
    for medidor_id in medidores:
        medidor_data[medidor_id] = generate_initial_data(medidor_id)

    try:
        while True:
            for medidor_id in medidores:
                #Invoca la funcion para  generar la información del consumo y timestamp actual por cada medidor
                data = generate_data(medidor_data[medidor_id])

                # Segregación de datos hacia Kafka x region
                if data["region"] == "Samborondon":
                    producer.send(TOPIC_SAMBORONDON, value=data)
                elif data["region"] == "Daule":
                    producer.send(TOPIC_DAULE, value=data)

                print(f"Enviado a {data['region']}: {json.dumps(data)}")
            time.sleep(1)  
    except KeyboardInterrupt:
        print("Simulador detenido.")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
