import os
import sys
import traci

# Step 1: Pastikan SUMO_HOME sudah terdaftar di environment
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 2: Konfigurasi SUMO
Sumo_config = [
    'sumo-gui',
    '-c', 'emergencykeputih.sumocfg',  # File konfigurasi utama
    '--step-length', '0.05',  # Simulasi berjalan per 0.05 detik
    '--delay', '1000',  # Delay visualisasi (1000 ms)
    '--lateral-resolution', '0.1'
]

# Step 3: Mulai SUMO
traci.start(Sumo_config)

# Step 4: Definisi Variabel dan Traffic Light
# Dictionary yang menentukan fase lampu berdasarkan jalur
desired_phase_mapping = {
    'J1_EW': 0,  # EW (East-West)
    'J1_NS': 2,  # NS (North-South)
}

adjusted_tls = {}  # Menyimpan traffic light yang sudah diubah
step = 0  # Melacak langkah simulasi

# Step 5: Fungsi untuk mendeteksi kendaraan darurat
def get_emergency_vehicle_direction(vehicle_id):
    current_edge = traci.vehicle.getRoadID(vehicle_id).lower()
    print(f"Vehicle {vehicle_id} is on edge {current_edge}")
    if 'e0' in current_edge or 'e1' in current_edge:
        return 'NS'
    elif 'e2' in current_edge or 'e3' in current_edge or 'e4' in current_edge:
        return 'EW'
    else:
        return None

# Step 6: Fungsi untuk menangani kendaraan darurat dan mengatur lampu lalu lintas
def process_emergency_vehicles(desired_phase_mapping, adjusted_tls, step):
    emergency_vehicles = [veh for veh in traci.vehicle.getIDList() if traci.vehicle.getTypeID(veh) == "emergency"]
    active_tls = set()

    for veh in emergency_vehicles:
        direction = get_emergency_vehicle_direction(veh)
        if direction:
            next_tls = traci.vehicle.getNextTLS(veh)
            print(f"next_tls for {veh}: {next_tls}")

            if next_tls:
                tls_info = next_tls[0]
                tlsID, linkIndex, distance, state = tls_info
                tl_key = f"{tlsID}_{direction}"
                desired_phase = desired_phase_mapping.get(tl_key)

                if desired_phase is not None:
                    current_phase = traci.trafficlight.getPhase(tlsID)
                    print(f"TLS {tlsID}, Current phase: {current_phase}, Desired phase: {desired_phase}")
                    active_tls.add(tlsID)

                    if tlsID not in adjusted_tls or adjusted_tls[tlsID] != desired_phase:
                        adjusted_tls[tlsID] = desired_phase  # Simpan fase
                        if current_phase == desired_phase:
                            new_duration = max(20, traci.trafficlight.getPhaseDuration(tlsID) + 10)
                            traci.trafficlight.setPhaseDuration(tlsID, new_duration)
                            print(f"Extended phase {current_phase} of {tlsID} to {new_duration} seconds")
                        else:
                            traci.trafficlight.setPhaseDuration(tlsID, 0.1)
                            print(f"Shortened phase {current_phase} of {tlsID} to 1 second")

    # Reset traffic lights ke normal jika tidak ada kendaraan darurat
    for tlsID in list(adjusted_tls.keys()):
        if tlsID not in active_tls:
            del adjusted_tls[tlsID]
            print(f"Resetting traffic light {tlsID} to normal operation.")

    step += 1
    return step

# Step 7: Loop simulasi
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    step = process_emergency_vehicles(desired_phase_mapping, adjusted_tls, step)

# Step 8: Tutup simulasi
traci.close()
print("Simulation ended successfully.")