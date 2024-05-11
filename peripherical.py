import wmi
import json

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
                    "id": teclado.DeviceID.split("\\")[-1]
                }

        info_mouse = c.Win32_PointingDevice()

        if info_mouse:
            for mouse in info_mouse:
                device_info["mouse"] = {
                    "name": mouse.Name,
                    "description": mouse.Description,
                    "id": mouse.DeviceID.split("\\")[-1]
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

# Chamada da função para obter as informações dos dispositivos
devices = get_device_info()
with open('monitors_info.json', 'w') as file:
    json.dump(devices, file)