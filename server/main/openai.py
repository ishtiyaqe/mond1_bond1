from httpx import request
from openai import OpenAI
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
import json
import re
from django.db.models import Count
import requests
import time

# Initialize OpenAI API key
client = OpenAI(api_key = 'Your_api_key')



def generate_prompt(id):
    a = Conflict.objects.get(id = id)

    # Example structured response generation template
    structured_response_template = {
        "impact": ["<List of Contextual impacts>", ...],
        "responsibility": [
            {"name": a.user.username, "value": "<Contextual Progress Percentage acording description>", "color": "<Color>"},
            {"name": a.assign_to.username, "value": "<Contextual Progress Percentage acording assign_description>", "color": "<Color>"}
        ] if hasattr(a, 'assign_to') and a.assign_to  else [
            {"name": a.user.username, "value": "<Contextual Progress Percentage>", "color": "<Color>"},
        ],
        "factors": ["<List of Contextual factors>", ...],
        "nextSteps": ["<List of Contextual next steps>", ...],
        "contextualOverview": "<Contextual Overview>",
        "primaryIssues": ["<List of  Contextual primary issues>", ...],
        "perspectivesBreakdown": [
            {"name": a.user.username, "Underlying_Interests": 
             ["<List of  Contextual Underlying Interests acording description>", ...]},
            {"name": a.assign_to.username, "Underlying_Interests": 
             ["<List of Contextual Underlying Interests acording assign_description>", ...]}
        ] if hasattr(a, 'assign_to') and a.assign_to else [
            {"name": a.user.username, "Underlying_Interests": 
             ["<List of Contextual Underlying Interests>", ...]},
        ],

        "accountabilityAndContributions": [
            {
                "Actions_Causing_Friction": 
                    [
                    {"name": a.user.username, "Actions_Causing_Friction": 
                    ["<List of Contextual Actions Causing Friction acording description>", ...]},
                    {"name": a.assign_to.username, "Actions_Causing_Friction": 
                    ["<List of Contextual Actions Causing Friction acording assign_description>", ...]}
                ] if hasattr(a, 'assign_to') and a.assign_to else [
                    {"name": a.user.username, "Actions_Causing_Friction": 
                    ["<List of Contextual Actions Causing Friction>", ...]},
                ]
            },
            {
                "Miscommunication_Points": ["<List of Contextual MiscommunicationPoints>", ...]
            },
            {
                "Responsibility_Distribution": 
                [

                    {"name": a.user.username, "value": "<Contextual Progress Percentage acording description>", "color": "<Color>"},
                    {"name": a.assign_to.username, "value": "<Contextual Progress Percentage acording assign_description>", "color": "<Color>"}
                ] if hasattr(a, 'assign_to') and a.assign_to else [
                    {"name": a.user.username, "value": "<Contextual Progress Percentage >", "color": "<Color>"},
                ]
            },
        ],
       
        "AreasOfImprovements": [
            {"name": a.user.username, "Communication_Style_Adjustments": 
             ["<List of Contextual Communication Style Adjustments acording description>", ...], "Cultural_&_Value_Considerations": 
             ["<List of Contextual Cultural & Value Considerations acording description>", ...]},
            {"name": a.assign_to.username, "Communication_Style_Adjustments": 
             ["<List of Contextual Communication Style Adjustments acording assign_description>", ...], "Cultural_&_Value_Considerations": 
             ["<List of Contextual Cultural & Value Considerations acording assign_description>", ...]}
        ] if hasattr(a, 'assign_to') and a.assign_to else [
            {"name": a.user.username, "Communication_Style_Adjustments": 
             ["<List of Contextual Communication Style Adjustments>", ...], "Cultural_&_Value_Considerations": 
             ["<List of Contextual Cultural & Value Considerations>", ...]},
        ],
        "ActionPlan": [
            {
                "Immediate_Steps": [{"name": "Project Scope Alignment", "Project_Scope_Alignment": 
                                     ["<List of Contextual Project Scope Alignment>", ...]}]
            },
            {
                "Long_Term_Agreements": [{"name": "Long-term Agreements", "Long_term_Agreements": 
                                          ["<List of Contextual Long-term Agreements>", ...]}],
                "Priority": "<Contextual Priority>",
                "Timeline": "<Contextual Timeline in Month>"
            },
        ],
        "AdditionalTools&Resources": [
            {
                "Recommended_Communication_Techniques": [
                    {
                        "name": "<Contextual Name>",
                        "Duration": "<Contextual Hours>",
                        "Format": "<Contextual Format>"
                    },
                    {
                        "name": "<Contextual Name>",
                        "Duration": "<Contextual Hours>",
                        "Format": "<Contextual Format>"
                    },
                    {
                        "name": "<Contextual Name>",
                        "Duration": "<Contextual Hours>",
                        "Format": "<Contextual Format>"
                    }
                ]
            },
            {
                "Progress_Tracking_Tools": [
                    {
                        "name": "<Contextual Name>",
                        "purpose": "<Contextual purpose>"
                    },
                    {
                        "name": "<Contextual Name>",
                        "purpose": "<Contextual purpose>"
                    },
                    {
                        "name": "<Contextual Name>",
                        "purpose": "<Contextual purpose>"
                    }
                ]
            }
        ],
        "Premium_Insights_&_Tools": [
            {
                "Sentiment_Analysis": [
                    [
                        {"name": a.user.username, "Communication_Style": "<Contextual Communication Style>",
                        "positive": "<Contextual positive Percentage acording description>",
                        "neutral": "<Contextual neutral Percentage acording description>",
                        "negative": "<Contextual negative Percentage acording description>",
                        "Communication_Style_Type": ["<List of Contextual Communication Style Type acording description>", ...]},
                        {"name": a.assign_to.username, "Communication_Style": "<Contextual Communication Style acording assign_description>",
                         "positive": "<Contextual positive Percentage acording assign_description>",
                        "neutral": "<Contextual neutral Percentage acording assign_description>",
                        "negative": "<Contextual negative Percentage acording assign_description>",
                        "Communication_Style_Type": ["<List of Contextual Communication Style Type acording assign_description>", ...]}
                    ] if hasattr(a, 'assign_to') and a.assign_to else [
                        {"name": a.user.username, "Communication_Style": "<Contextual Communication Style>",
                         "positive": "<Contextual positive Percentage>",
                        "neutral": "<Contextual neutral Percentage>",
                        "negative": "<Contextual negative Percentage>",
                        "Communication_Style_Type": ["<List of Contextual Communication Style Type>", ...]},
                    ]
                   
                ]
            },
            {
                "Interactive_Learning_Tools": [
                    [
                        {
                            "name": a.user.username,
                            "key": "<Contextual Interactive Learning Name>", 
                         "value": "<Related Context or Description>",
                        "Interactive_Learning": ["<List of Contextual Interactive Learning acording description>", ...]},
                        {"name": a.assign_to.username, "key": "<Contextual Interactive Learning Name>", 
                         "value": "<Related Context or Description>",
                        "Interactive_Learning": ["<List of Contextual Interactive Learning acording assign_description>", ...]}
                    ] if hasattr(a, 'assign_to') and a.assign_to else [
                        {"name": a.user.username, "key": "<Contextual Interactive Learning Name>", 
                         "value": "<Related Context or Description>",
                        "Interactive_Learning": ["<List of Contextual Interactive Learning>", ...]},
                    ]
                   
                ]
            },
            {
                "name": "Progress & Milestones",
                "Progress_&_Milestones": [
                    [
                        {
                            "name": a.user.username,
                            "progress": "<Contextual Progress Percentage>", 
                         "milestones": [
                            {

                                "achievement":["<List of Contextual milestones achievement acording description>", ...],
                                "impact":["<List of Contextual milestones impact acording description>", ...]
                            }
                         ]},
                        {"name": a.assign_to.username, "progress": "<Contextual Progress Percentage>", 
                         "milestones": [
                            {

                                "achievement":["<List of Contextual milestones achievement acording assign_description>", ...],
                                "impact":["<List of Contextual milestones impact acording assign_description>", ...]
                            }
                         ]}
                    ] if hasattr(a, 'assign_to') and a.assign_to else [
                        {"name": a.user.username, 
                         "progress": "<Contextual Progress Percentage>", 
                         "milestones": [
                            {

                                "achievement":["<List of Contextual milestones achievement>", ...],
                                "impact":["<List of Contextual milestones impact>", ...]
                            }
                         ]},
                    ]
                   
                ] 
            },
        ]



    }

    prompt = f"""
        Given the following input data:

        assign_description: "{a.assign_description}"
        description: "{a.description}"

        Generate a structured response in the following format:

        {structured_response_template}
        """

    print(prompt)
    return prompt



