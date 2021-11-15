import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from sqlalchemy.sql.expression import null

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # CORS HEADERS
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization, true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS"
        )
        return response

    @app.route("/categories")
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        formatted_categories = {category.id: category.type for category in categories}

        if len(formatted_categories) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "categories": formatted_categories
        })

    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        total_questions = len(selection)

        categories = Category.query.all()
        formatted_categories = {
            category.id: category.type for category in categories}

        return jsonify(
            {
                "success": True,
                'questions': current_questions,
                'total_questions': total_questions,
                'categories': formatted_categories,
                'current_category': None
            }
        )

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "deleted": question_id,
                "questions": current_questions,
                "total_questions": len(Question.query.all())
            })
        except:
            abort(422)

    @app.route("/questions/add", methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_difficulty = body.get("difficulty", None)
        new_category = body.get("category", None)

        try:
            question = Question(question=new_question,
                                answer=new_answer,
                                category=new_category,
                                difficulty=new_difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "created": question.id,
                "questions": current_questions,
                "total_questions": len(Question.query.all())
            })

        except:
            abort(422)

    @app.route("/questions/search", methods=["POST"])
    def search_questions():
        body = request.get_json()
        searchTerm = body.get("searchTerm", None)

        try:
            if searchTerm:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(searchTerm)))

                current_questions = paginate_questions(request, selection)

                return jsonify({
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(selection.all()),
                    "current_category": None
                })

        except:
            abort(422)

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_questions_by_category(category_id):
        try:
            selection = Question.query.order_by(Question.id).filter(
                Question.category == category_id)

            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection.all()),
                "current_category": None
            })

        except:
            abort(400)

    @app.route("/quizzes", methods=["POST"])
    def get_quizzes():
        body = request.get_json()

        try:
            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(404)

            previousQuestions = body.get("previous_questions", None)
            quizCategory = body.get("quiz_category", None)

            if quizCategory['type'] == 'click':
                questions = Question.query.order_by(Question.id).filter(
                    Question.id.notin_(previousQuestions)).all()
            else:
                questions = Question.query.order_by(Question.id).filter(
                    Question.category == quizCategory["id"]).filter(
                    Question.id.notin_(previousQuestions)).all()

            formatted_questions = [question.format() for question in questions]

            questions_choices = []

            for item in formatted_questions:
                if item['id'] not in previousQuestions:
                    questions_choices.append(item)

            current_question = ""

            if len(questions_choices) > 0:
                current_question = random.choice(questions_choices)

            return jsonify({
                "success": True,
                "question": current_question
            })

        except:
            abort(400)

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404,
                    "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422,
                    "message": "unprocessable"}),
            422,
        )

    return app
