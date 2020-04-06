from geopy.distance import geodesic

from db.building import get_building
from models.building import Coordinates


def check_location(building_id: str, user_location: Coordinates) -> bool:
    """Check the user's location

    :param building_id: id of the building where it is registered
    :param user_location: user's location
    :return: True - access, False - no access
    """
    building = get_building(building_id)
    distance = geodesic(building.location, user_location).m
    if distance <= 100:
        return True
    else:
        return False
