import datetime
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI , OpenAI
from langchain.memory import ConversationBufferMemory 
from langchain.agents import Tool, load_tools
from langchain.tools import BaseTool, StructuredTool
from langchain.agents import initialize_agent
#Importing llm toolkits
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from langchain.chat_models import ChatOpenAI
from langchain_mistralai.chat_models import ChatMistralAI
from pydantic import BaseModel, Field, constr, validator
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel, Field, constr
from langchain.output_parsers import OutputFixingParser
from typing import Dict, Any


#llm = ChatMistralAI(temperature=0)
llm = ChatOpenAI(temperature=0, model_name="gpt-4")


from langchain.callbacks import get_openai_callback
import re
from googletrans import Translator
translator = Translator(service_urls=[
      'translate.google.co.kr',
    ])


from qdrant_client import QdrantClient


#Set up the Qdrant client
client = QdrantClient(
        url= os.getenv("QDRANT_URL"),
        api_key= os.getenv("QDRANT_API_KEY")
    )
client.set_model("sentence-transformers/all-MiniLM-L6-v2")

#Function to retrieve documents from Qdrant
def Qdrant_retrieve( k , query):
    query = query.lower()
    results = client.query(
    collection_name= "KFC",
    query_filter=None,
    query_text=query,
    limit=k,
)
    docs = results
    #Build the string to be returned
    text_joined = """ """
    for index, doc in enumerate (docs):
        text_joined += f"{{Match {index}: {doc.metadata['document']},  Price: {doc.metadata['price']}, Available: {doc.metadata['available']}, Keywords: {doc.metadata['keywords']}  }}, "
    return text_joined





def get_price(product):
    try:
        raw_price = calculate_response(product)
        #Ensuring nice format with pydantic 
        price = get_price_format(raw_price)
    except Exception as e:
        price = -1
    return price



def clean_string(input_string):
        # Define the patterns to be removed
        patterns = [
            r'"[Aa]ction":.*?,',
            r'"[Aa]ction":',
            r'"[Aa]ction_input":',
            r'"[Aa]ction_output":',
            r'"[Ff]inal Answer",',
            r'{',
            r'}',
            r'"'
        ]

        # Apply the patterns to the input string
        cleaned_string = input_string
        for pattern in patterns:
            cleaned_string = re.sub(pattern, '', cleaned_string)

        return cleaned_string


def calculate_response(product):
    
   
    llm = ChatOpenAI(model='gpt-4', temperature=0)

    """Tool section"""

    def rag(input = ""):
        response =  Qdrant_retrieve( 3 , input)
        if response == "":
            return "The information is not in the database"
        else:
            return "The information is: " + response    
       


    rag_retrieval = StructuredTool.from_function(
        name="rag_retrieval",
        func=rag,
        description="Useful when you want to get the price of a product. If the product is not in the give context, answer price =-1",
    
    )


    def no_info(input = ""):
        return "The price is -1"

    not_exist =  StructuredTool.from_function(
        name="not_info",
        func=no_info,
        description="Useful when the rag_retrieval tool doent find the product in the database.",
    )

    my_tools = [rag_retrieval, not_exist]
                
   



    memory = ConversationBufferMemory( k=5, return_messages=True, memory_key="chat_history", output_key="output")
    

    #PREFIX = "You are Aipickz "
    PREFIX = """You are a worker in a fast food restaurant, your task is to find the price of a given produc
    Only formulate answer with data  obtained from rag_retrieval tool. Dont answer with your own knowledge."""

    

    conversational_agent = initialize_agent(
        agent='structured-chat-zero-shot-react-description',
        tools=my_tools,
        llm=llm,
        verbose=True,
        max_iterations=5,
        early_stopping_method='generate',
        memory=memory,
        max_execution_time= 20
       
    )

    old_template = conversational_agent.agent.llm_chain.prompt[0].prompt.template
    new_template = PREFIX + old_template 
    conversational_agent.agent.llm_chain.prompt[0].prompt.template = new_template
    
    #This could be helpful to log price of operations and also for multilanguage support
    with get_openai_callback() as cb:
        
        #if record['language'] != "en":
            #record['last_message'] = translator.translate(record['last_message']).text

        
        response = conversational_agent.run(product)
        
     
        #if record['language'] == "es":
            #response = translator.translate(response, src= 'en', dest='es').text
        print('cost: $',cb.total_cost, 'tokens: ', cb.total_tokens)
      
        return response
   








#Class to indicate the format of the intent
class Price(BaseModel):
    price: float  = Field(description="The price of the product with 2 decimal places", examples= [2.50, 3.00, 5.00 , 12.75, 123.34])
    
    @validator('price')
    def check_score(cls, value):
        if value > 1000:
            raise ValueError("Badly formed Score")
        elif value < -2:
            raise ValueError("Badly formed Score")
        return value

#Class to correct any malformed intent output from the llm     
class Price_corrector(BaseModel):
    price: float  = Field(description="The price of the product with 2 decimal places", examples= [2.50, 3.00, 5.00 , 12.75, 123.34])







# Function to get the intent of the user, with output parser chain to ensure the format stability
def get_price_format(price) -> int | str:
    # Call the API to get the intent
    pydantic_parser = PydanticOutputParser(pydantic_object=Price)

    format_instructions = pydantic_parser.get_format_instructions()

    template_string = """ You are a worker in a fast food restaurant, you goal is to give the price of the product based on the given information.
    

    

    information: ```{price_info}```

    {format_instructions}

    """
    prompt = ChatPromptTemplate.from_template(template=template_string)

    messages = prompt.format_messages(price_info= price, 
                                format_instructions=format_instructions)
    output = llm(messages)

    parser = PydanticOutputParser(pydantic_object=Price_corrector)

    new_parser = OutputFixingParser.from_llm(parser=parser, 
                                         llm=llm)
    return new_parser.parse(output.content).price