@csrf_exempt
def process_assessment(id):
    retries = 3  # Max retries
    attempt = 0
    while attempt < retries:
        attempt += 1
        print(f"Attempt {attempt} of {retries}")

        # Generate prompt for OpenAI
        prompt = generate_prompt(id)

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant skilled in transforming text into structured data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096  # Adjust this value if needed  
            )

            ai_response = response.choices[0].message.content.strip()
            print(ai_response)
            ai = ai_response.replace("Based on the given text, here is the structured response: ```", "")

            # Extract the required part from the AI response
            
            
            # Convert the extracted part to a Python dictionary
            start_index = ai.find("{")
            end_index = ai.rfind("}") + 1
            
            if start_index == -1 or end_index == 0:
                raise ValueError("No JSON object found in the response")
            
            json_part = ai[start_index:end_index]
            
            # Convert the extracted part to a Python dictionary
            structured_data = json.loads(json_part)
            
            # Pretty-print the structured JSON data
            formatted_json = json.dumps(structured_data, indent=4)
            print("Extracted and Formatted JSON Response:")
            print(formatted_json)
            
            # Check if 'responsibility' is valid
            c = Conflict.objects.get(id=id)
            
            c.responsibility = structured_data['responsibility']
            c.impact = structured_data['impact']
            c.factors = structured_data['factors']
            c.nextSteps = structured_data['nextSteps']
            c.contextualOverview = structured_data['contextualOverview']  # As it's a single string, no need to modify
            c.primaryIssues = structured_data['primaryIssues']
            c.perspectives = structured_data['perspectivesBreakdown']  # Assuming this is a list of dicts
            c.accountability = structured_data['accountabilityAndContributions']  # Assuming this is a list of dicts
            c.improvements = structured_data['AreasOfImprovements']  # Assuming this is a list of dicts
            c.actionPlan = structured_data['ActionPlan']  # Assuming this is a list of dicts
            c.resources = structured_data['AdditionalTools&Resources']  # Assuming it's a list
            c.premium_tools = structured_data['Premium_Insights_&_Tools']  # Assuming it's a list
            c.status = 'resolved'

            # Save the updated conflict object
            c.save()
            if not structured_data['impact']:
                raise Exception("Impact is empty.")
            # Access the 'impact' field in the dictionary
            print("Impact:", structured_data['impact'])
            return structured_data

        except Exception as e:
            print(f"Error during processing: {e}")
        
        # If we reach here, the processing was unsuccessful, retry after a delay
        time.sleep(5)  # Delay before retrying

    # If retries exhausted and still no valid data, return None
    print("Failed to get valid structured data after multiple attempts.")
    return None



