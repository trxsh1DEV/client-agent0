import nmap
import time

def scan_network(network):
    start_time = time.time()  # Captura o tempo de início da execução do script
    nm = nmap.PortScanner()
    nm.scan(hosts=network, arguments='-T4 -O -F --osscan-limit')
    
    active_devices = []
    for host in nm.all_hosts():
        if nm[host]['status']['state'] == 'up':
            device_info = {'ip': host}
            if 'mac' in nm[host]['addresses']:
                device_info['mac'] = nm[host]['addresses']['mac']
            else:
                device_info['mac'] = 'Não disponível'
            os_matches = nm[host].get('osmatch', [])
            if os_matches:
                device_info['os'] = os_matches[0]['name']
            else:
                device_info['os'] = 'Não disponível'
            if 'tcp' in nm[host]:
                device_info['ports'] = nm[host]['tcp'].keys()
            else:
                device_info['ports'] = 'Não disponível'
            active_devices.append(device_info)
    
    end_time = time.time()  # Captura o tempo de término da execução do script
    execution_time_ms = (end_time - start_time) * 100  # Calcula o tempo de execução em milissegundos
    return active_devices, execution_time_ms

# Exemplo de uso:
# Substitua '192.168.1.0/24' pelo intervalo de IP da sua rede
active_devices, execution_time_ms = scan_network('192.168.0.0/24')
print("Dispositivos ativos na rede:")
for device in active_devices:
    print("IP:", device['ip'])
    print("MAC:", device['mac'])
    print("Sistema Operacional:", device['os'])
    print("Portas abertas:", device['ports'])
    print()

print("Tempo de execução: {:.2f} ms".format(execution_time_ms))  # Imprime o tempo de execução com duas casas decimais