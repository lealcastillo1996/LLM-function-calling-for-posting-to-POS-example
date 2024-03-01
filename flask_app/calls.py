"""Code to define call to POS"""
#importing the required libraries
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
from hmacHelper import hmacHelper
from datetime import datetime
from datetime import timezone
import json
import requests

#Format the payload
def doubleQ(dict):
    return (json.dumps(dict))

#Create the payload
def createPayload(dict):
    eDict = {}
    quantity = {
        "unitOfMeasure": "EA",
        "unitOfMeasureLabel": "",
        "value": dict['qty'],
    }
    unitPrice = dict["price"]
    productId = {
        "type": "",
        "value": dict['item'],
    }
    eDict.update({"productId": productId})
    eDict.update({"quantity": quantity})
    eDict.update({"unitPrice": unitPrice})

    return eDict

#Function for creating an order based in a cart object list of dictionaries
def createOrder(cart):
    secretKey = os.getenv('SECRET_KEY')
    sharedKey = os.getenv('SHARED_KEY')
    nepOrganization = os.getenv('ORGANIZATION')
    now = datetime.now(tz=timezone.utc)
    now = datetime(now.year, now.month, now.day, hour=now.hour,
                   minute=now.minute, second=now.second)
    requestURL = "https://api.ncr.com/order/3/orders/1"
    httpMethod = 'POST'
    contentType = 'application/json'
    hmacAccessKey = hmacHelper(sharedKey, secretKey, now, httpMethod,
                               requestURL, contentType, None, None, None, nepOrganization, None)
    
    utcDate = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    headers = {
        "Date": utcDate,
        "Content-Type": contentType,
        "Authorization": "AccessKey " + hmacAccessKey,
        "nep-organization": nepOrganization
    }
    results = []
    for dict in range(len(cart)):
        results.append(createPayload(cart[dict]))
    
    modified_results = doubleQ(results)

    customer = {
        "email": "test@ncr.com",
        "firstName": "Testy",
        "lastName": "McTest Test"
    }

    modified_customer = doubleQ(customer)
    payload = "{\"comments\":\"This is a test4\",\"customer\":%s,\"orderLines\":%s}" % (
    modified_customer, modified_results)

    payload = json.loads(payload)
    payload = json.dumps(payload)
    request = requests.post(requestURL, data=payload, headers=headers)
    result = request.json()
    return result['id']

#Function for getting an order based on an orderId
def getOrder(orderId):
    secretKey = os.getenv('SECRET_KEY')
    sharedKey = os.getenv('SHARED_KEY')
    nepOrganization = os.getenv('ORGANIZATION')
    now = datetime.now(tz=timezone.utc)
    now = datetime(now.year, now.month, now.day, hour=now.hour,
                   minute=now.minute, second=now.second)

    requestURL = 'https://api.ncr.com/order/3/orders/1/%s' % orderId
    httpMethod = 'GET'
    contentType = 'application/json'

    hmacAccessKey = hmacHelper(sharedKey, secretKey, now, httpMethod,
                               requestURL, contentType, None, None, None, nepOrganization, None)
    utcDate = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    headers = {
        "Date": utcDate,
        "Content-Type": contentType,
        "Authorization": "AccessKey " + hmacAccessKey,
        "nep-organization": nepOrganization
    }
    request = requests.get(requestURL, headers=headers)

    res = dict()
    res['status'] = request.status_code
    res['data'] = request.json()

    json_formatted = json.dumps(res, indent=2)
    print(json_formatted)
    return res

#Function to get all orders
def getOrders():
    secretKey = os.getenv('SECRET_KEY')
    sharedKey = os.getenv('SHARED_KEY')
    nepOrganization = os.getenv('ORGANIZATION')

    now = datetime.now(tz=timezone.utc)
    now = datetime(now.year, now.month, now.day, hour=now.hour,
                   minute=now.minute, second=now.second)

    requestURL = "https://api.ncr.com/order/3/orders/1"
    httpMethod = 'POST'
    contentType = 'application/json'

    hmacAccessKey = hmacHelper(sharedKey, secretKey, now, httpMethod,
                               requestURL, contentType, None, None, None, nepOrganization, None)

    utcDate = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    headers = {
        "Date": utcDate,
        "Content-Type": contentType,
        "Authorization": "AccessKey " + hmacAccessKey,
        "nep-organization": nepOrganization
    }
    data = {
        "enterpriseUnitId" : os.environ.get('ENTERPRISE_ID') }

    payload = json.dumps(data)

    request = requests.post(requestURL, data=payload, headers=headers)
    
    print(request)
    res = dict()
    res['status'] = request.status_code
    res['data'] = request.json()
    
    json_formatted = json.dumps(res, indent=2)
    return res

#Function to replace an order based on an orderId and a cart object list of dictionaries
def updateOrder(orderId,cart):
    secretKey = os.getenv('SECRET_KEY')
    sharedKey = os.getenv('SHARED_KEY')
    nepOrganization = os.getenv('ORGANIZATION')

    now = datetime.now(tz=timezone.utc)
    now = datetime(now.year, now.month, now.day, hour=now.hour,
                   minute=now.minute, second=now.second)

    requestURL = 'https://api.ncr.com/order/3/orders/1/%s' % orderId
    httpMethod = 'PUT'
    contentType = 'application/json'

    hmacAccessKey = hmacHelper(sharedKey, secretKey, now, httpMethod,
                               requestURL, contentType, None, None, None, nepOrganization, None)
    utcDate = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    headers = {
        "Date": utcDate,
        "Content-Type": contentType,
        "Authorization": "AccessKey " + hmacAccessKey,
        "nep-organization": nepOrganization
    }
    results = []
    for dict in range(len(cart)):
        results.append(createPayload(cart[dict]))
    modified_results = doubleQ(results)
    customer = {
        "email": "test@ncr.com",
        "firstName": "Testy",
        "lastName": "McTest Test"
    }

    modified_customer = doubleQ(customer)
    payload = "{\"comments\":\"This is a test6\",\"customer\":%s,\"orderLines\":%s}" % (
    modified_customer, modified_results)

    payload = json.loads(payload)
    payload = json.dumps(payload)
    request = requests.put(requestURL, data=payload, headers=headers)
    result = request.json()
    return result


#Cart example
cart = [{'item': 'SmallFries', 'price': 9.00, 'qty': 2}, {'item': 'Tunaburger',
                                                          'price': 13.00, 'qty': 2}, {'item': 'milkshake', 'price': 11.00, 'qty': 2}]


#res = createOrder(cart)
#print(res)


orderId = '12522067931988904101'

res = getOrder(orderId)



#res = updateOrder(orderId,cart)
#print('order replaced',res)




