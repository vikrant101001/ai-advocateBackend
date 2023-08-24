from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import pickle
from langchain import LLMChain
from langchain.llms import OpenAIChat
from langchain.prompts import Prompt
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
import requests
import json
import traceback
import random

print("hi")
pointer = 0
history = []
API_SECRET = os.environ.get(
    'API_SECRET')  # Get the API_SECRET from Replit environment

#***************CHECKIN MODULE***********************************
# Load existing data from the JSON file, if any
json_file_path = 'user_responses.json'
try:
  with open(json_file_path, 'r') as json_file:
    data = json.load(json_file)
except FileNotFoundError:
  data = {'check_ins': []}

# Define the questions and gather user information
questions = {
    'Q1': {
        'question': "How is Martha's mood today?",
        'options':
        ["Agitated", "Angry", "Frustrated", "Lost", "Neutral", "Happy"]
    },
    'Q2': {
        'question':
        "Has Martha experienced any of the following in the past week?",
        'options': ["Increasing irritability", "Wandering", "Delusions"]
    },
    'Q3': "How long did Martha sleep yesterday?",
    'Q4': {
        'question':
        "How was Martha's sleep yesterday?",
        'options': [
            "Well rested", "Woke up once", "Woke up 2 or 3 times",
            "Woke up 4 or more times", "Disrupted"
        ]
    },
    'Q5': {
        'question':
        "Has Martha experienced any vomiting in the past week? (yes/no)",
        'options': ["yes", "no"]
    },
    'Q5.1': {
        'question':
        "How many times in the past week?",
        'options':
        ["Once only", "2 to 3 times", "4 to 5 times", "More than 5 times"]
    },
    'Q5.2': {
        'question':
        "For how long did the episode last?",
        'options': [
            "Less than 30 minutes", "30 mins to an hour", "1 to 4 hours",
            "Full day"
        ]
    },
    'Q5.3': {
        'question':
        "How did it impact Martha's daily activities?",
        'options': [
            "Difficulty eating and drinking", "Difficulty walking", "Fatigue",
            "Severe dehydration"
        ]
    }
}

