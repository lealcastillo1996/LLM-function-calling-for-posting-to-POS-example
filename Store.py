#This is the app for simulating the flow at the sales point of a fast food restaurant

import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()
import requests
import random
import string
import time

from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

llm = ChatOpenAI()
prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            """"You are a drive-through assistant. 
                The customer wants to order a meal, repeat the order and ask if they want anything else. 
                If the customer doesn't have any more orders or wants to checkout, ask them to drive to the next window. Dont invent an order if the customer hasn't given one."""
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
)

# Define the URL of your Flask application
url = 'http://127.0.0.1:5000'
# Define the secret token
SECRET_TOKEN = os.getenv('SECRET_TOKEN')

#Function to read the response of the API
def read_response(response):
    for order_line in response['data']['orderLines']:
        product = order_line['productId']['value']
        quantity = order_line['quantity']['value']
        price = order_line['unitPrice']
        print(f"Product: {product}, Quantity: {quantity}, Price: {price}")

#Function to generate a random string for security auth with the app, this can be upgraded if security is a concern
def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

#Function to make a post request to the API and see the state of an order by ID
def make_post_request(order_id):
    try:
        headers_edited = {'Authorization': SECRET_TOKEN, 'Content-Type': 'application/json' }  # Make sure to replace 'SECRET_TOKEN' with your actual token
        url_edited = f'{url}/order'  # Replace with your actual URL
        data_edited = {
            'order_id': str(order_id)
                }
        response = requests.post(url_edited, json=data_edited,  headers=headers_edited,)
        #if the response is not 200, return the error message
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}"
        response = response.json()
        # if the response is not 200, return the error message
        order_list = []

        for order_line in response['data']['orderLines']:
            product = order_line['productId']['value']
            quantity = order_line['quantity']['value']
            price = order_line['unitPrice']
            order_list.append({'product': product, 'quantity': quantity, 'price': price})
    
        return str(order_list)
    
    except Exception as e:
        return str(e)
    
#Function to make a checkout request to the API and see the state of an order by ID
def make_checkout_request(order_id, taxes, promotions):
    try:
        headers_edited = {'Authorization': SECRET_TOKEN, 'Content-Type': 'application/json' }  # Make sure to replace 'SECRET_TOKEN' with your actual token
        url_edited = f'{url}/order'  # Replace with your actual URL
        data_edited = {
            'order_id': str(order_id)
                }
        response = requests.post(url_edited, json=data_edited,  headers=headers_edited,)

        #if the response is not 200, return the error message
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}"
        
        response = response.json()
        # if the response is not 200, return the error message
        order_list = []
        sum = 0
        build_str = ""
        for order_line in response['data']['orderLines']:
            product = order_line['productId']['value']
            quantity = order_line['quantity']['value']
            price = order_line['unitPrice']
            order_list.append({'product': product, 'price': price, 'quantity': quantity, 'total': price * quantity})
            build_str = build_str + f"""Product: {product}, Quantity: {quantity}, Price: {price}; \n""" 
            sum += price * quantity

        #Building the ticket
        taxes =  (sum * taxes) 
        subtotal = sum + taxes
        discounts = (subtotal * promotions)
        total_price = subtotal - discounts
        order_list.append({'subtotal': sum, 'taxes': taxes, 'discounts': discounts, 'total_price': total_price})
        build_str = build_str + f"""
        Subtotal: \n {sum}, 

        Taxes: \n  {taxes},

        Discounts: \n  {discounts},

        Total: \n {total_price}

"""
        return build_str
    except Exception as e:
        return str(e)

#Class to handle the session of the sellig point, each location can have a different session so it would be scalable and good infortation such as language and location can be used in our favour
class Session:
    def __init__(self, restaurant_name = "Not defined", language = "en", location="Not defined", taxes=0.15, promotions=0):
        self.state = restaurant_name
        self.language = language
        self.location = location
        self.memory = ConversationBufferMemory(k=5, memory_key="chat_history", return_messages=True)
        self.orderid = generate_random_string(25)
        self.taxes = taxes
        self.promotions = promotions
        
        #Create a random order id of 20 characters and letters
        
    #METHOD TO reset the session
    def new_car(self):
        # self.orderid = call to the API
        self.orderid = generate_random_string(25)
        self.memory = self.memory.clear()

    #METHOD TO get the conversation with the user
    def get_conversation(self, message):
        message_dict ={"question": message}
        conversation = LLMChain(
            llm=llm,
            prompt=prompt,
            verbose=True,
            memory=self.memory
        )

        response = conversation(message_dict)

        #This is the call to our API for making POS integration with Agents
        # make a call to the integration_API
        data = {
            "order_id": str(self.orderid),
            "restaurant": self.state,
            "language": self.language,
            "message": message,
            "response": response['text'],
            "location": self.location,
            "taxes": self.taxes,
            "promotions": self.promotions
        }
        # Define headers with the Authorization token
        headers = {'Authorization': SECRET_TOKEN, 'Content-Type': 'application/json'}
        try:
    
            # Make the POST request
            call = requests.post(url, json=data, headers=headers)
        except Exception as e:
            print(e)
        return response
    
# Initialize the session if it's not already done
if 'session1' not in st.session_state:
    st.session_state['session1'] = Session('KFC', 'en', '2595-SN')

# Function to handle sending messages and updating chat history
def send_message(message):
    if message:  # Check if message is not empty
        
        st.session_state['session1'].user_message = message       
        st.session_state['session1'].agent_response = st.session_state['session1'].get_conversation(message)['text']
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []
        st.session_state['chat_history'].append(("You: " + message, "Bot: " + st.session_state['session1'].agent_response))

# Layout
st.title("Chatbot App")

# Input for new messages
message_input = st.text_input("Type your message here...", key='message')

# Buttons
col1, col2,col3 = st.columns(3)
with col1:
    if st.button('Send'):
        send_message(st.session_state['message'])

with col2:
    if st.button('Get current order in POS'):
        result = make_post_request(st.session_state['session1'].orderid)
        st.write("Result of order request:", result)
        
with col3:
    if st.button('Checkout order in POS'):
        check = make_checkout_request(st.session_state['session1'].orderid, st.session_state['session1'].taxes, st.session_state['session1'].promotions)
        st.write("Result of order request:", check)
# Display chat history
if 'chat_history' in st.session_state:
    # Reverse the chat history list to display newest messages first
    reversed_chat_history = reversed(st.session_state['chat_history'])
    for user_msg, bot_reply in reversed_chat_history:
        st.text_area(key = generate_random_string(5),label="", value=f"{user_msg}\n{bot_reply}", height=100, disabled=True)

# Clear chat history
if st.button('New customer'):
    st.session_state['chat_history'] = []
    st.session_state['session1'].new_car()
    st.session_state['session1'] = Session('KFC', 'en', '2595-SN')
    #reload the streamlit app
    st.rerun()
