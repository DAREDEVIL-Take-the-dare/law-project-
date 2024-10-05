from flask import Flask, render_template, request, session, redirect, jsonify, flash
import ultralytics
import mysql.connector
import os
import bcrypt
import openai
import cv2
import base64

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

DB = mysql.connector.connect(
    host="localhost",
    user="root",
    password="abhinav",
    database="law"
)

cursor = DB.cursor()
app.secret_key = os.urandom(24)

#openai.api_key = "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"

# Store conversation history
conversation = []


def detect(buf):
    model = ultralytics.YOLO('../yolo_weights/yolov8l.pt')
    results = model.predict(buf, conf=0.5, show=True)
    result = results[0]
    class_names = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle',
                   4: 'airplanes', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat',
                   9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter',
                   13: 'bench', 14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep',
                   19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe',
                   24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie',
                   28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball',
                   33: 'kite', 34: 'baseball bat', 35: 'baseball glove', 36: 'skateboard',
                   37: 'surfboard', 38: 'tennis racket', 39: 'bottle', 40: 'wine glass',
                   41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana',
                   47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot',
                   52: 'hot dog', 53: 'pizza', 54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch',
                   58: 'potted plant', 59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv',
                   63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone',
                   68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator',
                   73: 'book', 74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier',
                   79: 'toothbrush'}

    class_namess = []
    for box in result.boxes:
        class_id = class_names[box.cls[0].item()]
        cords = box.xyxy[0].tolist()
        cords = [round(x) for x in cords]
        conf = round(box.conf[0].item(), 2)
        print("Object type:", class_id)
        print("Coordinates:", cords)
        print("Probability:", conf)
        print("---")
        class_namess.append(class_id)
        #cv2.waitKey(0)
       #cv2.destroyAllWindows()
    return class_namess, str(len(result.boxes))


def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# def get_description(obj):
#     # Query the database for the description based on the object class
#     query = "SELECT description FROM legal_info WHERE topic = %s"
#     cursor.execute(query, (obj,))
#     obj_description = [row[0] for row in cursor.fetchall()]
#     return obj_description

@app.route('/')
def login():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute('SELECT first_name FROM users WHERE usersid=%s', (user_id,))
        username = cursor.fetchone()[0]  # Assuming the username is in the first column
        return render_template('homepage.html', username=username)
    else:
        return render_template('homepage.html')


@app.route('/home')
def home():
    if 'user_id' in session:
        return redirect('/')
    else:
        return render_template("login.html")



@app.route('/image', methods=['GET'])
def imagesearch():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute('SELECT username FROM users WHERE usersid =%s', (user_id,))
        username = cursor.fetchone()[0]  # Assuming the username is in the first column
        return render_template('image.html', username=username)
    else:
        return render_template('image.html')


@app.route('/image', methods=['POST'])
def image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'})

    image_file = request.files['image']

    # Check if the file has a valid name and extension
    if image_file.filename == '' or not allowed_file(image_file.filename):
        return jsonify({'error': 'Invalid file name or extension'})

    # Save the file to the upload folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
    image_file.save(file_path)

    obj, c = detect(file_path)


    prompt = f"{obj} for given object name tell me laws and rights provided in prompt: constitution of India\n"
    prompt += "Answer the question related to the Constitution of India.\n"
    prompt += f"In your Answer include laws and rights related to object name {obj}.\n"
    prompt += "In your answer, include relevant articles and laws provided by the Constitution of India.\n"

        # Make a request to the OpenAI API
    response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150  # You can adjust this parameter based on your needs
        )

    output_description = [response['choices'][0]['text']]
    print(output_description)
    result = {
            'object_names': obj,
            'object_description': output_description
        }
    if obj in ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
               'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
               'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
               'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
               'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
               'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
               'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard',
               'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
               'scissors', 'teddy bear', 'hair drier', 'toothbrush']:
        return render_template('image.html', result=result)
    else:
        result = {
            'object_names': obj,
            'object_description': output_description
         }
        return render_template('image.html', result=result)