# Define the questionnaire questions with options and scores
questionnaire_questions = [{
    "title":
    "Basic Activities of Daily Living",
    "question":
    "During the past month, have you had difficulty with taking care of yourself, eating,dressing or bathing",
    "options": [{
        "option": "Usually did with no difficulty",
        "score": 4
    }, {
        "option": "Some difficulty",
        "score": 3
    }, {
        "option": "Much difficulty",
        "score": 2
    }, {
        "option": "Usually did not do because of health",
        "score": 1
    }, {
        "option": "Usually did not do for other reasons",
        "score": 0
    }]
}, {
    "title":
    "Basic Activities of Daily Living",
    "question":
    "During the past month, have you had difficulty with movingn in or out of a bed or chair",
    "options": [{
        "option": "Usually did with no difficulty",
        "score": 4
    }, {
        "option": "Some difficulty",
        "score": 3
    }, {
        "option": "Much difficulty",
        "score": 2
    }, {
        "option": "Usually did not do because of health",
        "score": 1
    }, {
        "option": "Usually did not do for other reasons",
        "score": 0
    }]
}, {
    "title":
    "Basic Activities of Daily Living",
    "question":
    "During the past month, have you had difficulty with walking indoors such as around you home",
    "options": [{
        "option": "Usually did with no difficulty",
        "score": 4
    }, {
        "option": "Some difficulty",
        "score": 3
    }, {
        "option": "Much difficulty",
        "score": 2
    }, {
        "option": "Usually did not do because of health",
        "score": 1
    }, {
        "option": "Usually did not do for other reasons",
        "score": 0
    }]
}, {
    "title":
    "Intermediate Activities of Daily Living",
    "question":
    "During the past month, have you had difficulty with walking several blocks",
    "options": [{
        "option": "Usually did with no difficulty",
        "score": 4
    }, {
        "option": "Some difficulty",
        "score": 3
    }, {
        "option": "Much difficulty",
        "score": 2
    }, {
        "option": "Usually did not do because of health",
        "score": 1
    }, {
        "option": "Usually did not do for other reasons",
        "score": 0
    }]
}, {
    "title":
    "Intermediate Activities of Daily Living",
    "question":
    "During the past month, have you had difficulty with walking one block or climbing one flight of stairs",
    "options": [{
        "option": "Usually did with no difficulty",
        "score": 4
    }, {
        "option": "Some difficulty",
        "score": 3
    }, {
        "option": "Much difficulty",
        "score": 2
    }, {
        "option": "Usually did not do because of health",
        "score": 1
    }, {
        "option": "Usually did not do for other reasons",
        "score": 0
    }]
}, {
    "title":
    "Intermediate Activities of Daily Living",
    "question":
    "During the past month, have you had difficulty with doing errands",
    "options": [{
        "option": "Usually did with no difficulty",
        "score": 4
    }, {
        "option": "Some difficulty",
        "score": 3
    }, {
        "option": "Much difficulty",
        "score": 2
    }, {
        "option": "Usually did not do because of health",
        "score": 1
    }, {
        "option": "Usually did not do for other reasons",
        "score": 0
    }]
}, {
    "title":
    "Mental Health",
    "question":
    "During the past month, have you been a very nervous person?",
    "options": [{
        "option": "All of the time",
        "score": 0
    }, {
        "option": "Most of the time",
        "score": 1
    }, {
        "option": "A good bit of the time",
        "score": 2
    }, {
        "option": "Some of the time",
        "score": 3
    }, {
        "option": "None of the time",
        "score": 4
    }]
}, {
    "title":
    "Mental Health",
    "question":
    "During the past month, have you felt calm and peaceful?",
    "options": [{
        "option": "All of the time",
        "score": 4
    }, {
        "option": "Most of the time",
        "score": 3
    }, {
        "option": "A good bit of the time",
        "score": 2
    }, {
        "option": "Some of the time",
        "score": 1
    }, {
        "option": "None of the time",
        "score": 0
    }]
}, {
    "title":
    "Mental Health",
    "question":
    "During the past month, have you felt downhearted and blue?",
    "options": [{
        "option": "All of the time",
        "score": 0
    }, {
        "option": "Most of the time",
        "score": 1
    }, {
        "option": "A good bit of the time",
        "score": 2
    }, {
        "option": "Some of the time",
        "score": 3
    }, {
        "option": "None of the time",
        "score": 4
    }]
}, {
    "title":
    "Work Performance",
    "question":
    "During the Past month, have you done as much work as others in similar jobs?",
    "options": [{
        "option": "All of the time",
        "score": 4
    }, {
        "option": "Most of the time",
        "score": 3
    }, {
        "option": "Some of the time",
        "score": 2
    }, {
        "option": "None of the time",
        "score": 1
    }]
}, {
    "title":
    "Work Performance",
    "question":
    "During the Past month, have you worked you regular number of hours?",
    "options": [{
        "option": "All of the time",
        "score": 4
    }, {
        "option": "Most of the time",
        "score": 3
    }, {
        "option": "Some of the time",
        "score": 2
    }, {
        "option": "None of the time",
        "score": 1
    }]
}, {
    "title":
    "Work Performance",
    "question":
    "During the Past month, have you feared losing your job because of your health?",
    "options": [{
        "option": "All of the time",
        "score": 1
    }, {
        "option": "Most of the time",
        "score": 2
    }, {
        "option": "Some of the time",
        "score": 3
    }, {
        "option": "None of the time",
        "score": 4
    }]
}]

