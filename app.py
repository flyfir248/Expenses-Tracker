from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from sqlalchemy import func
from datetime import datetime
import pandas as pd
from flask import send_file
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

@app.route('/export/csv')
def export_csv():
    # Query all expenses
    expenses = Expense.query.all()

    # Calculate metrics
    total_expenses = sum(expense.amount for expense in expenses)
    average_expense = total_expenses / len(expenses) if expenses else 0
    highest_expense = max(expense.amount for expense in expenses) if expenses else 0

    # Prepare data for CSV
    data = [{
        "Amount": expense.amount,
        "Category": expense.category,
        "Description": expense.description,
        "Date": expense.date.strftime('%Y-%m-%d %H:%M')
    } for expense in expenses]

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Add metrics to the DataFrame
    metrics_df = pd.DataFrame({
        "Metric": ["Total Expenses", "Average Expense", "Highest Expense"],
        "Value": [total_expenses, average_expense, highest_expense]
    })

    # Save metrics to the top of the CSV file
    csv_path = os.path.join('static', 'expenses.csv')
    with open(csv_path, 'w') as f:
        metrics_df.to_csv(f, index=False)
        f.write('\n')  # Add a blank line between metrics and data
        df.to_csv(f, index=False)

    # Send the file to the user
    return send_file(csv_path, as_attachment=True)

@app.route('/export/pdf')
def export_pdf():
    # Query all expenses
    expenses = Expense.query.all()

    # Calculate metrics
    total_expenses = sum(expense.amount for expense in expenses)
    average_expense = total_expenses / len(expenses) if expenses else 0
    highest_expense = max(expense.amount for expense in expenses) if expenses else 0

    # Set up PDF
    pdf_path = os.path.join('static', 'expenses.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Expense Report")

    # Metrics
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 140, f"Total Expenses: ${total_expenses:.2f}")
    c.drawString(50, height - 160, f"Average Expense: ${average_expense:.2f}")
    c.drawString(50, height - 180, f"Highest Expense: ${highest_expense:.2f}")

    # Table headers
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 220, "Amount")
    c.drawString(150, height - 220, "Category")
    c.drawString(300, height - 220, "Description")
    c.drawString(450, height - 220, "Date")

    # Table rows
    y = height - 240
    c.setFont("Helvetica", 12)
    for expense in expenses:
        c.drawString(50, y, f"${expense.amount:.2f}")
        c.drawString(150, y, expense.category)
        c.drawString(300, y, expense.description or "N/A")
        c.drawString(450, y, expense.date.strftime('%Y-%m-%d %H:%M'))
        y -= 20

    c.save()

    # Send the file to the user
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)