from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from sqlalchemy import func
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/add', methods=['POST'])
def add_expense():
    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']
    new_expense = Expense(amount=amount, category=category, description=description)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/')
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()

    # Calculate total expenses
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0.0

    # Calculate average expense
    average_expense = db.session.query(func.avg(Expense.amount)).scalar() or 0.0

    # Find the highest expense
    highest_expense = db.session.query(func.max(Expense.amount)).scalar() or 0.0

    # Calculate total expenses by category
    category_totals = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).group_by(Expense.category).all()

    categories = [cat for cat, _ in category_totals]
    totals = [float(total) for _, total in category_totals]

    return render_template('index.html',
                           expenses=expenses,
                           total_expenses=total_expenses,
                           average_expense=average_expense,
                           highest_expense=highest_expense,
                           chart_categories=categories,
                           chart_data=totals)


@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    expense_to_delete = Expense.query.get_or_404(id)
    db.session.delete(expense_to_delete)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)