questionaire_questions_new = [{
    "title":
    "Daily Activities",
    "question":
    "Can Martha feed herself without assistance or does she need help during meal times?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Daily Activities",
    "question":
    "I see. Moving on, when it comes to dressing, can Martha put on her clothes without any assistance? Or does she struggle with certain aspects like buttons, zippers, or shoe laces?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Daily Activities",
    "question":
    "Thank you for sharing. Now, regarding toileting, can Martha use the toilet independently, or does she require some assistance for certain parts, like cleaning or flushing?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Daily Activities",
    "question":
    "Thank you for being patient with these questions. When it comes to personal hygiene, can Martha brush her teeth, comb her hair, and wash her face and hands without assistance?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Daily Activities",
    "question":
    "Okay, and for bathing, is Martha able to bathe herself without any help? Or does she need assistance with some parts, like washing her back or feet?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Mobility",
    "question":
    "Got it. How about transferring? Is Martha able to move in and out of her bed or chair on her own? Or does she need some help or an assistive device for that?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Mobility",
    "question":
    "How would you rate Martha’s ability to walk a block or climb a flight of stairs or more?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Cognition",
    "question":
    "Has Martha experienced any difficulties with memory, attention, or problem-solving that affected daily life?",
    "options": [{
        "option": "Rarely or never",
        "score": 3
    }, {
        "option": "Occasionally",
        "score": 2
    }, {
        "option": "Frequently",
        "score": 1
    }, {
        "option": "Constantly",
        "score": 0
    }]
}, {
    "title":
    "Cognition",
    "question":
    "Thank you. Has Martha exhibited difficulties in recognizing their environment or wandered away from home lately?",
    "options": [{
        "option": "Rarely or never",
        "score": 3
    }, {
        "option": "Occasionally",
        "score": 2
    }, {
        "option": "Frequently",
        "score": 1
    }, {
        "option": "Constantly",
        "score": 0
    }]
}, {
    "title":
    "Cognition",
    "question":
    "And has Martha faced difficulties remembering date and month or familiar faces?",
    "options": [{
        "option": "Rarely or never",
        "score": 3
    }, {
        "option": "Occasionally",
        "score": 2
    }, {
        "option": "Frequently",
        "score": 1
    }, {
        "option": "Constantly",
        "score": 0
    }]
}, {
    "title":
    "Mind",
    "question":
    "Has Martha felt agitated, anxious, irritable, or depressed?",
    "options": [{
        "option": "Rarely or never",
        "score": 3
    }, {
        "option": "Occasionally",
        "score": 2
    }, {
        "option": "Frequently",
        "score": 1
    }, {
        "option": "Constantly",
        "score": 0
    }]
}, {
    "title":
    "Mind",
    "question":
    "Thank you for answering. From late afternoon till night, has Martha shown increased confusion, disorientation, restlessness, or difficulty sleeping?",
    "options": [{
        "option": "Rarely or never",
        "score": 3
    }, {
        "option": "Occasionally",
        "score": 2
    }, {
        "option": "Frequently",
        "score": 1
    }, {
        "option": "Constantly",
        "score": 0
    }]
}, {
    "title":
    "Independence (IADL)",
    "question":
    "Thanks for that. Now, let's move on to some instrumental activities. Can Martha prepare and cook meals by herself? Or does she require help with certain dishes or prefer pre-prepared meals?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Independence (IADL)",
    "question":
    "Understood. When it comes to her medications, can Martha manage and take them correctly without supervision? Or does she sometimes forget and need reminders?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Independence (IADL)",
    "question":
    "Alright. How about money management? Can she handle her finances, pay bills, and manage money without assistance?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Independence (IADL)",
    "question":
    "Thanks for sharing. Does Martha still use the phone? Is she able to make and answer calls independently?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Independence (IADL)",
    "question":
    "Got it. Regarding housekeeping, can Martha manage household chores on her own, or does she require some assistance?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Independence (IADL)",
    "question":
    "Thank you. When it comes to shopping, can Martha shop for groceries and necessities independently? Or does she need some help or prefer to make only small purchases?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Independence (IADL)",
    "question":
    "And concerning transportation, is Martha still driving or using public transport by herself? Or does she require assistance or uses pre-arranged transportation?",
    "options": [{
        "option": "Manages independently",
        "score": 3
    }, {
        "option": "Requires occasional assistance",
        "score": 2
    }, {
        "option": "Needs frequent assistance",
        "score": 1
    }, {
        "option": "Requires full assistance",
        "score": 0
    }]
}, {
    "title":
    "Social",
    "question":
    "Now, thinking about Martha’s social activity. Has Martha had any difficulty interacting with relatives or friends or participating in community or social activities?",
    "options": [{
        "option": "No difficulty, socializes independently",
        "score": 3
    }, {
        "option": "Some difficulty",
        "score": 2
    }, {
        "option": "Much difficulty",
        "score": 1
    }, {
        "option": "Cannot socialize without assistance",
        "score": 0
    }]
}, {
    "title":
    "Social",
    "question":
    "How frequently does Martha engage in social activities or maintain relationships?",
    "options": [{
        "option": "Regularly",
        "score": 3
    }, {
        "option": "Occasionally",
        "score": 2
    }, {
        "option": "Rarely",
        "score": 1
    }, {
        "option": "Almost never or never",
        "score": 0
    }]
}]

