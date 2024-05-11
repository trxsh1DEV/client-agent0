import asyncio
import winsdk.windows.devices.geolocation as wdg


async def get_coords():
    try:
        # Inicializa o Geolocator com configurações para aumentar a precisão
        locator = wdg.Geolocator()
        locator.desired_accuracy_in_meters = 10  # Aumentando a precisão
        locator.report_interval = 0  # Define o intervalo de relatório de localização como 0 para obter a localização mais recente
        locator.desired_accuracy = wdg.PositionAccuracy.HIGH  # Define a precisão desejada como alta
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


get_location()
