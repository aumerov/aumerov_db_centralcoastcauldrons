from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
import os
from .helper import global_status, potion_status

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print("Visited today: ", customers)

    return "OK"



### Keeping track of adventurers as well as creating carts.
@router.post("/")
def create_cart(new_customer: Customer): # renamed from new_cart becuase that made no sense
    """ """
    print("Create_cart called by: ", new_customer)
    with db.engine.begin() as connection:

        # if adventurer already exists
        sql_to_execute = """
            SELECT adventurer_id 
            FROM adventurers 
            WHERE name = :name 
            AND character_class = :character_class 
            AND level = :level
        """
        result = connection.execute(sqlalchemy.text(sql_to_execute), {
            'name': new_customer.customer_name, 
            'character_class': new_customer.character_class, 
            'level': new_customer.level
        }).fetchone()

        # if not, create one 
        if result is None:
            print("New customer!")
            sql_to_execute = """
                INSERT INTO adventurers (name, character_class, level)
                VALUES (:name, :character_class, :level)
                RETURNING adventurer_id
            """
            result = connection.execute(sqlalchemy.text(sql_to_execute), {
                'name': new_customer.customer_name, 
                'character_class': new_customer.character_class, 
                'level': new_customer.level
            }).fetchone()

        # create new cart, tied to adventurer        # HARD CODED WOW sorry it wasn't working any other way, the type errors were insane
        adventurer_id_str = str(result).strip('(),')
        adventurer_id = int(adventurer_id_str)
        print("Adventurer id: ", adventurer_id)

        sql_to_execute = "INSERT INTO carts (adventurer_id) VALUES (:adventurer_id) RETURNING cart_id"
        cart_result = connection.execute(sqlalchemy.text(sql_to_execute), {'adventurer_id': adventurer_id}).fetchone()

        cart_id_str = str(cart_result).strip('(),')
        cart_id = int(cart_id_str)
        print("Cart id: ", cart_id)

        return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int






@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    if cart_item.quantity == 0: # double check
        return "OK"

    with db.engine.begin() as connection:
        # gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
        # num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status() 
        
        query = sqlalchemy.text(f"SELECT * FROM potion_inventory")
        result = connection.execute(query)
        data = result.fetchall()
        print("Current potion inventory: ", data) 

        columns = [col for col in result.keys()]
        print("Columns:", columns)

        for row in data:
            quantity = row[columns.index('quantity')]
            price = row[columns.index('price')]
            sku = row[columns.index('sku')]
            print(f"Inventory item: SKU {sku}, Quantity {quantity}, Price {price}")

            if item_sku == sku: # item to add to cart
                if (cart_item.quantity > quantity) or (quantity == 0):
                    print("Insufficient Stock.")
                    return "Insufficient Stock."
                
                # add to cart_items
                sql_to_execute = """
                    INSERT INTO cart_items (cart_id, sku, quantity, current_price)
                    VALUES (:cart_id, :sku, :quantity, :current_price)
                """
                result = connection.execute(sqlalchemy.text(sql_to_execute), {
                    'cart_id': cart_id, 
                    'sku': sku, 
                    'quantity': cart_item.quantity,
                    'current_price': price
                })
                break
    return "OK"





class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # profit = int(cart_checkout.payment)    # NOT what this is
    print(f"Checkout called for cart_id {cart_id}.")
    with db.engine.begin() as connection:

        # Retrieve cart items
        sql_to_execute = """
            SELECT sku, quantity, current_price
            FROM cart_items
            WHERE cart_id = :cart_id
        """
        cart_items = connection.execute(sqlalchemy.text(sql_to_execute), {'cart_id': cart_id}).fetchall()
        print("Cart: ", cart_items)


        # Update potion inventory and calculate total cost
        total_cost = 0 # keep track locally
        total_quantity = 0
        for item in cart_items:   # TODO: do this better, call once instead of in the loop.
            purchase_quantity = item.quantity
            purchase_price = item.current_price
            sku = item.sku

            # Check potion inventory
            sql_to_execute = """
                SELECT quantity
                FROM potion_inventory
                WHERE sku = :sku
            """
            potion = connection.execute(sqlalchemy.text(sql_to_execute), {'sku': sku}).fetchone()
            # print("Potion: ", potion, type(potion))
            inventory_stock = 0
            if potion is not None:
                inventory_stock = potion[0]
                # print(inventory_stock)

            if inventory_stock < purchase_quantity:
                return "Insufficient stock for potion."
            
            total_quantity += purchase_quantity
            total_cost += purchase_price * purchase_quantity

            # Update potion inventory
            sql_to_execute = sqlalchemy.text("""
                UPDATE potion_inventory
                SET quantity = quantity - :quantity
                WHERE sku = :sku
            """)
            connection.execute(sql_to_execute, {'quantity': item.quantity, 'sku': sku})



        # if total_cost != profit: # double check everything matches
        #     print("ERROR, mismatch between gold received and calculated cost.")
        #     print(f"Received {profit} gold, calculated cost was {total_cost} gold.")

        # Update global inventory for gold
        sql_to_execute = sqlalchemy.text("""
            UPDATE global_inventory
            SET quantity = quantity + :profit
            WHERE name = 'gold'
        """)
        connection.execute(sql_to_execute, {'profit': total_cost})

    return {"total_potions_bought": total_quantity, "total_gold_paid": total_cost}















    #     gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = global_status() 
    #     num_red_potions, num_green_potions, num_blue_potions, num_dark_potions = potion_status() 


    #     # UPDATE
    #     # price still hard coded at 50/60/80 for R/G/B. Assuming we sold 1 red potion
    #     sql_to_execute = \
    #         f"""UPDATE global_inventory
    #         SET num_red_potions = {num_red_potions - 1},
    #         gold = {gold + 50};
    #         """
    #     result = connection.execute(sqlalchemy.text(sql_to_execute))

    #     # check updated table
    #     global_status() 

    # return {"total_potions_bought": 1, "total_gold_paid": 60}
