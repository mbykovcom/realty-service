from typing import List

from bson import ObjectId
from fastapi import HTTPException
from starlette import status

from models.building import BuildingIn, BuildingOut
from utils.db import building_collection


def create_building(building: BuildingIn) -> BuildingOut:
    """Create a building

    :param building: object BuildingIn with data a building for create
    :return: data the building
    """
    building_db = {}
    try:
        building_db = {'name': building.name, 'description': building.description, 'location': building.location,
                       'square': building.square}
        building_db['_id'] = str(building_collection.insert_one(building_db).inserted_id)
    except BaseException as e:  # If an exception is raised when adding to the database
        print(f'Error: {e}')
        if building_collection:
            building_collection.remove({'_id': building_db['_id']})
    if building_db['_id']:
        return BuildingOut(building_id=str(building_db['_id']), name=building_db['name'],
                           description=building_db['description'], location=building_db['location'],
                           square=building_db['square'])
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to add a building')


def get_buildings() -> List[BuildingOut]:
    """Get buildings

    :return: building list (BuildingOut)
    """
    cursor = building_collection.find()
    buildings = [
        BuildingOut(building_id=str(building['_id']), name=building['name'],
                    description=building['description'], location=building['location'],
                    square=building['square']) for building in cursor]
    if buildings:
        return buildings
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'No buildings have been created')


def get_building(building_id: str) -> BuildingOut:
    """ Get building by a id building

    :param building_id: id building
    :return: data the request
    """

    building = building_collection.find_one({'_id': ObjectId(building_id)})
    if building:
        return BuildingOut(building_id=str(building['_id']), name=building['name'],
                           description=building['description'], location=building['location'],
                           square=building['square'])
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This building ({building_id}) does not '
                                                                            f'exist')


def edit_building(building_id: str, name: str = None, description: str = None, square: float = None) -> BuildingOut:
    """Edit building

    :param building_id: id building
    :param name: new name building
    :param description: new description building
    :param square: square area of the building
    :return: data the building
    """
    building = building_collection.find_one({'_id': ObjectId(building_id)})
    if not building:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This building ({building_id}) does not '
                                                                            f'exist')
    result = 0  # The modified flag
    if name is not None and name != building['name']:
        result = building_collection.update_one({'_id': ObjectId(building_id)},
                                                {'$set': {"name": name}}).modified_count
    if description is not None and description != building['description']:
        result = building_collection.update_one({'_id': ObjectId(building_id)},
                                                {'$set': {"description": description}}).modified_count
    if square is not None and square != building['square']:
        result = building_collection.update_one({'_id': ObjectId(building_id)},
                                                {'$set': {"square": square}}).modified_count
    if result:
        building = building_collection.find_one({'_id': ObjectId(building_id)})
    return BuildingOut(building_id=str(building['_id']), name=building['name'],
                       description=building['description'], location=building['location'],
                       square=building['square'])