# LOGIN SECTION OF THE WEBSITE


@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/login_validation', methods=['POST'])
def login_validation():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect('/home')
        else:
            flash('Incorrect email or password. Please try again.', 'error')
            return render_template('login.html', login_failed=True)


@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        # Extract registration form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        cpass = request.form['confirm_password']
        if cpass == password:
             hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
             cursor.execute('INSERT INTO users (first_name,last_name, email, password) VALUES (%s, %s, %s,%s)',
                       (first_name,last_name, email, hashed_password))

        # Commit the changes to the database
             DB.commit()

             cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
             myuser = cursor.fetchone()
             session['user_id'] = myuser[0]

             msg = 'Registration successful! Please log in.'
             return redirect('/home')

    return redirect('/register')  # Assuming you have a 'register.html' template for the registration form

@app.route('/doc')
def doc():
    return render_template("doc.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/chat')
def chat():
    # Format the conversation to include both user and assistant messages
    formatted_conversation = [{"role": message["role"], "content": message["content"]} for message in conversation]
    return render_template('chat.html', conversation=formatted_conversation)

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.form['user_input']
    user_language = request.form['user_language']
    if user_language == "":
        user_language = "english"
    # Add user message to conversation
    print(user_language)
    conversation.append({"role": "user", "content": user_message})

    # Handle specific greetings or start messages
    if user_message.lower() in ['hi', 'hello', 'hey', 'shru karo', 'start', 'who are you']:
        conversation.append({"role": "assistant",
                             "content": 'Hi there! I am JANSEVAK. How can I assist you today?'})
        return render_template('chat.html', conversation=conversation)

    # Handle inappropriate or empty queries
    elif user_message.lower() in ["", "fuck_you", "how to kill user","kill you"]:
        conversation.append({"role": "assistant",
                             "content": "I'm sorry, but I cannot respond to inappropriate queries. Please rephrase your question."})
        return render_template('chat.html', conversation=conversation)

    else:
        # Construct prompt without revealing the user's question
        prompt = f" prompt: Constitution of India Legal Rights,legal document\n"
        prompt += "Answer the question related to the Constitution of India.\n"
        prompt += "In your answer, include relevant articles and laws provided by the Constitution of India.\n"
        prompt += "In your answer, include relevant punishment or compensation money or both under relevent article and law provided by the Constitution of India.\n"
        prompt += "In your answer, include relevant  compensation amount fair under relevent article and law provided by the Constitution of India.\n"
        prompt += "In your answer, include at most one relevant example of cases for relevent article and law provided by the Constitution of India.\n"
        prompt += f"User Query: {user_message}\n"  # Include user query for model understanding

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=180
        )

        # Extract assistant's reply from the response
        reply = response["choices"][0]["text"]

        # Add assistant's reply to conversation without revealing the user's question
        conversation.append({"role": "assistant", "content": reply})
        return render_template('chat.html', conversation=conversation)

@app.route("/know_rights")
def rights():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute('SELECT first_name FROM users WHERE usersid=%s', (user_id,))
        username = cursor.fetchone()[0]  # Assuming the username is in the first column
        return render_template('Final.html', username=username)
    else:
        return render_template('Final.html')

@app.route("/document")
def document():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute('SELECT first_name FROM users WHERE usersid=%s', (user_id,))
        username = cursor.fetchone()[0]  # Assuming the username is in the first column
        return render_template('document.html', username=username)
    else:
        return render_template('document.html')


@app.route("/aadhar")
def aadhar():
    return render_template('docsec/adhaar.html')


@app.route("/hotline")
def hotline():
    return render_template('hotline.html')


@app.route("/hcard")
def hcard():
    return render_template('hcard.html')

@app.route("/learn")
def learn():
    return render_template('learn.html')


@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/lvid")
def lvid():
    return render_template('lvid.html')

@app.route("/update")
def update():
    return render_template('updates.html')

if __name__ == "__main__":
    app.run()

