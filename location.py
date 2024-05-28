import asyncio
import winsdk.windows.devices.geolocation as wdg
import timeit


async def get_coords():
    try:
        locator = wdg.Geolocator()
        locator.desired_accuracy_in_meters = 10  
        locator.report_interval = 0  
        locator.desired_accuracy = wdg.PositionAccuracy.HIGH  
        pos = await locator.get_geoposition_async()
        return [pos.coordinate.latitude, pos.coordinate.longitude]
    except PermissionError:
        print("ERROR: You need to allow applications to access your location in Windows settings")


def generate_google_maps_link(latitude, longitude):
    google_maps_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
    return google_maps_link


def get_location():
    try:
        coords = asyncio.run(get_coords())
        if coords:
            latitude, longitude = coords
            google_maps_link = generate_google_maps_link(latitude, longitude)
            print("Google Maps Link:", google_maps_link)
        else:
            print("ERROR: Unable to get location")
    except PermissionError:
        print("ERROR: You need to allow applications to access your location in Windows settings")


# Função wrapper para medir o tempo de execução
def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped

import geocoder
import webbrowser
import timeit

def get_location():
    start_time = timeit.default_timer()
    
    # Obtém a localização atual usando a API de geolocalização do provedor padrão
    localizacao = geocoder.ip('me')
    
    if localizacao.ok:
        latitude, longitude = localizacao.latlng
        print("Latitude:", latitude)
        print("Longitude:", longitude)
        
        # Cria um link para o Google Maps com as coordenadas
        google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
        print("Link para o Google Maps:", google_maps_url)
        
        # Abre o link no navegador padrão
        webbrowser.open(google_maps_url)
        
        elapsed_time = timeit.default_timer() - start_time
        print("Tempo de execução:", elapsed_time, "segundos")
    else:
        print("Não foi possível obter a localização atual.")

# obter_localizacao_atual()


# Chama a função wrapper com a função a ser testada
wrapped_get_location = wrapper(get_location)

# Mede o tempo de execução
execution_time_sec = timeit.timeit(wrapped_get_location, number=1)

print("Tempo de execução:", "{:.2f}".format(execution_time_sec), "segundos")