# Store the scores for each title
title_scores = {
    question["title"]: 0
    for question in questionaire_questions_new
}


def get_user_choice(question, options):
  print(question)
  for i, option in enumerate(options, 1):
    print(f"{i}. {option}")
  while True:
    choice = input("Enter the number corresponding to your choice: ")
    if choice.isdigit() and 1 <= int(choice) <= len(options):
      return options[int(choice) - 1]
    print("Invalid choice. Please enter a valid number.")


def get_user_response(question):
  return input(question + " ")


#END of checkin*************************************************


def geocode(address, access_token):
  if not address:
    return None, None

  url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?access_token={access_token}'
  response = requests.get(url)
  data = response.json()
  if data['features']:
    longitude, latitude = data['features'][0]['center']
    return latitude, longitude
  else:
    return None, None


#added to github

index = faiss.read_index("training.index")

with open("faiss.pkl", "rb") as f:
  store = pickle.load(f)

store.index = index

with open("training/master.txt", "r") as f:
  promptTemplate = f.read()

prompt = Prompt(template=promptTemplate,
                input_variables=["history", "context", "question"])

llmChain = LLMChain(prompt=prompt,
                    llm=OpenAIChat(
                        temperature=0.5,
                        model_name="gpt-3.5-turbo",
                        openai_api_key=os.environ["OPENAI_API_KEY"]))

history = []

app = Flask(__name__)
cors = CORS(app)


@app.route("/", methods=["GET"])
def index():
  return "API Online"


@app.route("/", methods=["POST"])
def ask():

  try:
    reqData = request.get_json()
    if reqData['secret'] == os.environ["API_SECRET"]:
      user_question = reqData['question']

      # Process user location only if needed
      if "live" in user_question.lower() or "need" in user_question.lower():
        location = user_question
        latitude, longitude = geocode(location, os.environ["MAP_KEY"])
        answer = "Please provide your complete location so that we can find the nearest required professional for you: "
      else:
        docs = store.similarity_search(user_question)
        contexts = [
            f"Context {i}:\n{doc.page_content}" for i, doc in enumerate(docs)
        ]
        answer = llmChain.predict(question=user_question,
                                  context="\n\n".join(contexts),
                                  history=history)

      history.append(f"Human: {user_question}")
      history.append(f"Bot: {answer}")

      return jsonify({"answer": answer, "success": True})
    else:
      return jsonify({
          "answer": None,
          "success": False,
          "message": "Unauthorised"
      })
  except Exception as e:
    return jsonify({"answer": None, "success": False, "message": str(e)}), 400


