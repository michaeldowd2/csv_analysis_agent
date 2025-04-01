from flask import Flask, render_template, jsonify, request
import json
from src.agent.graph import graph
from src.agent.state import State

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def run_analysis():
    data = request.get_json()
    csv_source = data.get('csv')
    user_input = data.get('question')

    # Create initial state
    initial_state = State(
        user_input=user_input,
        csv_path=csv_source
    )

    # Prepare configuration
    config = {
        "configurable": {
            "model_name": "gpt-4o-mini",
            "model_temperature": 0.0,
            "csv_preview_rows": 5
        }
    }

    # Run the graph
    print(f"Processing CSV source: {csv_source}")
    print(f"Question: {user_input}")
    print("Generating code...\n")
    
    # Run the graph
    result = graph.invoke(initial_state, config=config)
    
    # Prepare response
    response = {
        'text': result.get('output'),
        'png': result.get('chart_path'),
        'python': result.get('python_path')
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
