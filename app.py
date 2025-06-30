from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from transformers import pipeline
import spacy
import os

# Initialize the app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    fitness_level = db.Column(db.String(50), nullable=False)
    goal = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'fitness_level': self.fitness_level,
            'goal': self.goal
        }

# Load the Hugging Face model for intent recognition
try:
    intent_recognizer = pipeline("zero-shot-classification")
except Exception as e:
    intent_recognizer = None
    print(f"Error loading Hugging Face model: {e}")

# Load the spaCy model for NER
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# List of possible intents related to fitness
intents = ['weight_loss', 'muscle_gain', 'workout_schedule', 'nutrition', 'fitness_goals', 'request_plan', 'request_meal_plan']

# Define functions for intent recognition and NER
def recognize_intent(user_input):
    result = intent_recognizer(user_input, candidate_labels=intents)
    return result['labels'][0]

def extract_entities(user_input):
    doc = nlp(user_input)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

def generate_workout_plan(profile):
    goal = profile.get('goal', 'general_fitness')
    level = profile.get('fitness_level', 'beginner')
    plan = f"Here is a {level} workout plan for {goal}:\n\n"

    if goal == 'weight_loss':
        if level == 'beginner':
            plan += "- **Monday:** 30 minutes of Light Cardio (Jogging, Cycling)\n"
            plan += "- **Wednesday:** 30 minutes of Brisk Walking\n"
            plan += "- **Friday:** 30 minutes of Light Cardio (Swimming, Elliptical)\n"
        else: # Intermediate / Advanced
            plan += "- **Monday:** 45 minutes of High-Intensity Interval Training (HIIT)\n"
            plan += "- **Wednesday:** 45 minutes of Strength Training (Full Body)\n"
            plan += "- **Friday:** 60 minutes of Moderate Cardio (Running, Cycling)\n"
    elif goal == 'muscle_gain':
        if level == 'beginner':
            plan += "- **Monday:** Full Body Strength (Squats, Push-ups, Rows)\n"
            plan += "- **Wednesday:** Full Body Strength (Lunges, Overhead Press, Lat Pulldowns)\n"
            plan += "- **Friday:** Full Body Strength (Deadlifts, Bench Press, Bicep Curls)\n"
        else: # Intermediate / Advanced
            plan += "- **Monday:** Upper Body Strength (Bench Press, Rows, Shoulder Press)\n"
            plan += "- **Tuesday:** Lower Body Strength (Squats, Deadlifts, Leg Press)\n"
            plan += "- **Thursday:** Upper Body Strength (Pull-ups, Incline Press, Lateral Raises)\n"
            plan += "- **Friday:** Lower Body Strength (Lunges, Hamstring Curls, Calf Raises)\n"
    else: # General Fitness
        plan += "- **Monday:** 30 minutes of Cardio\n"
        plan += "- **Wednesday:** 30 minutes of Full Body Strength Training\n"
        plan += "- **Friday:** 30 minutes of your favorite activity (hike, swim, sport)\n"
    
    plan += "\nRemember to warm up before each workout and cool down afterward."
    return plan

def generate_meal_plan(profile):
    goal = profile.get('goal', 'general_fitness')
    plan = f"Here is a sample meal plan for your goal of {goal}:\n\n"

    if goal == 'weight_loss':
        plan += "- **Breakfast:** Oatmeal with berries and a handful of nuts.\n"
        plan += "- **Lunch:** Grilled chicken salad with mixed greens and a vinaigrette dressing.\n"
        plan += "- **Dinner:** Baked salmon with quinoa and steamed vegetables.\n"
        plan += "- **Snack:** Greek yogurt or an apple.\n"
    elif goal == 'muscle_gain':
        plan += "- **Breakfast:** Scrambled eggs with spinach and whole-wheat toast.\n"
        plan += "- **Lunch:** Lean beef with brown rice and broccoli.\n"
        plan += "- **Dinner:** Chicken breast, sweet potatoes, and a side salad.\n"
        plan += "- **Snack:** Protein shake or a handful of almonds.\n"
    else: # General Fitness
        plan += "- **Breakfast:** Smoothie with fruit, spinach, and protein powder.\n"
        plan += "- **Lunch:** Turkey and avocado sandwich on whole-wheat bread.\n"
        plan += "- **Dinner:** Pasta with a lean meat sauce and a side of vegetables.\n"
        plan += "- **Snack:** A piece of fruit or cottage cheese.\n"
    
    plan += "\nThis is a sample plan. Adjust portion sizes based on your needs and consult a nutritionist for detailed advice."
    return plan

