import datetime
import winreg
import json
import socket
import platform
import psutil
import subprocess
from hashlib import md5
# from bson import ObjectId
from uuid import uuid4
import tempfile
import wmi
import geocoder


def get_workstation_domain_wmi():
    c = wmi.WMI()
    for computer in c.Win32_ComputerSystem():
        return computer.Domain
    
def get_location():
    try:
        # Obtém a localização atual usando a API de geolocalização do provedor padrão
        localizacao = geocoder.ip('me')

        if localizacao.ok:
            latitude, longitude = localizacao.latlng
            return {"latitude": latitude, "longitude": longitude}
        else:
            print("Não foi possível obter a localização atual.")
            return None
    except Exception as e:
        print("Ocorreu um erro ao obter a localização:", e)
        return None

def get_hwid():
    # Obtém informações do hardware que podem ser usadas para gerar o HWID
    try:
        # Executa o comando wmic para obter informações do hardware
        wmic_output = subprocess.check_output('wmic csproduct get uuid', shell=True)
        # Converte a saída para uma string decodificada
        wmic_output = wmic_output.decode('utf-8').strip()
        # Calcula o hash MD5 das informações do hardware
        hwid = md5(wmic_output.encode('utf-8')).hexdigest()
        # Convertendo string hwid em um JSON válido
        return hwid
    except Exception as e:
        print("Erro ao obter o HWID:", e)
        return None

def get_device_info():
    c = wmi.WMI()
    
    device_info = {
        "keyboard": {},
        "mouse": {},
        "monitors": []
    }

    try:
        info_teclado = c.Win32_Keyboard()

        if info_teclado:
            for teclado in info_teclado:
                device_info["keyboard"] = {
                    "name": teclado.Name,
                    "description": teclado.Description,
                    "device_id": teclado.DeviceID.split("\\")[-1]
                }

        info_mouse = c.Win32_PointingDevice()

        if info_mouse:
            for mouse in info_mouse:
                device_info["mouse"] = {
                    "name": mouse.Name,
                    "description": mouse.Description,
                    "device_id": mouse.DeviceID.split("\\")[-1]
                }

        info_monitor = c.Win32_DesktopMonitor()
        info_video = c.Win32_VideoController()

        # Se houver informações sobre os monitores, adicione ao objeto de retorno
        if info_monitor:
            c = wmi.WMI(namespace=r"root\wmi")
            query_result = c.query("SELECT * FROM WmiMonitorID")
            for query_result in query_result:
                device_info["monitors"].append({
                    "edid": query_result.InstanceName.split("\\")[1],
                    "resolution": str(info_video[0].CurrentHorizontalResolution) + " x " + str(info_video[0].CurrentVerticalResolution) + " - " + str(info_video[0].MaxRefreshRate) + " Hertz",
                    "gpu": info_video[0].Name,
                    "gpu_id": info_video[0].PNPDeviceID.split("\\")[-1],
                })

    except Exception as e:
        print("Ocorreu um erro ao tentar obter informações sobre os dispositivos:", e)

    return device_info
    
def run_client():
    server_ip = "192.168.0.2"  # Endereço IP do cliente
    server_port = 8080  # Porta para o servidor socket

    # Conexão com o servidor
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    server_port = client.getsockname()[1]

    hwid = get_hwid()        
    uid = read_from_registry() or write_to_regedit(str(uuid4()))
    start_collect(client, {"hwid": hwid, "uid": uid})    

    print("send")
    client.close()

    while True:
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((server_ip, server_port))
            server.listen(1)

            print("Server is waiting for connection...")

            # Aguarda até que uma conexão seja aceita
            client, client_address = server.accept()
            print(f"Connected to client: {client_address}")

            print("Connected to server")
                # Recebe mensagem do servidor
            command = client.recv(1024).decode()
            print("command", command)
            
            # Executa o comando recebido do servidor
            if command.strip().lower() == "shutdown_now":
                print("Recebido comando de desligamento. Desligando a máquina...")
                subprocess.run(["shutdown", "-p"], shell=True)
            elif command.strip().lower() == "get_inventory":
                print("get_inventory")
                start_collect(client, {"hwid": hwid, "uid": uid})
            elif command.strip().lower() == "quit":
                print("saindo...")
                break  # Sai do loop e encerra a conexão com o servidor
            elif command.strip().lower() == "winget_install":
                subprocess.run("powershell -command \"iex ((New-Object System.Net.WebClient).DownloadString('https://aka.ms/install-winget'))\"")
            elif command.strip().lower() == "remove_agent":
                # wmic product where "name='Exemplo'" call uninstall
                subprocess.Popen(["wmic product where name='nameApp' call uninstall"])
            else:
                timeout = command.split("##")[1] if len(command.split("##")) > 1 else 30
                command = command.split("##")[0]

                if "echo" in command:
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.bat') as temp_file:
                        temp_file.write(command)
                        command = temp_file.name

                encoding = "cp850" if platform.system() == "Windows" else "utf_8"
                try:
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, encoding=encoding)
                    # Aguarde até que o processo seja concluído
                    stdout, stderr = process.communicate(timeout=int(timeout))
                    if stdout:
                        # print(stdout)
                        client.sendall(stdout.encode())
                    if stderr:
                        client.sendall(stderr.encode())
                        print("Erro ao executar o comando:", stderr)
                except subprocess.TimeoutExpired:
                    print("Tempo limite excedido ao executar o comando.")
                except Exception as e:
                    print("Erro ao executar o comando:", e)

        except Exception as e:
            print(f"Erro: {e}")
        finally:
            # Fecha a conexão com o cliente
            client.close()
            print("Connection to client closed")

