from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'super_secret_educonnect_key'

import sqlite3

DATABASE = 'educonnect.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Helper to dictionary-ize rows
def row_to_dict(row):
    return dict(row) if row else None

@app.route("/")
def index():
    # Pass up to 4 approved teachers to display on the homepage
    conn = get_db_connection()
    featured = conn.execute('SELECT * FROM teachers WHERE approved = 1 LIMIT 4').fetchall()
    conn.close()
    return render_template("index.html", featured_teachers=featured)

@app.route("/teachers")
def teachers():
    conn = get_db_connection()
    search_query = request.args.get('search', '').lower()
    
    if search_query:
        query = "SELECT * FROM teachers WHERE approved = 1 AND (LOWER(name) LIKE ? OR LOWER(subject) LIKE ?)"
        approved_teachers = conn.execute(query, (f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        approved_teachers = conn.execute('SELECT * FROM teachers WHERE approved = 1').fetchall()
        
    conn.close()
    return render_template("teachers.html", teachers=approved_teachers)

@app.route("/teacher/<int:id>")
def teacher_profile(id):
    conn = get_db_connection()
    teacher = conn.execute('SELECT * FROM teachers WHERE id = ? AND approved = 1', (id,)).fetchone()
    
    if not teacher:
        conn.close()
        return "Teacher not found or not approved yet", 404
        
    # Check if a logged in student has already requested this teacher
    has_requested = False
    if session.get('user_role') == 'student':
        student_id = session.get('user_id')
        req = conn.execute('SELECT 1 FROM tuition_requests WHERE teacher_id = ? AND student_id = ?', (id, student_id)).fetchone()
        if req:
            has_requested = True
            
    conn.close()
    return render_template("teacher_profile.html", teacher=teacher, has_requested=has_requested)

@app.route("/request_tuition/<int:teacher_id>", methods=['POST'])
def request_tuition(teacher_id):
    if session.get('user_role') != 'student':
        return redirect(url_for('login'))
        
    student_id = session.get('user_id')
    student_name = session.get('user_name')
    
    conn = get_db_connection()
    
    # Get student phone
    student = conn.execute('SELECT phone FROM students WHERE id = ?', (student_id,)).fetchone()
    student_phone = student['phone'] if student else "N/A"
    
    # Check if request already exists
    existing = conn.execute('SELECT 1 FROM tuition_requests WHERE teacher_id = ? AND student_id = ?', (teacher_id, student_id)).fetchone()
    
    if not existing:
        conn.execute('''
            INSERT INTO tuition_requests (teacher_id, student_id, student_name, student_phone, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (teacher_id, student_id, student_name, student_phone, 'pending'))
        conn.commit()
        
    conn.close()
    return redirect(url_for('teacher_profile', id=teacher_id))

@app.route("/questions")
def questions():
    conn = get_db_connection()
    papers = conn.execute('SELECT * FROM pyqs').fetchall()
    conn.close()
    return render_template("question_papers.html", papers=papers)

@app.route("/videos")
def videos():
    conn = get_db_connection()
    videos = conn.execute('SELECT * FROM videos').fetchall()
    conn.close()
    return render_template("videos.html", videos=videos)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Handle Student Registration
        if action == 'register_student':
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO students (name, email, phone)
                VALUES (?, ?, ?)
            ''', (name, email, phone))
            student_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Auto-login newly registered student
            session['user_id'] = student_id
            session['user_role'] = 'student'
            session['user_name'] = name
            session['user_email'] = email
            
            return redirect(url_for('index'))

        # Handle Teacher Registration
        if action == 'register_teacher':
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            experience = request.form.get('experience')
            subject = request.form.get('subject')
            class_level = request.form.get('class_level')
            
            # Create a placeholder ID for filename since we don't have the lastrowid yet
            # We'll use a temporary filename and update it if needed, or just use email/name
            
            # Handle Profile Picture
            profile_pic_file = request.files.get('profile_pic')
            profile_pic_url = ""
            if profile_pic_file and profile_pic_file.filename != '':
                safe_name = secure_filename(name.replace(" ", "_"))
                filename = secure_filename(f"teacher_{safe_name}_{profile_pic_file.filename}")
                upload_path = os.path.join(app.root_path, 'static', 'uploads', filename)
                profile_pic_file.save(upload_path)
                profile_pic_url = url_for('static', filename='uploads/' + filename)
            
            about_me = f"Hello! I'm {name}, an experienced educator specializing in {subject}. With over {experience} years in the teaching field, my primary goal is to help students grasp complex concepts with ease."
            video_url = 'https://www.youtube.com/embed/dQw4w9WgXcQ'
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO teachers (name, email, phone, experience, subject, class_level, approved, profile_pic, about_me, video_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, experience, subject, class_level, 0, profile_pic_url, about_me, video_url))
            teacher_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Auto-login newly registered teacher
            session['user_id'] = teacher_id
            session['user_role'] = 'teacher'
            session['user_name'] = name
            session['user_email'] = email
            session['user_subject'] = subject
            session['user_class'] = class_level
            session['user_experience'] = experience
            session['user_about'] = about_me
            session['user_video'] = video_url
            session['user_profile_pic'] = profile_pic_url
            session['user_approved'] = False
            
            return redirect(url_for('teacher_dashboard'))
            
        # Handle Login
        elif action == 'login':
            email = request.form.get('email')
            if email == 'admin@educonnect.com':
                session['user_role'] = 'admin'
                return redirect(url_for('admin'))
            else:
                conn = get_db_connection()
                # Check Teachers
                teacher = conn.execute('SELECT * FROM teachers WHERE email = ?', (email,)).fetchone()
                if teacher:
                    session['user_id'] = teacher['id']
                    session['user_role'] = 'teacher'
                    session['user_name'] = teacher['name']
                    session['user_email'] = teacher['email']
                    session['user_subject'] = teacher['subject']
                    session['user_class'] = teacher['class_level']
                    session['user_experience'] = teacher['experience']
                    session['user_about'] = teacher['about_me']
                    session['user_video'] = teacher['video_url']
                    session['user_profile_pic'] = teacher['profile_pic']
                    session['user_approved'] = bool(teacher['approved'])
                    conn.close()
                    return redirect(url_for('teacher_dashboard'))
                
                # Check Students
                student = conn.execute('SELECT * FROM students WHERE email = ?', (email,)).fetchone()
                if student:
                    session['user_id'] = student['id']
                    session['user_role'] = 'student'
                    session['user_name'] = student['name']
                    session['user_email'] = student['email']
                    conn.close()
                    return redirect(url_for('index'))
                
                conn.close()
                return redirect(url_for('login'))
                    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/admin", methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        teacher_id = int(request.form.get('teacher_id'))
        
        if action == 'approve':
            conn.execute('UPDATE teachers SET approved = 1 WHERE id = ?', (teacher_id,))
            conn.commit()
        elif action == 'reject':
            conn.execute('DELETE FROM teachers WHERE id = ?', (teacher_id,))
            conn.commit()
        
        conn.close()
        return redirect(url_for('admin'))

    # Separate approved and pending teachers for the dashboard
    approved_teachers = conn.execute('SELECT * FROM teachers WHERE approved = 1').fetchall()
    pending_teachers = conn.execute('SELECT * FROM teachers WHERE approved = 0').fetchall()
    students_list = conn.execute('SELECT * FROM students').fetchall()
    papers = conn.execute('SELECT * FROM pyqs').fetchall()
    videos = conn.execute('SELECT * FROM videos').fetchall()
    
    # Get total counts for metrics
    total_students = len(students_list)
    
    conn.close()
    return render_template("admin_dashboard.html", 
                           approved_teachers=approved_teachers, 
                           pending_teachers=pending_teachers,
                           students=students_list,
                           total_students=total_students,
                           papers=papers,
                           videos=videos)

@app.route("/add_pyq", methods=['POST'])
def add_pyq():
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    board = request.form.get('board')
    class_level = request.form.get('class_level')
    subject = request.form.get('subject')
    year = request.form.get('year')
    
    # Handle the file upload
    file = request.files.get('pdf_file')
    file_url = ""
    size_str = "Unknown Size"
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.root_path, 'static', 'uploads', filename)
        file.save(upload_path)
        file_url = url_for('static', filename='uploads/' + filename)
        
        # Calculate size
        size_bytes = os.path.getsize(upload_path)
        size_mb = size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB"
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO pyqs (title, board, class_level, subject, year, size, file_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, board, class_level, subject, year, size_str, file_url))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

