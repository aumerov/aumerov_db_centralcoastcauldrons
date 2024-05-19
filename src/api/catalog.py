from fastapi import APIRouter
import sqlalchemy
from src import database as db
from .helper import global_status

router = APIRouter()

##Note from class
# SELECT inv, sku, type, price from potion_catalog
# # Not a table - this is a VIEW
# ### 
# for row in results:
#     catalog.append({}"sku": row.sku, "quantity": row.inventory, ...}) 

# put hardcoded logic in database - not here.

# max 6 potions in catalog

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    print("Catalog called")
    with db.engine.begin() as connection:
        # gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        # num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status() 
        
        query = sqlalchemy.text(f"SELECT * FROM potion_inventory")
        result = connection.execute(query)
        data = result.fetchall()
        # print("Current potion inventory: ", data) 

        columns = [col for col in result.keys()]
        # print("Columns:", columns)

        ### TODO: dynamically change prices here

        catalog = []
        for row in data:
            sku = row[columns.index('sku')]
            name = row[columns.index('name')]
            quantity = row[columns.index('quantity')]
            price = row[columns.index('price')]
            type = [row[columns.index('red_content')], 
                    row[columns.index('green_content')], 
                    row[columns.index('blue_content')], 
                    row[columns.index('dark_content')]]

            if quantity > 0:
                print(f"Selling {quantity} {name}s at {price} gold each.")
                catalog.append({
                    "sku": sku,
                    "name": name,
                    "quantity": quantity,
                    "price": price,
                    "potion_type": type,
                })
                if len(catalog) >= 6:
                    break  

    return catalog

