from dotenv import load_dotenv
from langchain.globals import set_verbose, set_debug
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
import streamlit as st

from prompts import *
from states import *
from tools import *



_ = load_dotenv()

set_debug(True)
set_verbose(True)

llm = ChatGroq(model="openai/gpt-oss-120b")


def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    resp = llm.with_structured_output(Plan).invoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}


def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    resp = llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")

    resp.plan = plan
    print(resp.model_dump_json())
    return {"task_plan": resp}


def coder_agent(state: dict) -> dict:
    """LangGraph tool-using coder agent."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.run(current_task.filepath)

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n"
        "Use write_file(path, content) to save your changes."
    )

    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(llm, coder_tools)

    react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}]})

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")
agent = graph.compile()

# Streamlit Frontend
st.title("Agentic Code Generator")

if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.header("User Input")
    user_prompt = st.text_area("Enter your prompt:", value="Build a functional simple calculator for basic arithmetic operations in html css and js", height=150)
    if st.button("Generate App"):
        with st.spinner("Generating app..."):
            st.session_state.result = agent.invoke({"user_prompt": user_prompt}, {"recursion_limit": 100})
        st.success("App generated!")

if st.session_state.result:
    st.header("Developed App")
    try:
        # Extract filepaths from task plan
        steps = st.session_state.result["coder_state"].task_plan.implementation_steps
        filepaths = [step.filepath for step in steps]

        # Identify files (assume one each)
        html_file = next(f for f in filepaths if f.endswith('.html'))
        css_file = next((f for f in filepaths if f.endswith('.css')), None)
        js_file = next((f for f in filepaths if f.endswith('.js')), None)

        # Read contents
        html_content = read_file(html_file)

        # Inline CSS if exists
        if css_file:
            css_content = read_file(css_file)
            html_content = html_content.replace('</head>', f'<style>\n{css_content}\n</style>\n</head>')

        # Inline JS if exists
        if js_file:
            js_content = read_file(js_file)
            html_content = html_content.replace('</body>', f'<script>\n{js_content}\n</script>\n</body>')

        # Render the inlined HTML
        st.components.v1.html(html_content, height=600, scrolling=True)
    except StopIteration:
        st.error("Required files not found. Check generated filepaths.")
    except Exception as e:
        st.error(f"Error rendering app: {e}")

    with st.expander("Final State (for debugging)"):
        st.json(st.session_state.result)