@app.route("/delete_pyq/<int:id>", methods=['POST'])
def delete_pyq(id):
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    paper = conn.execute('SELECT file_url FROM pyqs WHERE id = ?', (id,)).fetchone()
    
    if paper:
        # Delete the file
        if paper['file_url']:
            filename = paper['file_url'].split('/')[-1]
            file_path = os.path.join(app.root_path, 'static', 'uploads', filename)
            if os.path.exists(file_path):
                try: os.remove(file_path)
                except: pass
        
        conn.execute('DELETE FROM pyqs WHERE id = ?', (id,))
        conn.commit()
        
    conn.close()
    return redirect(url_for('admin'))

@app.route("/add_video", methods=['POST'])
def add_video():
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    category = request.form.get('category')
    youtube_url = request.form.get('youtube_url')
    channel_name = request.form.get('channel_name', 'EduConnect Partner')
    duration = request.form.get('duration', '10:00')
    
    # Process YouTube URL
    embed_url = youtube_url
    if "youtube.com/watch?v=" in youtube_url:
        video_id = youtube_url.split("v=")[1].split("&")[0]
        embed_url = f"https://www.youtube.com/embed/{video_id}"
    elif "youtu.be/" in youtube_url:
        video_id = youtube_url.split("/")[-1]
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        
    thumbnail_url = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80"
    if "/embed/" in embed_url:
        try:
            v_id = embed_url.split("/embed/")[1].split("?")[0]
            thumbnail_url = f"https://img.youtube.com/vi/{v_id}/mqdefault.jpg"
        except: pass

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO videos (title, youtube_url, embed_url, thumbnail_url, category, channel_name, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, youtube_url, embed_url, thumbnail_url, category, channel_name, duration))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

