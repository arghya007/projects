# *** Importing Necessary Packages ***
import streamlit as st
import os
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ['GROQ_API_KEY']                                                       # Retriving API Key from environment file


def main():

    st.title("🎥 Movie time with Arghya")                                                # Define a title for the chatbot Front End

    # Add customization options to the sidebar
    st.sidebar.title('Select an LLM')                                                      # Define a title for the chatbot Side Bar
    model = st.sidebar.selectbox(
        'Choose a model',
        ['mixtral-8x7b-32768', 'Gemma-7b-lt']                           # 'llama2-70b-4096',  Define a choices for LLM Model
    )
    conversational_memory_length = st.sidebar.slider('Conversational memory length:', 
                                                     1, 10, value = 5)                     # Define a slider to choose the lengh of converstaion in Side Bar 

    memory=ConversationBufferWindowMemory(k=conversational_memory_length)                  # Store the user chosen length as memory for future use  

    user_question = st.text_area(
        "da da da... what's there to watch.. tell me about an Actor, Director, Movie, or anything...... Still no clue? Okay let's start with how's your mood! ")                                  # Define a prompt for question area

    # session state variable
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history=[]
    else:
        for message in st.session_state.chat_history:
            memory.save_context({'input':message['human']},{'output':message['AI']})       # Storing the context of the conversation 

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

    if st.button("Submit & Process"):
        if user_question:
            with st.spinner("Processing..."):
                response = chain.invoke({"question":user_question}) 
                if isinstance(response, dict):
                    response = response['response']                                                           # Generating response for User's Question
                message = {'human':[user_question],'AI':response}                         
                st.session_state.chat_history.append(message)                                      # Appending the QnA to chat history
                st.write("Chatbot:", response)                                         # Writing back the response in Front End

if __name__ == "__main__":
    main()