@app.route('/get_question', methods=['GET'])
def get_question():
  # Check if the API_SECRET from the frontend matches the one stored in the environment
  api_secret_from_frontend = request.headers.get('X-API-SECRET')
  if api_secret_from_frontend != API_SECRET:
    return jsonify({'error': 'Unauthorized access'}), 401

  current_week = len(data['check_ins']) + 1
  current_question_index = data['check_ins'][-1].get(
      f"Week {current_week}", {}).get('current_question_index', 0)

  if current_question_index >= len(questions):
    return jsonify(
        {'message': 'All questions for this week have been answered!'})

  current_question_key = list(questions.keys())[current_question_index]
  current_question = questions[current_question_key]

  if isinstance(current_question, dict) and 'options' in current_question:
    options = current_question['options']
    formatted_options = [
        f"{i+1}. {option}" for i, option in enumerate(options)
    ]
    question_text = {
        'question': current_question['question'],
        'options': formatted_options
    }
  else:
    question_text = {'question': current_question}

  return jsonify({'question': question_text})


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
  # Check if the API_SECRET from the frontend matches the one stored in the environment
  api_secret_from_frontend = request.headers.get('X-API-SECRET')
  if api_secret_from_frontend != API_SECRET:
    return jsonify({'error': 'Unauthorized access'}), 401

  try:
    user_response = request.json.get('answer')
    if not user_response:
      return jsonify({'error': 'Invalid request'}), 400

    current_week = len(data['check_ins']) + 1

    # Check if this week's entry exists in data, if not, create a new entry
    if f"Week {current_week}" not in data['check_ins'][-1]:
      data['check_ins'][-1][f"Week {current_week}"] = {
          'current_question_index': 0
      }

    current_question_index = data['check_ins'][-1][f"Week {current_week}"][
        'current_question_index']

    # Get the list of questions and their keys
    question_keys = list(questions.keys())
    question_count = len(question_keys)

    # Check if all questions have been answered for this week
    if current_question_index >= question_count:
      return jsonify(
          {'message': 'All questions for this week have been answered!'})

    # Get the current question and options (if applicable)
    current_question_key = question_keys[current_question_index]
    current_question = questions[current_question_key]
    if isinstance(current_question, dict) and 'options' in current_question:
      options = current_question['options']
      if user_response.isdigit() and 1 <= int(user_response) <= len(options):
        user_response = options[int(user_response) - 1]

    # Store the user's response for the current question along with the question number
    data['check_ins'][-1][f"Week {current_week}"][
        f"Q{current_question_index + 1}"] = {
            'question': current_question,
            'response': user_response
        }

    # Increment the current question index for the next iteration
    data['check_ins'][-1][f"Week {current_week}"][
        'current_question_index'] = current_question_index + 1

    # If all questions are answered, move to the next week
    if data['check_ins'][-1][f"Week {current_week}"][
        'current_question_index'] >= question_count:
      data['check_ins'].append(
          {})  # Create a new empty entry for the next week

    # Save the data in the JSON file
    with open(json_file_path, 'w') as json_file:
      json.dump(data, json_file, indent=4)

    return jsonify({
        'message': 'Response saved successfully!',
        'question': current_question
    })

  except Exception as e:
    # Manually print the traceback to the console
    traceback.print_exc()

    return jsonify({'error': 'Internal Server Error'}), 500


# ... (previously defined code)