@app.route("/delete_video/<int:id>", methods=['POST'])
def delete_video(id):
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM videos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

@app.route("/teacher_dashboard")
def teacher_dashboard():
    if session.get('user_role') != 'teacher':
        return redirect(url_for('login'))
        
    teacher_id = session.get('user_id')
    
    conn = get_db_connection()
    # Get requests for this teacher
    my_requests = conn.execute('SELECT * FROM tuition_requests WHERE teacher_id = ?', (teacher_id,)).fetchall()
    conn.close()
    
    return render_template("teacher_dashboard.html", tuition_requests=my_requests)

@app.route("/update_tuition_request/<int:request_id>", methods=['POST'])
def update_tuition_request(request_id):
    if session.get('user_role') != 'teacher':
        return redirect(url_for('login'))
        
    action = request.form.get('action') # 'accept' or 'decline'
    status = 'accepted' if action == 'accept' else 'declined'
    
    conn = get_db_connection()
    conn.execute('UPDATE tuition_requests SET status = ? WHERE id = ? AND teacher_id = ?', 
                 (status, request_id, session.get('user_id')))
    conn.commit()
    conn.close()
        
    return redirect(url_for('teacher_dashboard'))

@app.route("/update_teacher_profile", methods=['POST'])
def update_teacher_profile():
    if session.get('user_role') != 'teacher':
        return redirect(url_for('login'))
        
    teacher_id = session.get('user_id')
    name = request.form.get('name')
    phone = request.form.get('phone')
    experience = request.form.get('experience')
    subject = request.form.get('subject')
    class_level = request.form.get('class_level')
    about_me = request.form.get('about_me')
    video_url = request.form.get('video_url')
    
    conn = get_db_connection()
    
    # Handle Profile Picture Update
    profile_pic_file = request.files.get('profile_pic')
    if profile_pic_file and profile_pic_file.filename != '':
        safe_name = secure_filename(name.replace(" ", "_"))
        filename = secure_filename(f"teacher_{teacher_id}_{safe_name}_{profile_pic_file.filename}")
        upload_path = os.path.join(app.root_path, 'static', 'uploads', filename)
        profile_pic_file.save(upload_path)
        profile_pic_url = url_for('static', filename='uploads/' + filename)
        conn.execute('UPDATE teachers SET profile_pic = ? WHERE id = ?', (profile_pic_url, teacher_id))
        session['user_profile_pic'] = profile_pic_url

    conn.execute('''
        UPDATE teachers 
        SET name = ?, phone = ?, experience = ?, subject = ?, class_level = ?, about_me = ?, video_url = ?
        WHERE id = ?
    ''', (name, phone, experience, subject, class_level, about_me, video_url, teacher_id))
    conn.commit()
    conn.close()
    
    # Update session
    session['user_name'] = name
    session['user_subject'] = subject
    session['user_class'] = class_level
    session['user_experience'] = experience
    session['user_about'] = about_me
    session['user_video'] = video_url
        
    return redirect(url_for('teacher_dashboard'))

