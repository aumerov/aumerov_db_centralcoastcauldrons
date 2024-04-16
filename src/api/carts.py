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
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    
    # using a global log.txt file to count. Code from Stack Overflow
    with open('src/log.txt','r') as f:
        counter = int(f.read())
        counter += 1 
    with open('src/log.txt','w') as f:
        f.write(str(counter))

    print(counter)
    return {"cart_id": counter}


class CartItem(BaseModel):
    quantity: int





@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection: # SELECT step may be unnecessary
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        data = result.fetchall() 
        num_green_potions = data[0][0]
        print("Table contents: ", data)

        # Still hard coded to green potions
        if item_sku != 'GREEN_POTION_0':
            print("Unsupported Potion type. This will be implemented in a later update.")
            return "Unsupported Potion type. This will be implemented in a later update."
        
        # Limit to one potion at a time? FOR V1 ONLY
        if cart_item.quantity < 0 or cart_item.quantity > 1:
            print("Only accepting orders of one item at a time.")
            return "Only accepting orders of one item at a time."

        # # Check stock
        # if cart_item.quantity > num_green_potions:
        #     print("Insufficient Stock")
        #     return "Insufficient Stock"

    return "OK"





class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):  # still hard coded for part 1
    """ """
    # profit = int(cart_checkout.payment)

    with db.engine.begin() as connection: # SELECT step may be unnecessary. Using to fetch table
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory;
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        data = result.fetchall() 
        num_green_potions = data[0][0]
        gold = data[0][2]

        # Double checking
        if num_green_potions == 0:
            print("Out of potions! Come back later.")
            return "Out of potions! Come back later."


        # UPDATE
        # price still hard coded at 60.
        sql_to_execute = \
            f"""UPDATE global_inventory
            SET num_green_potions = {num_green_potions - 1},
            gold = {gold + 60};
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        # check updated table
        sql_to_execute = \
            """SELECT * 
            FROM global_inventory;
            """
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        data = result.fetchall() 
        print("Checkout Result: ", data) 

    return {"total_potions_bought": 1, "total_gold_paid": 60}
