import sqlalchemy
from pydantic import BaseModel
from src import database as db

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


# Still hard coded. Returns the current global inventory (rows)
def global_status():
    with db.engine.begin() as connection:
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

    data = result.fetchall() 
    print("Current global inventory: ", data) 

    # Manually build a dictionary. Hard coded for name : quantity
    inventory_dict = {item[1]: item[2] for item in data}

    gold = inventory_dict.get('gold', 0)
    num_red_ml = inventory_dict.get('red_ml', 0)
    num_green_ml = inventory_dict.get('green_ml', 0)
    num_blue_ml = inventory_dict.get('blue_ml', 0)
    num_dark_ml = inventory_dict.get('dark_ml', 0)
    

    return gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml




# Still hard coded. Returns the current potion inventory (rows)   TODO: remove hard coding
def potion_status():
    with db.engine.begin() as connection:
        sql_to_execute = \
            """SELECT * 
            FROM potion_inventory
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

    data = result.fetchall() 
    print("Current potion inventory: ", data)

    # Manually build the dictionary. Hard coded for name : quantity
    inventory_dict = {item[0]: item[2] for item in data}

    # entries will move around based on their value in the database. No hard coding here. TODO: fix (pass in column name and get a list?)
    num_red_potions = inventory_dict.get('red_potion', 0)
    num_green_potions = inventory_dict.get('green_potion', 0)
    num_blue_potions = inventory_dict.get('blue_potion', 0)
    num_dark_potions = inventory_dict.get('dark_potion', 0)

    # print(num_red_potions, num_green_potions, num_blue_potions, num_dark_potions)
    return num_red_potions, num_green_potions, num_blue_potions, num_dark_potions


# returns a dictionary of items, keyed by SKU. Used for wholesale barrel catalog
def itemize(catalog):
    barrel_dict = {}
    for barrel in catalog:
        barrel_dict[barrel.sku] = barrel
    
    return barrel_dict






def capacity_status():
    with db.engine.begin() as connection:
        sql = "SELECT potion_capacity, ml_capacity FROM capacity_inventory"
        res = connection.execute(sqlalchemy.text(sql)).fetchone()
        potion_capacity = int(res[0]) if res else 100
        ml_capacity = int(res[1]) if res else 10000
        print(f"Current potion capacity: {potion_capacity}\nCurrent ml capacity: \t {ml_capacity}")
    return potion_capacity, ml_capacity 