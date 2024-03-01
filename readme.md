# VOX TASK 2 POS implementation with GENAI

## _POS GenAI integrations

This code showcases an example of how an integration of POS system backend can coupled with a GenAI implementation. The system is capable of working with both GPT and Mistral but GPT is recommended for the highest performance.

The approach consist of an Streamlit app that simulates the conversation between a user and a cashier or drive-though seller, in the background a Flask webhook is hearing for all the steps in the conversation, first inferering the intent of the user, then updating the order if requiered and posting to a POS system.

This solution is scalable thanks to a support free database implementation (Mongodb) which helps to store conversation for the agents memory and also to match the POS user id with the selling point. Easily this implementation can serve more than 1 selling point at the same time, includingg aspects such as location, language , tax rate and promotion of the selling point. It also takes care of security of the webhook and the orders placing in a medium level with a simple but effective token authentification.


## _GENAAI APPROACH:
although agents are boom right now, they are no yet 100% stable, That is why I decided to dont use them for the 100% of the implementation, instead I only use them in a very focused task where they can shine more, the RAG retrieval with tools and functions. For the working flow of the API I decided to use chanes and output parsers, they sound simple, but thet are really effective,fast , stable and save a lot of tokens, making them a sweet spot for this purpose

_
## _POS Functions
All the asked features in the task are covered, the order is open an updated in real time alon with the conversation (in the background) and at the end an option for chekout is present in the UI. The implementation with GenAI is surprisingly good and stable. The only thing not covered during this demo is the retrival of articles from the catalog.

## _Implementation performance

The POS integration is stable and is capable of omitting articles that are not being sold in the store, also can add, remove and edit articles for the POS with a great performance

# Operation

## _Instructions to run APP
1.- Pull the repository from Github

2.- create python enviroment in the main folder of the project
$command: python -m venv venv    

3.- activate python env
$command: source venv/bin/activate

4.- install requirements
$command: pip install -r requirements.txt

5.- Rename .env_sample to .env and fill the Keys of the retrievers you want to use.

For running this locally, you would require 2 terminals at the same time

Terminal 1:
6.- for running the app go to the main source folder and do in terminal:
$command: streamlit run Store.py

Terminal 2:
7.- To serve the Flask backend, go to flask_app/ and 
$command: python app.py



## _Source of knowledge
KFC vector database from task 1