def generate_response(intent, entities, profile=None):
    if not profile:
        return "Sorry, I can't provide a personalized response without your profile. Please start over."

    name = profile.get('name', 'there')
    goal = profile.get('goal', 'your goal')
    level = profile.get('fitness_level', 'your level')

    if intent == 'weight_loss':
        response = f"Hi {name}! For weight loss, focusing on cardio and a calorie deficit is key. As a {level}, I'd suggest starting with 3 days of light cardio like jogging or cycling."
    elif intent == 'muscle_gain':
        response = f"Hi {name}! To achieve your muscle gain goal, you'll want to focus on strength training and a protein-rich diet. For a {level}, a full-body workout 3 times a week is a great start."
    elif intent == 'workout_schedule':
        response = f"Hi {name}! Based on your goal of {goal} and level as a {level}, how many days a week can you commit to working out? I can create a schedule for you."
    elif intent == 'nutrition':
        response = f"Hi {name}! For your goal of {goal}, would you prefer a high-protein or low-calorie meal plan?"
    elif intent == 'request_plan':
        response = generate_workout_plan(profile)
    elif intent == 'request_meal_plan':
        response = generate_meal_plan(profile)
    else:
        response = f"Hi {name}, I'm not sure I understand. You can ask me to 'create a workout plan' or 'suggest a meal plan'."
    
    if entities and intent not in ['request_plan', 'request_meal_plan']:
        response += " I see you mentioned " + ', '.join([ent[0] for ent in entities]) + ". I can help with that!"
    
    return response

# Route to serve the web app
@app.route('/')
def home():
    # If user is already in session, redirect to chat
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return redirect(url_for('chat_page'))
    # Otherwise, render the profile creation page
    return render_template('profile.html')

@app.route('/start', methods=['POST'])
def start_chat():
    # Create a new user in the database
    new_user = User(
        name=request.form.get('name'),
        age=request.form.get('age'),
        gender=request.form.get('gender'),
        fitness_level=request.form.get('fitness_level'),
        goal=request.form.get('goal')
    )
    db.session.add(new_user)
    db.session.commit()
    
    # Save user ID to session and clear history
    session['user_id'] = new_user.id
    session['history'] = []
    return redirect(url_for('chat_page'))

@app.route('/chat')
def chat_page():
    # Check if user exists, otherwise redirect to home
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    user = User.query.get(session['user_id'])
    if not user:
        # If user ID in session is invalid, clear it
        session.pop('user_id', None)
        return redirect(url_for('home'))

    return render_template('index.html', history=session.get('history', []), profile=user.to_dict())

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form['user_input']
    
    # Ensure user is in session
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('home'))

    # Ensure history is in session
    if 'history' not in session:
        session['history'] = []

    try:
        if intent_recognizer is None:
            raise RuntimeError("Intent recognizer model could not be loaded.")
        # Recognize the intent and extract entities
        intent = recognize_intent(user_input)
        entities = extract_entities(user_input)
        # Generate the response using the user's profile
        response = generate_response(intent, entities, user.to_dict())
    except Exception as e:
        response = f"Sorry, there was an error processing your request: {str(e)}"
    
    # Store chat history in session
    session['history'].append({'user': user_input, 'bot': response})
    session.modified = True
    
    return render_template('index.html', history=session['history'], profile=user.to_dict())

@app.route('/logout')
def logout():
    # Clear the session to log the user out
    session.clear()
    return redirect(url_for('home'))

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)