@app.route("/student_dashboard")
def student_dashboard():
    if session.get('user_role') != 'student':
        return redirect(url_for('login'))
        
    student_id = session.get('user_id')
    
    conn = get_db_connection()
    # Get requests with teacher info using JOIN
    query = '''
        SELECT r.*, t.name as teacher_name, t.subject as teacher_subject 
        FROM tuition_requests r
        JOIN teachers t ON r.teacher_id = t.id
        WHERE r.student_id = ?
    '''
    my_requests = conn.execute(query, (student_id,)).fetchall()
    conn.close()
                
    return render_template("student_dashboard.html", tuition_requests=my_requests)

@app.route("/chat/<int:request_id>", methods=['GET', 'POST'])
def chat(request_id):
    from datetime import datetime
    
    # Verify user is logged in
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_role or not user_id:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    
    # Get the request details
    req = conn.execute('SELECT * FROM tuition_requests WHERE id = ?', (request_id,)).fetchone()
    if not req or req['status'] != 'accepted':
        conn.close()
        return "Chat not available or request not accepted", 403
        
    # Verify authorization
    if user_role == 'student' and req['student_id'] != user_id:
        conn.close()
        return "Unauthorized", 403
    elif user_role == 'teacher' and req['teacher_id'] != user_id:
        conn.close()
        return "Unauthorized", 403
        
    if request.method == 'POST':
        message_text = request.form.get('message')
        if message_text:
            conn.execute('''
                INSERT INTO messages (request_id, sender_id, sender_role, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (request_id, user_id, user_role, message_text, datetime.now().strftime("%H:%M")))
            conn.commit()
            conn.close()
            return redirect(url_for('chat', request_id=request_id))
            
    # Get messages
    chat_messages = conn.execute('SELECT * FROM messages WHERE request_id = ? ORDER BY id', (request_id,)).fetchall()
    
    # Find counterpart details
    student = conn.execute('SELECT name FROM students WHERE id = ?', (req['student_id'],)).fetchone()
    teacher = conn.execute('SELECT name FROM teachers WHERE id = ?', (req['teacher_id'],)).fetchone()
    
    other_party = teacher['name'] if user_role == 'student' else student['name']
    conn.close()
    
    return render_template("chat.html", 
                           messages=chat_messages, 
                           request_id=request_id,
                           other_party=other_party,
                           user_role=user_role,
                           user_id=user_id)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
