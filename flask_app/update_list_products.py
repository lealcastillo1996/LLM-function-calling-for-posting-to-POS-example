#Importing llm toolkits
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from typing import List
from dotenv import load_dotenv
load_dotenv()
from langchain.chat_models import ChatOpenAI
from langchain_mistralai.chat_models import ChatMistralAI
from pydantic import BaseModel, Field, constr, validator
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel, Field, constr
from langchain.output_parsers import OutputFixingParser

#This part dosnt work with mistral for now

#llm = ChatMistralAI(temperature=0)
llm = ChatOpenAI(temperature=0, model_name="gpt-4")


#Class to indicate the format of the lists to get
class Order(BaseModel):
    list_products: List| str = Field(description="[the new list of products]", examples= ["['cheseeburger', 'fries', 'pepsi']"])
    list_ocurrences: List | str = Field(description="[the new list of number of ocurrences of each product]", examples= ["[2, 2, 4]" ])
    
        

#Class to correct any malformed intent output from the llm     
class Order_corrector(BaseModel):
    list_products: List | str = Field(description="[the new list of products]", examples= ["['cheseeburger', 'fries' ,'menu Colonel', 'pepsi' , 'salad', 'ice cream']"])
    list_ocurrences: List | str = Field(description="[the new list of number of ocurrences of each product]" , examples= ["[2, 2, 1, 4, 1, 2]" ])
    

# Function to get the intent of the user, with output parser chain to ensure the format stability
def get_new_order(query: str, list_products_past, list_ocurrences_past) -> str:
    # Call the API to get the intent
    pydantic_parser = PydanticOutputParser(pydantic_object=Order)

    format_instructions = pydantic_parser.get_format_instructions()

    template_string = """ You are a worker in a fast food restaurant, 
    your task is to take the previous list of products and occurrences and update it based in the conversation between the user and the assistant.

    previous list of products: {list_products_past}

    previous list of occurrences: {list_ocurrences_past}

    conversation: ```{user_query}```

    {format_instructions}

    """
    prompt = ChatPromptTemplate.from_template(template=template_string)

    messages = prompt.format_messages(user_query= query,list_products_past = list_products_past, list_ocurrences_past = list_ocurrences_past,    
                                format_instructions=format_instructions)
    output = llm(messages)

    parser = PydanticOutputParser(pydantic_object=Order_corrector)

    new_parser = OutputFixingParser.from_llm(parser=parser, 
                                         llm=llm)
    return new_parser.parse(output.content).list_products, new_parser.parse(output.content).list_ocurrences
