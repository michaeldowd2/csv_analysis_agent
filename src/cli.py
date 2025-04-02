import os
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from agent.graph import graph
from agent.state import State
from agent.configuration import Configuration
from IPython.display import Image, display
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles


def main():
    """Run the CLI application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate Python code to analyze CSV data based on natural language questions."
    )
    parser.add_argument(
        "--csv", "-c", type=str, required=True, help="Path to the CSV file or URL to a CSV file"
    )
    parser.add_argument(
        "--question", "-q", type=str, help="Question to ask about the data"
    )
    parser.add_argument(
        "--model", "-m", type=str, default="gpt-4o-mini", 
        help="OpenAI model to use"
    )
    parser.add_argument(
        "--temperature", "-t", type=float, default=0.0,
        help="Temperature for the LLM (0.0-1.0)"
    )
    parser.add_argument(
        "--preview-rows", "-p", type=int, default=5,
        help="Number of rows to include in the preview"
    )
    
    args = parser.parse_args()
    
    # Validate CSV source
    csv_source = args.csv
    if not csv_source:
        print("Error: No CSV source provided")
        return
    
    # Get user question if not provided
    user_input = args.question
    if not user_input:
        user_input = input("Enter your question about the data: ")
    
    # Prepare configuration
    config = {
        "configurable": {
            "model_name": args.model,
            "model_temperature": args.temperature,
            "csv_preview_rows": args.preview_rows
        }
    }
    
    # Initialize state
    initial_state = State(
        user_input=user_input,
        csv_path=csv_source
    )
    
    # Run the graph
    print(f"Processing CSV source: {csv_source}")
    print(f"Question: {user_input}")
    print("Generating code...\n")
    print('graph name: ' + graph.name)
    
    result = graph.invoke(initial_state, config)
    
    # Display result - result is now an AddableValuesDict not a State object
    chart_path = result.get("chart_path")
    python_path = result.get("python_path")
    output = result.get("output")
    print(chart_path)
    print(python_path)
    print(output)
    return
    


if __name__ == "__main__":
    main() 