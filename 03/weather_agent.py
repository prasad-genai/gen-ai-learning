from openai import OpenAI
import requests
from dotenv import load_dotenv
import json
import os


load_dotenv()

client = OpenAI(
    api_key=os.environ['API_KEY'],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

def get_weather(city):
    print("🔨 Tool Called: get_weather", city)
    
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."
    return "Something went wrong"

def run_command(command):
    
    os.system(command=command)


available_tools = {
    "get_weather": {
        "fn": get_weather,
        "description": "Takes a city name as an input and returns the current weather for the city."
    },
    "run_command": {
        "fn": run_command,
        "description": "Takes a command as input to execute on system and returns ouput."
    }
}


system_prompt = """
You are an AI assistant who is expert in breaking down complex problems and then resolve the user query.
For the given user input, analyze the input and breakdown the problem step by step.
Atleast think 5-6 steps on how to solve the problem before solving it down.

The steps are you get a user input, you analyze, you think, you again think for serveral times and then return an output with explanation and then finally you validate the output as well before giving final results.
Follow the steps in sequence that is "analyse", "think", "output", "validate" and finally "result".

Rules-
1. Follow the strict JSON output as per output schema.
2. Always perform one step at at time and time and wait for next input.
3. Carefully analyze the user query.

Output Format-
{{
    "step": "string", 
    "content": "string", 
    "function":"The name of function if the step is action",
    "input": "The input parameter for the function"
}}

Available Tools-
- get_weather: Takes a city name as an input and returns the current weather for the city.
- run_command: Takes a command as input to execute on system and returns output.

Example-
User Query: What is the weather of Mumbai?
Output: {{"step": "plan", "content": "The user is interested in weather data of mumbai"}}
Output: {{"step": "plan", "content": "From the available tools I should call get_weather"}}
Output: {{"step": "action", "function": "get_weather", "input": "mumbai"}}
Output: {{"step": "observe", "content": "30 Degree Cel"}}
Output: {{"step": "output", "content": The weather for mumbai to be 30 degrees."}}

"""

messages = [
    { "role": "system", "content": system_prompt }
]

while True:
    user_query = input('> ')
    messages.append({ "role": "user", "content": user_query })

    while True:
        response = client.chat.completions.create(
            model="models/gemini-1.5-flash-001",
            response_format={"type": "json_object"},
            messages=messages
        )

        parsed_output = json.loads(response.choices[0].message.content)
        messages.append({ "role": "assistant", "content": json.dumps(parsed_output) })

        if parsed_output.get("step") == "plan":
            print(f"🧠: {parsed_output.get('content')}")
            continue
        
        if parsed_output.get("step") == "action":
            tool_name = parsed_output.get("function")
            tool_input = parsed_output.get("input")

            if available_tools.get(tool_name, False) != False:
                output = available_tools[tool_name].get("fn")(tool_input)
                messages.append({ "role": "assistant", "content": json.dumps({ "step": "observe", "output":  output}) })
                continue
        
        if parsed_output.get("step") == "output":
            print(f"🤖: {parsed_output.get('content')}")
            break