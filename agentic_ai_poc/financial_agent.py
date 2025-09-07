from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
import os
from dotenv import load_dotenv
load_dotenv()

# Web Search Agent
web_search_agent = Agent(
    name = "Web Search Agent",
    role = "Search the web for imformation",
    model = Groq(id = "deepseek-r1-distill-llama-70b"),
    tool = [DuckDuckGo()],
    instructions = ["Always include sources"],
    show_tools_calls = True,
    markdown = True
)

# Financial Agent
finance_agent = Agent(
    name = "Finance AI Agent",
    model = Groq(id = "deepseek-r1-distill-llama-70b"),
    tools=[YFinanceTools(stock_price=True, 
                         analyst_recommendations=True, 
                         stock_fundamentals=True,
                         company_news=True)],
    instructions = ["Use tables to display data"],
    show_tools_calls = True,
    markdown = True
)


multi_ai_agent = Agent(
    team = [web_search_agent, finance_agent],
    model = Groq(id = "deepseek-r1-distill-llama-70b"),
    instructions = ["Always include sources", "Use tables to display data"],
    show_tools_calls = True,
    markdown = True
)


multi_ai_agent.print_response("Summerize analyst recomendation and share the latest news for NVDA", stream=True)