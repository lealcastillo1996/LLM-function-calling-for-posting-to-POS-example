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

#llm = ChatMistralAI(temperature=0)
llm = ChatOpenAI(temperature=0, model_name="gpt-4")

#Class to indicate the format of the intent
class Intent(BaseModel):
        intent: constr(pattern='^(A|B|C)$') = Field(description="current intent of the user, A): checkout order, B): add,remove,update products, C): other")
    
        @validator('intent')
        def check_score(cls, value):
            if value not in ["A", "B", "C"]:
                raise ValueError("Intent must be one of 'A', 'B', or 'C'.")
            return value

#Class to correct any malformed intent output from the llm     
class Intent_corrector(BaseModel):
    intent:constr(pattern='^(A|B|C)$') = Field(description="current intent of the user, A): checkout order, B): add,remove,update, C): other")


# Function to get the intent of the user, with output parser chain to ensure the format stability
def get_intent(query: str) -> str:
    # Call the API to get the intent
    pydantic_parser = PydanticOutputParser(pydantic_object=Intent)

    format_instructions = pydantic_parser.get_format_instructions()

    template_string = """ You are a worker in a fast food restaurant, you goal is to identificate the current intent of the user in the given conversation.
    The user can have 3 possible intents:
    A) Checkout order
    B) Add,remove or update
    C) Other

    Please identify the intent of the user and write it down.

    conversation: ```{user_query}```

    {format_instructions}

    """
    prompt = ChatPromptTemplate.from_template(template=template_string)

    messages = prompt.format_messages(user_query= query, 
                                format_instructions=format_instructions)
    output = llm(messages)

    parser = PydanticOutputParser(pydantic_object=Intent_corrector)

    new_parser = OutputFixingParser.from_llm(parser=parser, 
                                         llm=llm)
    return new_parser.parse(output.content).intent
