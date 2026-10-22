import os
import sys

# Read the current app.py
with open('app.py', 'r') as f:
    content = f.read()

# Make sure it hasn't been patched already
if 'educonnect_data.json' in content:
    print('Already patched.')
    sys.exit(0)

# Replace the mock DB initialization
stub_to_replace = """# Mock Database (Since no DB is configured yet)
# We store registered teachers here. 
# Structure: {id: int, name: str, email: str, phone: str, experience: int, subject: str, class_level: str, approved: bool, profile_pic: str}
MOCK_TEACHERS_DB = []
TEACHER_ID_COUNTER = 1

MOCK_STUDENTS_DB = []
STUDENT_ID_COUNTER = 1

# Mock database for tuition requests
# Structure: {id: int, teacher_id: int, student_id: int, student_name: str, student_phone: str, status: str}
MOCK_TUITION_REQUESTS = []
REQUEST_ID_COUNTER = 1

# Mock database for chat messages
# Structure: {id: int, request_id: int, sender_id: int, sender_role: str, message: str, timestamp: str}
MOCK_MESSAGES = []
MESSAGE_ID_COUNTER = 1

# Mock database for Previous Year Questions
# Structure: {id: int, title: str, board: str, class_level: str, subject: str, year: str, size: str}
MOCK_PYQ_DB = [
    {'id': 1, 'title': 'Physics Board Exam', 'board': 'cbse', 'class_level': '12', 'subject': 'physics', 'year': '2025', 'size': '2.4 MB'},
    {'id': 2, 'title': 'Mathematics Main', 'board': 'cbse', 'class_level': '12', 'subject': 'maths', 'year': '2025', 'size': '3.1 MB'},
    {'id': 3, 'title': 'Chemistry Solutions', 'board': 'state', 'class_level': '10', 'subject': 'chemistry', 'year': '2024', 'size': '1.8 MB'},
    {'id': 4, 'title': 'English Literature', 'board': 'cbse', 'class_level': '10', 'subject': 'english', 'year': '2024', 'size': '1.2 MB'},
    {'id': 5, 'title': 'Biology Theory', 'board': 'state', 'class_level': '12', 'subject': 'biology', 'year': '2024', 'size': '2.8 MB'},
    {'id': 6, 'title': 'Science Basics', 'board': 'cbse', 'class_level': '8', 'subject': 'science', 'year': '2025', 'size': '1.5 MB'}
]
PYQ_ID_COUNTER = 7"""

replacement = """import json

DATA_FILE = 'educonnect_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "teachers": [], "teacher_id_counter": 1,
        "students": [], "student_id_counter": 1,
        "requests": [], "request_id_counter": 1,
        "messages": [], "message_id_counter": 1,
        "pyqs": [], "pyq_id_counter": 1
    }

def save_data():
    data = {
        "teachers": MOCK_TEACHERS_DB, "teacher_id_counter": TEACHER_ID_COUNTER,
        "students": MOCK_STUDENTS_DB, "student_id_counter": STUDENT_ID_COUNTER,
        "requests": MOCK_TUITION_REQUESTS, "request_id_counter": REQUEST_ID_COUNTER,
        "messages": MOCK_MESSAGES, "message_id_counter": MESSAGE_ID_COUNTER,
        "pyqs": MOCK_PYQ_DB, "pyq_id_counter": PYQ_ID_COUNTER
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

_data = load_data()
MOCK_TEACHERS_DB = _data["teachers"]
TEACHER_ID_COUNTER = _data["teacher_id_counter"]
MOCK_STUDENTS_DB = _data["students"]
STUDENT_ID_COUNTER = _data["student_id_counter"]
MOCK_TUITION_REQUESTS = _data["requests"]
REQUEST_ID_COUNTER = _data["request_id_counter"]
MOCK_MESSAGES = _data["messages"]
MESSAGE_ID_COUNTER = _data["message_id_counter"]
MOCK_PYQ_DB = _data["pyqs"]
PYQ_ID_COUNTER = _data["pyq_id_counter"]"""

if stub_to_replace not in content:
    print('Could not find exact stub!')
    sys.exit(1)

content = content.replace(stub_to_replace, replacement)

# Add save calls after mutations
content = content.replace("REQUEST_ID_COUNTER += 1", "REQUEST_ID_COUNTER += 1\\n        save_data()")
content = content.replace("STUDENT_ID_COUNTER += 1", "STUDENT_ID_COUNTER += 1\\n            save_data()")
content = content.replace("TEACHER_ID_COUNTER += 1", "TEACHER_ID_COUNTER += 1\\n            save_data()")
content = content.replace("MESSAGE_ID_COUNTER += 1", "MESSAGE_ID_COUNTER += 1\\n            save_data()")
content = content.replace("PYQ_ID_COUNTER += 1", "PYQ_ID_COUNTER += 1\\n    save_data()")

content = content.replace("MOCK_TEACHERS_DB.remove(teacher)", "MOCK_TEACHERS_DB.remove(teacher)\\n                save_data()")
content = content.replace("req['status'] = 'accepted' if action == 'accept' else 'declined'", "req['status'] = 'accepted' if action == 'accept' else 'declined'\\n        save_data()")
content = content.replace("session['user_video'] = teacher['video_url']", "session['user_video'] = teacher['video_url']\\n        save_data()")
content = content.replace("teacher['approved'] = True", "teacher['approved'] = True\\n                save_data()")

with open('app.py', 'w') as f:
    f.write(content)
print('Successfully patched app.py!')