@app.route('/perform_action', methods=['POST'])
def perform_action():
  # Perform the desired action here
  #to add data
  with open("user_responses.json", 'r') as json_file:
    json_contents = json_file.read()

  # Write the contents to the text file
  with open("training/facts/user_responses.txt", 'w') as text_file:
    text_file.write(json_contents)
  #to train
  trainingData = list(Path("training/facts/").glob("**/*.*"))
  data = []
  for training in trainingData:
    with open(training) as f:
      print(f"Add {f.name} to dataset")
      data.append(f.read())

  textSplitter = RecursiveCharacterTextSplitter(chunk_size=2000,
                                                chunk_overlap=0)

  docs = []
  for sets in data:
    docs.extend(textSplitter.split_text(sets))
  embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
  store = FAISS.from_texts(docs, embeddings)

  faiss.write_index(store.index, "training.index")
  store.index = None

  with open("faiss.pkl", "wb") as f:
    pickle.dump(store, f)

  return jsonify({"message": "Action performed successfully!"})


# Load stored questionnaire data from JSON file

# Load stored questionnaire data from JSON file

try:
  with open("questionnaire_data.json", "r") as file:
    stored_questionnaire_data = json.load(file)
except FileNotFoundError:
  stored_questionnaire_data = {}

# Define a set to keep track of the questions that have been asked
asked_questions = set()


@app.route('/get_questionnaire_question', methods=['GET'])
def get_questionnaire_question():
  # Filter out questions that have already been asked
  available_questions = [
      question for question in questionaire_questions_new
      if question["question"] not in asked_questions
  ]

  if available_questions:
    # Retrieve a random question from the available questions
    question = random.choice(available_questions)
    asked_questions.add(
        question["question"])  # Add the asked question to the set
    return jsonify({
        "question":
        question["question"],
        "options": [option["option"] for option in question["options"]]
    })
  else:
    # If all questions have been asked, return a message or handle as needed
    return jsonify({"message": "All questions have been asked."})


@app.route('/submit_questionnaire_answer', methods=['POST'])
def submit_questionnaire_answer():
  try:
    data = request.json
    answer_option = data["answer"]

    # Update stored questionnaire data
    patient_first_name = "Martha"  # Fixed patient's first name
    if patient_first_name not in stored_questionnaire_data:
      stored_questionnaire_data[patient_first_name] = {}

    # Get the last asked question
    last_asked_question = list(asked_questions)[-1]

    # Find the question in the questionnaire_questions list
    question_match = None
    for question in questionaire_questions_new:
      if question["question"] == last_asked_question:
        question_match = question
        break

    if question_match is None:
      return jsonify({
          "success": False,
          "error": "Last asked question not found in questionnaire"
      })

    # Find the score for the selected answer_option
    score = None
    for option in question_match["options"]:
      if option["option"] == answer_option:
        score = option["score"]
        break

    if score is None:
      return jsonify({
          "success": False,
          "error": "Answer option not found in last asked question"
      })

    # Store the data in the JSON file
    title = question_match["title"]
    if title not in stored_questionnaire_data[patient_first_name]:
      stored_questionnaire_data[patient_first_name][title] = {
          "questions": [],
          "answers": [],
          "scores": [],
          "total_score": 0
      }

    stored_questionnaire_data[patient_first_name][title]["questions"].append(
        last_asked_question)
    stored_questionnaire_data[patient_first_name][title]["answers"].append(
        answer_option)
    stored_questionnaire_data[patient_first_name][title]["scores"].append(
        score)
    stored_questionnaire_data[patient_first_name][title][
        "total_score"] += score

    # Update JSON file
    with open("questionnaire_data.json", "w") as file:
      json.dump(stored_questionnaire_data, file, indent=4)

    return jsonify({"success": True})

  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


@app.route('/calculate_questionnaire_results', methods=['GET'])
def calculate_questionnaire_results():
  results = {}
  for patient, patient_data in stored_questionnaire_data.items():
    results[patient] = {}
    for title, title_data in patient_data.items():
      results[patient][title] = title_data["total_score"]

  # Convert the results to the desired format
  converted_results = {}
  for patient, title_scores in results.items():
    for title, score in title_scores.items():
      if patient not in converted_results:
        converted_results[patient] = {}
      converted_results[patient][title] = score

  return jsonify(converted_results)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=3000)
