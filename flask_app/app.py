#This flask app is going to orchestrate the request from
# different selling points and direct the request to the POS by managing post request
# Flask can be scalled up to serve several selling points at the same time
#The implementation of MongoDB permits to store the state of the order and the conversation and match it with the POS order id
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import time
load_dotenv()
from pymongo.mongo_client import MongoClient

# Importing calls to the POS
from calls import createOrder, getOrder, getOrders, updateOrder
from intent_identification import get_intent
from update_list_products import get_new_order
from get_price_agents_approach import get_price


app = Flask(__name__)


#DATABASE CONNECTION
MONGO_URI = os.getenv('MONGO_URI')
DB= os.getenv('DB')
client = MongoClient(MONGO_URI)
db = client.get_database(DB)


# Define your API secret token
SECRET_TOKEN = os.getenv('SECRET_TOKEN')

# Function to verify the token
def verify_token(token):
    return token == SECRET_TOKEN

# Function to get the order data with user_id at the point of sale and Authorization token
@app.route('/order', methods=['POST'])
def get_order_data():
    # Check if the request contains the token
    token = request.headers.get('Authorization')
    if not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    #Reaf the order_id from the request
    try:
        order_id = data['order_id']
    except Exception as e:
        print (e)
        return jsonify({'error': 'Invalid data'}), 400
    
    order_id = data.get('order_id')
    #Check if the data contains a specific key
    if not order_id:
        return jsonify({'error': 'Invalid data'}), 400
    
    #Match order id with POS order id  Very important step, the heart of this implementation
    db_records = db.vox_pos

    #Check if the order_id exists in the database
    match = db_records.find_one({'order_id': order_id})
    if not match:
        return jsonify({'error': 'Order not found'}), 404
    #Getting the id of the order in the POS and matching to the current order id in the selling point
    POS_order_id = match['POS_order_id']
    #Call the API to get the current order
    current_order = getOrder(POS_order_id)
    #return a response with the order data
    return jsonify(current_order), 200

# Function to handle the conversation updatin in real time, this is the core function with agents implementation
@app.route('/', methods=['POST'])
def order_listener():
    
    # Check if the request contains the token
    token = request.headers.get('Authorization')
    if not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    # Access the data sent with the POST request
    data = request.json
    # Check if the data contains a specific key
    #chec if one ofthe following keys is not present data 'order_id', 'restaurant', 'language', 'message', 'response'
    if not all(key in data for key in ['order_id', 'restaurant', 'language', 'message', 'response', 'location', 'taxes', 'promotions']):
        return jsonify({'error': 'Invalid data'})
    
    order_id = data['order_id']
    restaurant = data['restaurant']
    language = data['language']
    message = data['message']
    response = data['response']
    location = data['location']
    taxes = data['taxes']
    promotions = data['promotions']
    
    #Get data from db
    db_records = db.vox_pos

    #Check if the order_id exists in the database
    match = db_records.find_one({'order_id': order_id})
    if not match:
        # Create a new order with the api
        empty_cart = []
        POS_order_id = createOrder(empty_cart)

        # Create a new order in mongoDB
        record = {
                "order_id": order_id,
                "POS_order_id": POS_order_id,
                "Restaurant": restaurant,
                "Location": location,
                "Hour": time.time(),
                "Language": language,
                "List_products": [],
                "List_prices": [],
                "List_quantities": [],
                "Taxes": taxes,
                'Promotions': promotions,
                "Total_price": '',
        
                "last_message": message,
                "last_response": response,
                
                "last_message2": "",
                "last_response2":"",
                
                "last_message3": "",
                "last_response3":"" }
        
        db_records.insert_one(record)
    # is not the first message
    else: 
        record = {
                "order_id": order_id,
                "POS_order_id": match['POS_order_id'],
                "Restaurant": match['Restaurant'],
                "Location": match['Location'],
                "Hour": match['Hour'],
                "Language": match['Language'],
                "List_products": match['List_products'],
                "List_prices": match['List_prices'],
                "List_quantities": match['List_quantities'],
                "Taxes": match['Taxes'],
                'Promotions': match['Promotions'],
                "Total_price": match['Total_price'],
        
                "last_message": message,
                "last_response": response,
                
                "last_message2": match['last_message'],
                "last_response2": match['last_response'],
                
                "last_message3": match['last_message2'],
                "last_response3":match['last_response2'] }
         
        #Call for the order data in the POS
        current_order = getOrder(record['POS_order_id'])

        #Initialize the order list and memory
        product_list = []
        prices_list = []
        quantity_list = []
        for order_line in current_order['data']['orderLines']:
            product_list.append(order_line['productId']['value'])
            quantity_list.append(order_line['quantity']['value'])
            prices_list.append(order_line['unitPrice'])
            
        #Update the order in the database
        record['List_products'] = product_list
        record['List_prices'] = prices_list
        record['List_quantities'] = quantity_list

    #Here the agent flow will start
    
    #Intent evaluation  We want to know the intent of the user to know what to do in the flow
    #Using pydantic format and to ensure format stability Output FixingParser
    # Set up a parser + inject instructions into the prompt template.
    conversation = {"user previous message": record['last_message2'],
                    "assistant previous response": record['last_response2'],
                    "user current message": record['last_message'],
                    "assistant current message": record['last_response']}
    
    # Firts GenAi chain with format and fixing parser (very stable, good for production, very low token cost)                    
    intent = get_intent(str(conversation))

    #Know we know what the user wants to do, A) Checkout order, B) Add,remove,update products, C) Other

    if intent == "A":
        pass
        #Intent is checkout order
        # Here a call to lock the order can be done
    
        #Get  a list of the products, prices and quantities of the current order and return order and total price
        if len (record['List_products']) == 0:
            return jsonify({'conversation': "The order is empty"}), 200

        #Formula to calculate the total price (including taxes and promotions from the specific location)
        pre_total_price  = 0
        for n in range(len(record['List_products'])):
            pre_total_price += float(record['List_prices'][n]) * float(record['List_quantities'][n])
        
        subtotal = pre_total_price * (pre_total_price * float (record['Taxes'])) 
        total_price = subtotal - (subtotal * float(record['Promotions']))

        record['Total_price'] = total_price

        #update conversation and return the response
        db_records.update_one({'user_id': order_id}, {"$set": record})
        return jsonify({'conversation': "The total price of the order is: " + str(total_price)}), 200

    #If the intent is to add or remove products
    elif intent == "B":
      
    
        #1.- Second GenAi chain with format and fixing parser to update the list of products and quantities with the conversation(real time)
        list_products, list_ocurrences = get_new_order(str(conversation), str(record['List_products']), str(record['List_quantities']))

        #2,- We need to get the prices of the products to update the order in the POS,
        #the optimal way would be querying an existing catalog to match real POS products
        #In thia case I will use one of my arquitectures deployed for task 1 with KFC MENU

        
        prices_list = []
        index_to_drop = []
        for index, product in enumerate (list_products):
            #Here you can see my implementation og GEMAI Agents for doing RAG one by one of the products and demonstrating i know how to do function calling
            price = get_price(product)
            if price == -1 or price == "-1" or price == "0" or price == 0:
                index_to_drop.append(index)
            
            prices_list.append(price)
        #Dropping the products that are not in the catalog
        list_products = [x for index, x in enumerate(list_products) if index not in index_to_drop]    
        list_ocurrences = [x for index, x in enumerate(list_ocurrences) if index not in index_to_drop]
        prices_list =[x for index, x in enumerate(prices_list) if index not in index_to_drop]  
    
        #3.- Update the listd of products in mongo db and also build the cart for updating the order
        #Build the cart
        cart = []

        for index, product in enumerate(list_products):
            cart.append({'item': product, 'price': prices_list[index], 'qty': list_ocurrences[index]})


        #Update the list of products in the POS
        updateOrder(record['POS_order_id'], cart)

        #update mongo
        record['List_products'] = list_products
        record['List_prices'] = prices_list
        record['List_quantities'] = list_ocurrences

        db_records.update_one({'user_id': order_id}, {"$set": record})
        
        return jsonify({'conversation': "The order has been updated"}), 200

    else:   
        #Intent is other
        #update conversation and return the response
        #restart the loop

        db_records.update_one({'user_id': order_id}, {"$set": record})
        return jsonify({'conversation': "Just a conversation, nothing to update in order"}), 200


