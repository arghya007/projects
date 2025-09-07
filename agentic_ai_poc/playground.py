import os
import phi
import phi.api
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.playground import Playground, serve_playground_app
from dotenv import load_dotenv

load_dotenv()

phi.api=os.getenv("PHI_API_KEY")

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

app=Playground(agents=[finance_agent, web_search_agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("playground:app", reload=True)
