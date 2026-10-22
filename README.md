# EduConnect - Tuition Discovery Platform

EduConnect is a modern web application designed to bridge the gap between students and qualified tutors. The platform allows teachers to register and showcase their expertise, while students can discover tutors based on subjects, class levels, and experience.

## Features

- **Teacher Discovery**: Filterable search for tutors by subject, board, and grade.
- **Tuition Requests**: Secure request system for students to connect with teachers.
- **Resource Library**: Access to Previous Year Question (PYQ) papers.
- **Video Library**: Curated YouTube learning content.
- **Real-Time Dashboards**: Separate personalized dashboards for Students, Teachers, and Administrators.
- **Messaging**: Integrated chat system for accepted tuition requests.

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML5, Vanilla CSS, JavaScript
- **Server**: Gunicorn (Ready for deployment)

## Setup and Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd educonnect
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```
   The application will be available at `http://localhost:5000`.

## Admin Access
- **Email**: `admin@educonnect.com`
- **Default Password**: `admin123` (Note: Logic is currently email-based for demo purposes).

## Project Structure
- `app.py`: Main backend logic and routes.
- `educonnect.db`: SQLite database for persistent storage.
- `templates/`: HTML templates (Jinja2).
- `static/`: CSS, JavaScript, and user-uploaded media.