#DEFINE A route for checkout
# Define a route and function to handle HTTP GET requests
@app.route('/checkout', methods=['POST'])
def get_checkout():
    # Check if the request contains the token
    token = request.headers.get('Authorization')
    if not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    try:
        order_id = data['order_id']
    except:
        return jsonify({'error': 'Invalid data'}), 400
    
    order_id = data.get('order_id')

    #Check if the data contains a specific key
    if not order_id:
        return jsonify({'error': 'Invalid data'}), 400
    
    #Match order id with POS order id
    db_records = db.vox_pos

    #Check if the order_id exists in the database

    match = db_records.find_one({'order_id': order_id})

    if not match:
        return jsonify({'error': 'Order not found'}), 404
    
    POS_order_id = match['POS_order_id']
    #Call the API to get the current order
    current_order = getOrder(POS_order_id)

    #Initialize the order list and memory
    product_list = []
    prices_list = []
    quantity_list = []

    for order_line in current_order['data']['orderLines']:
        product_list.append(order_line['productId']['value'])
        quantity_list.append(order_line['quantity']['value'])
        prices_list.append(order_line['unitPrice'])
            
    if len (prices_list) == 0:
        return jsonify({'conversation': "The order is empty"}), 200

    #Formula to calculate the total price
    if len (product_list) == 0:
            return jsonify({'conversation': "The order is empty"}), 200
    
    #Formula to calculate the total price

    pre_total_price  = 0
    
    for n in range(len(product_list)):
        pre_total_price += float(prices_list[n]) * float(quantity_list[n])

    taxes =  (pre_total_price * float (match['Taxes'])) 
    subtotal = pre_total_price + taxes
    discounts = (subtotal * float(match['Promotions']))
    total_price = subtotal - discounts
    return jsonify({'product_list': str(product_list),
                    'quantity_list': str(quantity_list),
                    'prices_list': str(prices_list),
                    'subtotal': str(pre_total_price),
                    'taxes': str(taxes),
                    'discounts': str(discounts),
                    'total_price': str(total_price)
                    }), 200


if __name__ == '__main__':
    # Run the Flask app on localhost, port 5000
    app.run(debug=True)