def write_to_regedit(data):
    try:
        # Abrindo a chave do registro
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AgentZer0", 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        # Se a chave não existe, crie-a
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AgentZer0")
    
    value_name = "identity"
    value_type = winreg.REG_SZ
    # Criando uid no campo "identity"
    winreg.SetValueEx(key, value_name, 0, value_type, data)
    winreg.CloseKey(key)
    return data

def read_from_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AgentZer0", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)        
        value, _ = winreg.QueryValueEx(key, "identity")        
        winreg.CloseKey(key)
        
        return value
    except FileNotFoundError:
        return None

# def get_computer_manufacturer():
#     try:
#         key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\HardwareConfig\Current")
#         value, _ = winreg.QueryValueEx(key, "SystemManufacturer")
#         winreg.CloseKey(key)
#         if(value == "Default string"):
#             return "Generic"
#         return value.strip()
#     except Exception as e:
#         print("Erro ao obter o fabricante do computador:", e)
#         return "Not Detected"
    
def get_version_system():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        value = winreg.QueryValueEx(key, "ProductName")[0] 
        winreg.CloseKey(key)
        return value + " x" + platform.machine()[-2:]
    except Exception as e:
        return str(e), None

def categorie_system():
    if(get_version_system().lower() in "server"):
        return "Server"
    elif(psutil.sensors_battery() is not None):
        return "Notebook"
    else:
        return "Desktop"

def get_motherboard():
    try:
        chave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
        fabricante = winreg.QueryValueEx(chave, "BaseBoardManufacturer")[0]
        model = winreg.QueryValueEx(chave, "BaseBoardProduct")[0]
        manufacturer = winreg.QueryValueEx(chave, "SystemManufacturer")[0]
        print()
        return {'motherboard': fabricante, 'model': model, 'manufacturer': manufacturer}
    except Exception as e:
        print("err",e)
        return {'motherboard': "Máquina Virtual Detected", 'model': "Máquina Virtual Detected"}
    

def bytes_para_gb(bytes_valor):
    return round(bytes_valor / (1024 ** 3), 2)

def verify_system(returnValue):
    if(platform.system() == "Windows"):
        return returnValue

def get_cpu_info():
    try:
        # Obter o modelo exato do processador no Windows
        if platform.system() == "Windows":
            process = subprocess.run(['wmic', 'cpu', 'get', 'name'], capture_output=True, text=True, shell=True)
            if process.returncode == 0:
                model = process.stdout.strip().split('\n')[2]
            else:
                raise Exception(process.stderr.strip())

        # Obter informações genéricas sobre a CPU para outros sistemas
        else:
            model = platform.processor()

        return {
            "model": model,
            "architecture": platform.architecture()[0],
            "cpu_freq": psutil.cpu_freq().current,
            "physical_cores": psutil.cpu_count(logical=False),
            "logic_cores": psutil.cpu_count(logical=True)
        }
    except Exception as e:
        return {"Erro": str(e)}

def get_mac_address():
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK and psutil.net_if_stats()[interface].isup:
                    return addr.address
        return None
    except Exception as e:
        print("Erro ao obter o endereço MAC usando psutil:", e)
        return None

def get_memoria_info():
    memoria = psutil.virtual_memory()
    return {
        "total": bytes_para_gb(memoria.total),
        "available": bytes_para_gb(memoria.available),
        "used": bytes_para_gb(memoria.used),
        "percentage": memoria.percent
    }

def get_installed_software():
    software_list = []
    uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key) as key:
            i = 0
            while True:
                subkey_name = winreg.EnumKey(key, i)
                subkey_path = fr"{uninstall_key}\{subkey_name}"
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                        software_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        software_list.append(software_name)
                except FileNotFoundError:
                    pass
                i += 1
    except OSError:
        pass
    return software_list

def get_network(ip):
    return{
        "network": subprocess.run("powershell -Command \"(Get-NetConnectionProfile).Name", capture_output=True, text=True, shell=True).stdout,
        "ipv4": ip,
        "mac": get_mac_address()
    }
def get_so_info():
    return {
        "so": get_version_system(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "type_machine": categorie_system(),
        "hostname": platform.uname().node,
        "domain": get_workstation_domain_wmi(),
        "user_logged": psutil.users()[0].name,
        "last_update": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

def get_disco_info():
    disco = psutil.disk_usage('/')
    return {
        "total": bytes_para_gb(disco.total),
        "used": bytes_para_gb(disco.used),
        "available": bytes_para_gb(disco.free),
        "percentage": disco.percent
    }

def start_collect(client, identifiers):
    data = {
        "inventory": {
            "cpu": get_cpu_info(),
            "memory": get_memoria_info(),
            "system": get_so_info(),
            "storage": get_disco_info(),
            "software": get_installed_software(),
            "motherboard": get_motherboard(),
            "network": get_network(client.getsockname()[0]),
        },
        "location": get_location(),
        "periphericals": get_device_info(),
        "hwid": identifiers["hwid"],
        "uid": identifiers["uid"]
    }

    # print(data)
    client.sendall(json.dumps(data).encode())

run_client()
