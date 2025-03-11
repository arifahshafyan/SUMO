# Step 1: Import modules
import os  # Handle file paths and environment variables
import sys  # Access system functions
import traci  # SUMO TraCI module to control the simulation

# Step 2: Establish SUMO path (SUMO_HOME)
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 3: Define SUMO configuration
sumo_config = [
    'sumo-gui',  # Use SUMO with GUI for visualization
    '-c', 'tracikeputih.sumocfg',  # Configuration file
    '--step-length', '0.1',  # Simulation step in seconds
    '--delay', '100',  # Delay for visualization (100ms)
    '--lateral-resolution', '0.1'  # Improve vehicle lateral movement
]

# Step 4: Start SUMO
traci.start(sumo_config)

# Step 5: Define traffic light parameters
tls_id = "J1"  # Traffic Light System ID for Simpang Lima Keputih
step = 0  # Track simulation steps

# Step 6: Function to get traffic density
def get_traffic_density():
    """
    Menghitung jumlah kendaraan di jalur masuk ke Simpang Lima Keputih.
    """
    lanes = ["-E3", "-E1", "-E4", "-E2", "E0"]  # Jalan utama masuk ke simpang
    traffic_density = {lane: traci.edge.getLastStepVehicleNumber(lane) for lane in lanes}
    return traffic_density

# Step 7: Function to adjust adaptive traffic lights
def adjust_traffic_lights_adaptive(tls_id):
    """
    Menyesuaikan durasi lampu hijau berdasarkan tingkat kepadatan lalu lintas di setiap jalur.
    """
    traffic_density = get_traffic_density()
    max_density_lane = max(traffic_density, key=traffic_density.get)  # Jalur dengan kepadatan tertinggi
    num_vehicles = traffic_density[max_density_lane]

    # Atur durasi lampu hijau berdasarkan kepadatan kendaraan
    if num_vehicles > 20:
        new_duration = 50  # Kemacetan tinggi, perpanjang hijau
        status = f"🔴 Macet di {max_density_lane}, hijau diperpanjang"
    elif num_vehicles > 10:
        new_duration = 40  # Kemacetan sedang, waktu hijau agak panjang
        status = f"🟡 Kemacetan Sedang di {max_density_lane}, hijau normal"
    elif num_vehicles > 5:
        new_duration = 30  # Lalu lintas normal
        status = f"🟢 Lalu lintas lancar di {max_density_lane}, hijau normal"
    else:
        new_duration = 15  # Jalan sepi, perpendek hijau
        status = f"✅ Jalan sepi di {max_density_lane}, hijau diperpendek"

    # Terapkan perubahan ke SUMO
    traci.trafficlight.setPhaseDuration(tls_id, new_duration)
    print(f"STEP {step}: {status} ({num_vehicles} kendaraan)")

# Step 8: Function to regulate vehicle speeds
def regulate_vehicle_speeds():
    """
    Menyesuaikan kecepatan kendaraan agar sesuai aturan lalu lintas.
    """
    for veh_id in traci.vehicle.getIDList():
        current_speed = traci.vehicle.getSpeed(veh_id)
        if current_speed < 5:
            traci.vehicle.setSpeed(veh_id, 10)  # Tingkatkan jika terlalu lambat
        elif current_speed > 15:
            traci.vehicle.setSpeed(veh_id, 15)  # Batasi kecepatan maksimum

# Step 9: Simulation loop
sim_time = 0
max_time = 600  # Simulasi berjalan selama 5 menit

while traci.simulation.getMinExpectedNumber() > 0 and sim_time < max_time:
    traci.simulationStep()
    sim_time += 1

    # Setiap 10 detik, perbarui lampu lalu lintas
    if sim_time % 10 == 0:
        adjust_traffic_lights_adaptive(tls_id)

    # Sesuaikan kecepatan kendaraan
    regulate_vehicle_speeds()

    print(f"Simulation Time: {sim_time}s, Active Vehicles: {len(traci.vehicle.getIDList())}")

# Step 10: End simulation
traci.close()
print("Simulation ended successfully.")