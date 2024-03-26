## Import Libraries
import os

from langchain import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.memory import ConversationBufferMemory

from langchain_google_genai import GoogleGenerativeAI
import google.generativeai as genai

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
# Configure Google GenAI
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Stramlit Framework
st.title("Movie Explorer")
input_text = st.text_input("Let's know about your favorite movie..")

# Prompt Templates
first_input_prompt = PromptTemplate(
    input_variables = ['name'],
    template = "Give a brief plot about the movie {name}"
)

second_input_prompt = PromptTemplate(
    input_variables = ['name'],
    template = "Which year the movie {name} was released"
)

third_input_prompt = PromptTemplate(
    input_variables = ['yor'],
    template = "What are the top 5 most critically acclaimed movie that was released in {yor}"
)

# Memory
plot_memory = ConversationBufferMemory(input_key='name', memory_key='plot_history')
yor_memory = ConversationBufferMemory(input_key='name', memory_key='yor_history')
top5_memory = ConversationBufferMemory(input_key='yor', memory_key='top5_history')

# LLMs
llm = GoogleGenerativeAI(model = "gemini-pro", temperature = 0.8)

chain1 = LLMChain(
            llm=llm,
            prompt=first_input_prompt,
            verbose=True,
            output_key='plot',
            memory=plot_memory)

chain2 = LLMChain(
            llm=llm,
            prompt=second_input_prompt,
            verbose=True,
            output_key='yor',
            memory=yor_memory)

chain3 = LLMChain(
            llm=llm,
            prompt=third_input_prompt,
            verbose=True,
            output_key='top5',
            memory=top5_memory)

parent_chain=SequentialChain(
    chains=[chain1,chain2,chain3],input_variables=['name'],output_variables=['plot','yor','top5'],verbose=True)



if input_text:
    st.write(parent_chain({'name':input_text},return_only_outputs=True))

    with st.expander('Plot'): 
        st.info(plot_memory.buffer)

    with st.expander('Top 5 movies from same year'): 
        st.info(top5_memory.buffer)
