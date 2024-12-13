import sqlite3 

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courses.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


def get_db_connection():
    conn = sqlite3.connect('courses.db')
    conn.row_factory = sqlite3.Row  
    return conn


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=True)   


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/add_course', methods=['POST'])
def add_course():
    try:
        data = request.get_json()
        print(f"Полученные данные для добавления курса: {data}")  
        
     
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        requirements = data.get('requirements', '').strip()
        
        if not title or not description or not requirements:
            return jsonify({'error': 'Все поля (title, description, requirements) обязательны для заполнения.'}), 400
        
    
        new_course = Course(title=title, description=description, requirements=requirements)
        db.session.add(new_course)
        db.session.commit()
        
        print(f"Курс успешно добавлен с id: {new_course.id}")
        return jsonify({
            'message': 'Курс успешно добавлен!',
            'course': {
                'id': new_course.id,
                'title': new_course.title,
                'description': new_course.description,
                'requirements': new_course.requirements
            }
        }), 201  
    
    except Exception as e:
        print(f"Произошла ошибка при добавлении курса: {e}")
        return jsonify({'error': 'Произошла ошибка при добавлении курса. Проверьте отправленные данные.'}), 500


@app.route('/search_courses', methods=['POST'])
def search_courses():
    try:
        data = request.get_json()
        print(f"Полученные данные для поиска курсов: {data}")
        
        user_requirements = data.get('requirements', '').strip()
        
        if not user_requirements:
            return jsonify({'error': 'Требования не предоставлены или пусты.'}), 400

    
        requirements_list = [req.strip() for req in user_requirements.split(',') if req.strip()]
        
        if not requirements_list:
            return jsonify({'error': 'Нет действительных требований.'}), 400
        
        query = Course.query
        for requirement in requirements_list:
            query = query.filter(Course.requirements.ilike(f'%{requirement}%'))
        
        matched_courses = query.all()
        
        if not matched_courses:
            return jsonify({'message': 'Курсы, соответствующие требованиям, не найдены.'}), 404
        
        courses_data = [{
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'requirements': course.requirements
        } for course in matched_courses]
        
        return jsonify(courses_data)
    
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return jsonify({'error': 'Ошибка обработки запроса. Проверьте отправленные данные.'}), 400

# Маршрут для создания учебного плана
@app.route('/create_study_plan', methods=['POST'])
def create_study_plan():
    try:
        data = request.get_json()
        print(f"Полученные данные для создания учебного плана: {data}")
        
        user_requirements = data.get('requirements', '').strip()
        course_ids = data.get('course_ids', [])
        
        if not user_requirements and not course_ids:
            return jsonify({'error': 'Not enough data provided. Provide at least one of course_ids or requirements.'}), 400
        
        courses_query = Course.query
        
        if user_requirements:
            requirements_list = [req.strip() for req in user_requirements.split(',') if req.strip()]
            for req in requirements_list:
                courses_query = courses_query.filter(Course.requirements.ilike(f'%{req}%'))
        
        if course_ids:
            courses_query = courses_query.filter(Course.id.in_(course_ids))
        
        selected_courses = courses_query.all()
        
        if not selected_courses:
            return jsonify({'error': 'No courses found for the provided course_ids or requirements.'}), 404
        
        study_plan = {
            'total_courses': len(selected_courses),
            'courses': [{
                'title': course.title,
                'description': course.description
            } for course in selected_courses]
        }
        
        return jsonify(study_plan)
    
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return jsonify({'error': 'An error occurred while creating the study plan.'}), 500


def init_db():
    with app.app_context():
        db.create_all()
        
        if Course.query.first() is None:
            courses = [
                Course(
                    title="Введение в программирование",
                    description="Основы программирования на Python для начинающих.",
                    requirements="Начальные знания компьютеров"
                ),
                Course(
                    title="Веб-разработка с Flask",
                    description="Создание веб-приложений с использованием Flask и SQLAlchemy.",
                    requirements="Знания Python и основ HTML/CSS"
                ),
                Course(
                    title="Анализ данных и машинное обучение",
                    description="Основы анализа данных и алгоритмы машинного обучения на Python.",
                    requirements="Базовые знания Python и математики"
                ),
                Course(
                    title="Базы данных и SQL",
                    description="Изучение реляционных баз данных и языка SQL.",
                    requirements="Нет предварительных требований"
                ),
                Course(
                    title="Frontend-разработка с HTML, CSS и JavaScript",
                    description="Создание интерактивных пользовательских интерфейсов для веб-приложений.",
                    requirements="Нет предварительных требований"
                )
            ]
            db.session.add_all(courses)
            db.session.commit()
            print("✅ Данные о курсах успешно добавлены в базу данных.")

with app.app_context():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                requirements TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")


if __name__ == '__main__':
    init_db()  
    app.run(debug=True)