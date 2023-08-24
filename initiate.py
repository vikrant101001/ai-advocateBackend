import json

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

# Load existing data from the JSON file, if any
try:
    with open('user_responses.json', 'r') as json_file:
        data = json.load(json_file)
except FileNotFoundError:
    data = {'check_ins': []}

# Determine the current week based on existing data
current_week = len(data['check_ins']) + 1

# Define the questions and gather user information
questions = {
    'Q1': "How is Martha's mood today?",
    'Q2': "Has Martha experienced any of the following in the past week?",
    'Q3': "How long did Martha sleep yesterday?",
    'Q4': "How was Martha's sleep yesterday?",
    'Q5': "Has Martha experienced any vomiting in the past week? (yes/no)",
    'Q5.1': "How many times in the past week?",
    'Q5.2': "For how long did the episode last?",
    'Q5.3': "How did it impact Martha's daily activities?"
}

# Q1
options_q1 = ["Agitated", "Angry", "Frustrated", "Lost", "Neutral", "Happy"]
data['check_ins'].append({f"Week {current_week}": {questions['Q1']: get_user_choice(questions['Q1'], options_q1)}})

# Q2
options_q2 = ["Increasing irritability", "Wandering", "Delusions"]
data['check_ins'][-1][f"Week {current_week}"][questions['Q2']] = get_user_choice(questions['Q2'], options_q2)

# Q3
data['check_ins'][-1][f"Week {current_week}"][questions['Q3']] = get_user_response(questions['Q3'])

# Q4
options_q4 = ["Well rested", "Woke up once", "Woke up 2 or 3 times", "Woke up 4 or more times", "Disrupted"]
data['check_ins'][-1][f"Week {current_week}"][questions['Q4']] = get_user_choice(questions['Q4'], options_q4)

# Q5
data['check_ins'][-1][f"Week {current_week}"][questions['Q5']] = get_user_choice(questions['Q5'], ["yes", "no"])

# If Yes to Q5, ask further questions
if data['check_ins'][-1][f"Week {current_week}"][questions['Q5']] == "yes":
    data['check_ins'][-1][f"Week {current_week}"][questions['Q5.1']] = get_user_choice(questions['Q5.1'], ["Once only", "2 to 3 times", "4 to 5 times", "More than 5 times"])
    data['check_ins'][-1][f"Week {current_week}"][questions['Q5.2']] = get_user_choice(questions['Q5.2'], ["Less than 30 minutes", "30 mins to an hour", "1 to 4 hours", "Full day"])
    data['check_ins'][-1][f"Week {current_week}"][questions['Q5.3']] = get_user_choice(questions['Q5.3'], ["Difficulty eating and drinking", "Difficulty walking", "Fatigue", "Severe dehydration"])

# Save the data (questions and responses) in a JSON file
with open('user_responses.json', 'w') as json_file:
    json.dump(data, json_file, indent=4)

print("Responses saved successfully!")
