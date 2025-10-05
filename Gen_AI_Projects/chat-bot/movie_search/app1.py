import os
# from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig

from dotenv import load_dotenv
load_dotenv()

 
import chainlit as cl

load_dotenv()
api_key = os.environ['GROQ_API_KEY']   

@cl.on_chat_start
async def factory():
    # conversational_memory_length = 5
    elements = [
    cl.Image(name="image1", display="inline", path="./movie.jpeg")
    ]
    await cl.Message(content="da da da... what's there to watch.. tell me about an Actor, Director, Movie, or anything...... Still no clue? Okay let's start with how's your mood! ", elements=elements).send()
    model = 'Llama3-70b-8192'
    # memory=ConversationBufferWindowMemory(k=conversational_memory_length)                  # Store the user chosen length as memory for future use  
    
    # if 'chat_history' not in cl.session_state:
    #     cl.session_state.chat_history=[]
    # else:
    #     for message in cl.session_state.chat_history:
    #         memory.save_context({'input':message['human']},{'output':message['AI']})       # Storing the context of the conversation 
    prompt=ChatPromptTemplate.from_messages(
        [
            ("system",
             """
             You are a helpful movies expert. 
             Please response to the user queries which can be about a MOOD or GENRE, MOVIE, ACTOR, DIRECTOR, MUSIC DIRECTOR, CINEMATOGRAPHER, PRODUCER, TECHNICIAN etc. 
             Respond by mentioning:
                - Why famous in 50 words
                - If a MOVIE, a short plotline in another 50 words
                - If a MOVIE, Year of Release, genre, and 3 similar movie recomendation; if a(n) ACTOR, DIRECTOR, MUSIC DIRECTOR, CINEMATOGRAPHER, PRODUCER, TECHNICIAN, name and year of their first work and best 3 works with their genre
                - If a MOOD or GENRE, recomend 3 movies with why famous, Year of Release and plotline
             """),
            ("user","Question:{question}")
        ]
    )
    # Initialize Groq Langchain chat object and conversation
    groq_chat = ChatGroq(
            groq_api_key = api_key, 
            model_name=model                                                               # Initializing the Groq ChatBot
    )
    output_parser=StrOutputParser()

    chain=prompt|groq_chat|output_parser

    cl.user_session.set("chat_engine", chain)

@cl.on_message
async def main(message: cl.Message):
    runnable = cl.user_session.get("chat_engine")  # type: Runnable

    msg = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()