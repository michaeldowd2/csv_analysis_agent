"""Define a LangGraph application for processing CSV data and generating Python code."""

import os
import pandas as pd
import re
from pathlib import Path
import uuid
import requests
from urllib.parse import urlparse

from typing import Any, Dict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from agent.configuration import Configuration
from agent.state import State


def setup_llm(config: Configuration) -> ChatOpenAI:
    """Create and configure the LLM with environment variables."""
    return ChatOpenAI(
        model=config.model_name,
        temperature=config.model_temperature,
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE")
    )


def validate_url(url: str) -> bool:
    """Validate if the URL is valid and accessible."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def validate_input(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Validate the input state."""
    # Extract the Configuration object from the RunnableConfig
    config = Configuration.from_runnable_config(config)
    print(state)
    if not state.csv_path:
        return {"error_message": "No CSV source provided"}
    
    if isinstance(state.csv_path, str) and validate_url(state.csv_path):
        try:
            requests.head(state.csv_path).raise_for_status()
        except requests.RequestException as e:
            return {"error_message": f"Failed to access URL: {str(e)}"}
    else:
        path = Path(state.csv_path)
        if not path.exists():
            return {"error_message": f"CSV file not found: {state.csv_path}"}
    
    return {}

def load_csv_data(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Load and analyze the CSV data."""
    # Extract the Configuration object from the RunnableConfig
    config = Configuration.from_runnable_config(config)
    
    # Skip if there's an error or if data is already loaded
    if state.error_message or state.csv_metadata:
        return {}
    
    try:
        df = pd.read_csv(state.csv_path)
        
        preview = df.head(config.csv_preview_rows).to_string()
        
        metadata = {
            "columns": list(df.columns),
            "shape": df.shape,
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample_values": {col: df[col].iloc[:3].tolist() for col in df.columns},
            "null_counts": {col: int(df[col].isna().sum()) for col in df.columns}
        }
        
        return {"csv_preview": preview, "csv_metadata": metadata}
    except Exception as e:
        return {"error_message": f"Error loading CSV data: {str(e)}"}

def clean_python_code(code: str) -> str:
    """Clean up the generated code to remove any syntax issues."""
    # Remove markdown code blocks if present
    code = re.sub(r'```python\s*', '', code)
    code = re.sub(r'```\s*', '', code)
    code = re.sub(r'<.*?>', '', code)
    code = code.replace("csv_path = 'path_to_your_csv_file.csv'", "")
    code = code.replace("csv_path = \"path_to_your_csv_file.csv\"", "")
    
    # Make sure print statements don't contain HTML or markdown
    code = re.sub(r'print\("(.*?)"\)', r'print("\1")', code)
    return code

def execute_python_code(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Execute the generated Python code."""

    python_path = str(Path(__file__).resolve().parent.parent / ('static' + '/' + state.file_guid + '.py'))

    try:
        with open(python_path, 'w') as f:
            f.write(state.generated_python_code)
        # capture python printed output in exec 
        output = []
        def prt(*args, **kwargs):
            output.append(' '.join(map(str, args)))

        exec_globals = { 'print': prt }
        
        exec(state.generated_python_code, exec_globals)
        return {"python_path": python_path, "output": str(output)}
    except Exception as e:
        return {"error_message": f"Error executing Python code: {str(e)}"}

def generate_python_code(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Generate Python code to answer the user's question."""
    config = Configuration.from_runnable_config(config)
    if state.error_message or state.generated_python_code:
        return {}
    
    llm = setup_llm(config)
    system_prompt = f"""You are a data analyst who will analyse a csv file and answer a users question using python.
Your task is to generate Python code that reads the csv file, processes it and then prints an answer to the users question.
Also generate a matplotlib chart to visualize the answer.

The CSV data has the following properties:
- Columns: {state.csv_metadata.get("columns", [])}
- Shape: {state.csv_metadata.get("shape", (0, 0))}
- Data types: {state.csv_metadata.get("dtypes", {})}
- Sample values: {state.csv_metadata.get("sample_values", {})}

Here's a preview of the data:
{state.csv_preview}

Generate complete, functioning Python code that:
1. Loads the CSV file from the 'csv_path' variable that is already defined
2. MUST include matplotlib code to generate a chart and save it to 'chart_path' variable that is already defined
3. Uses pandas to process the data
4. Directly answers the user's question with appropriate data manipulation
5. MUST include print statements to display the results to the user
6. Charts should show a series of data, not just one value. Choose an appropriate series for the user question, e.g. if they request a mean, you could show a histogram of all values with the mean highlighted.

IMPORTANT GUIDELINES:
- The code must fully answer the user's question, not just load the data
- DO NOT omit any part of the solution; include all necessary data processing steps
- DO NOT include placeholders like '# Code to answer question here'
- The 'csv_path' variable is already defined; do not redefine it
- Always include necessary imports at the top of the file
- Do NOT wrap your code in markdown code blocks (no ```python or ``` tags)
- Double-check your code against the available column names in the CSV file
- Use the correct column names in the code
- Do NOT include a plt.show() line, the code should run and save the chart
- DO include plt.savefig(chart_path).

EXAMPLE SOLUTION:
For the question "What are the top 3 products by total sales?" with a sales dataset containing 'product_name' and 'sales' columns:

```python
import pandas as pd
df = pd.read_csv(csv_path)
product_sales = df.groupby('product_name')['sales'].sum().reset_index()
top_products = product_sales.sort_values('sales', ascending=False).head(3)
print("Top 3 Products by Total Sales:")
print(top_products)

# Create a bar chart to visualize the top products
plt.figure(figsize=(10, 6))
plt.bar(top_products['product_name'], top_products['sales'])
plt.title('Top 3 Products by Total Sales')
plt.xlabel('Product')
plt.ylabel('Total Sales ($)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(chart_path)
```

DO NOT include any commentary, explanations, or markdown. ONLY output valid Python code."""
    
    # Create the prompt with formatted system prompt
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state.user_input)
    ])
    
    try:
        chain = prompt | llm | StrOutputParser()
        code = chain.invoke({})

        file_guid = str(uuid.uuid4())
        chart_path = str(Path(__file__).resolve().parent.parent / ('static' + '/' + file_guid + '.png')).replace('\\','\\\\')
        if isinstance(state.csv_path, str) and validate_url(state.csv_path):
            code = f"# Define the URL to the CSV file\ncsv_path = '{state.csv_path}'\nchart_path = '{chart_path}'\n{code}"
        else:
            abs_path = str(Path(state.csv_path).absolute()).replace("\\", "/")
            code = f"# Define the path to the CSV file\ncsv_path = '{abs_path}'\nchart_path = '{chart_path}'\n\n{code}"
        
        code = clean_python_code(code)
        return {"generated_python_code": code, "file_guid": file_guid, "chart_path": '/static/' + file_guid + '.png'}
    except Exception as e:
        return {"error_message": f"Error generating code: {str(e)}"}

# Define the workflow
workflow = StateGraph(State, config_schema=Configuration)

# Add nodes to the graph
workflow.add_node("validate_input", validate_input)
workflow.add_node("load_csv_data", load_csv_data)
workflow.add_node("generate_python_code", generate_python_code)
workflow.add_node("execute_python_code", execute_python_code)

# Define a simple linear flow
workflow.add_edge("__start__", "validate_input")
workflow.add_edge("validate_input", "load_csv_data")
workflow.add_edge("load_csv_data", "generate_python_code")
workflow.add_edge("generate_python_code", "execute_python_code")
workflow.add_edge("execute_python_code", END)

# Compile the workflow
graph = workflow.compile()
graph.name = "CSV-to-Python-Code Generator"
