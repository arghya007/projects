# *** Importing Necessary Packages ***
import streamlit as st
import os
from groq import Groq
import random
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ['GROQ_API_KEY']                                                       # Retriving API Key from environment file


def main():

    st.title("Chai pe Charcha with Arghya")                                                # Define a title for the chatbot Front End

    # Add customization options to the sidebar
    st.sidebar.title('Select an LLM')                                                      # Define a title for the chatbot Side Bar
    model = st.sidebar.selectbox(
        'Choose a model',
        ['mixtral-8x7b-32768', 'llama2-70b-4096', 'Gemma-7b-lt']                           # Define a choices for LLM Model
    )
    conversational_memory_length = st.sidebar.slider('Conversational memory length:', 
                                                     1, 10, value = 5)                     # Define a slider to choose the lengh of converstaion in Side Bar 

    memory=ConversationBufferWindowMemory(k=conversational_memory_length)                  # Store the user chosen length as memory for future use  

    user_question = st.text_area("What's in your mind..")                                  # Define a prompt for question area

    # session state variable
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history=[]
    else:
        for message in st.session_state.chat_history:
            memory.save_context({'input':message['human']},{'output':message['AI']})       # Storing the context of the conversation 


    # Initialize Groq Langchain chat object and conversation
    groq_chat = ChatGroq(
            groq_api_key = api_key, 
            model_name=model                                                               # Initializing the Groq ChatBot
    )

    conversation = ConversationChain(
            llm=groq_chat,
            memory=memory                                                                  # Initializing the conversation chain  
    )
    if st.button("Submit & Process"):
        if user_question:
            with st.spinner("Processing..."):
                response = conversation(user_question)                                             # Generating response for User's Question
                message = {'human':user_question,'AI':response['response']}                         
                st.session_state.chat_history.append(message)                                      # Appending the QnA to chat history
                st.write("Chatbot:", response['response'])                                         # Writing back the response in Front End

if __name__ == "__main__":
    main()