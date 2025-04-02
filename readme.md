# CSV Analysis Agent

A web-based tool that allows users to analyze CSV data through natural language queries. The application generates visualizations and provides Python code for the analysis.

## Features

- Natural language query interface
- Automatic data visualization
- Python code generation
- Interactive UI with tabs for chart and code views

## Screenshots

![Ask a question about the data](screenshots/main.jpg)

![Underlying code is also returned](screenshots/python.jpg)

![LangGraph graph](screenshots/graph.jpg)

## Installation

# install dependencies
pip install -e ".[dev]"

pip install "langgraph-cli[inmem]" --upgrade

# Just to make sure you have everything
pip install "langgraph-cli[inmem]" --upgrade

# install lang graph
pip install langgraph-sdk

# run lang studio
langgraph dev

## Usage

1. Enter the URL of your CSV file
2. Ask a question about the data
3. View the generated visualization and Python code

## Requirements

- Python 3.8+
- Required packages listed in requirements.txt