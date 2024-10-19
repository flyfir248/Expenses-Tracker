from flask import Flask, render_template, request, redirect, url_for, send_file
from supabase import create_client
from datetime import datetime
import pandas as pd
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

app = Flask(__name__)

# Initialize Supabase client
# Initialize Supabase client using environment variables
url = os.getenv('SUPABASE_URL')  # Fetch URL from environment variable
key = os.getenv('SUPABASE_KEY')    # Fetch Key from environment variable

load_dotenv()  # Load environment variables from .env file
supabase = create_client(url, key)

@app.route('/add_goal', methods=['POST'])
def add_goal():
    name = request.form['name']
    target_amount = float(request.form['target_amount'])
    due_date = request.form['due_date']
    description = request.form['description']

    data = supabase.table('savings_goal').insert({
        "name": name,
        "target_amount": target_amount,
        "due_date": due_date,
        "description": description,
        "saved_amount": 0.0
    }).execute()

    return redirect(url_for('view_goals'))

@app.route('/goals')
def view_goals():
    response = supabase.table('savings_goal').select("*").execute()
    goals = response.data
    return render_template('goals.html', goals=goals)

@app.route('/add', methods=['POST'])
def add_expense():
    amount = float(request.form['amount'])
    category = request.form['category']
    description = request.form['description']
    date = datetime.utcnow().isoformat()

    data = supabase.table('expense').insert({
        "amount": amount,
        "category": category,
        "description": description,
        "date": date
    }).execute()

    return redirect(url_for('index'))

@app.route('/')
def index():

    response = supabase.table('expense').select("*").order('date', desc=True).execute()
    expenses = response.data

    # Convert string date to datetime object for all expenses
    for expense in expenses:
        expense['date'] = datetime.fromisoformat(expense['date'])

    # Calculate total expenses
    total_expenses = sum(expense['amount'] for expense in expenses)

    # Calculate average expense
    average_expense = total_expenses / len(expenses) if expenses else 0.0

    # Find the highest expense
    highest_expense = max(expense['amount'] for expense in expenses) if expenses else 0.0

    # Calculate total expenses by category
    category_totals = {}
    for expense in expenses:
        category = expense['category']
        amount = expense['amount']
        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount

    categories = list(category_totals.keys())
    totals = list(category_totals.values())

    return render_template('index.html',
                           expenses=expenses,
                           total_expenses=total_expenses,
                           average_expense=average_expense,
                           highest_expense=highest_expense,
                           chart_categories=categories,
                           chart_data=totals)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    data = supabase.table('expense').delete().eq('id', id).execute()
    return redirect(url_for('index'))

@app.route('/export/csv')
def export_csv():
    response = supabase.table('expense').select("*").execute()
    expenses = response.data

    # Calculate metrics
    total_expenses = sum(expense['amount'] for expense in expenses)
    average_expense = total_expenses / len(expenses) if expenses else 0
    highest_expense = max(expense['amount'] for expense in expenses) if expenses else 0

    # Prepare data for CSV
    data = [{
        "Amount": expense['amount'],
        "Category": expense['category'],
        "Description": expense['description'],
        "Date": expense['date']
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
    response = supabase.table('expense').select("*").execute()
    expenses = response.data

    # Calculate metrics
    total_expenses = sum(expense['amount'] for expense in expenses)
    average_expense = total_expenses / len(expenses) if expenses else 0
    highest_expense = max(expense['amount'] for expense in expenses) if expenses else 0

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
        c.drawString(50, y, f"${expense['amount']:.2f}")
        c.drawString(150, y, expense['category'])
        c.drawString(300, y, expense['description'] or "N/A")
        c.drawString(450, y, expense['date'])
        y -= 20

    c.save()

    # Send the file to the user
    return send_file(pdf_path, as_attachment=True)

@app.route('/spending_insights')
def spending_insights():
    response = supabase.table('expense').select("*").execute()
    expenses = response.data

    # Convert string date to datetime object for all expenses
    for expense in expenses:
        expense['date'] = datetime.fromisoformat(expense['date'])

    # Group expenses by category
    spending_by_category = {}
    for expense in expenses:
        category = expense['category']
        amount = expense['amount']
        if category in spending_by_category:
            spending_by_category[category] += amount
        else:
            spending_by_category[category] = amount

    # Group expenses by month
    spending_by_month = {}
    for expense in expenses:
        month = expense['date'].strftime('%Y-%m')  # Use datetime formatting
        amount = expense['amount']
        if month in spending_by_month:
            spending_by_month[month] += amount
        else:
            spending_by_month[month] = amount

    # Group expenses by week
    spending_by_week = {}
    for expense in expenses:
        week = expense['date'].strftime('%Y-%W')  # Use datetime formatting
        amount = expense['amount']
        if week in spending_by_week:
            spending_by_week[week] += amount
        else:
            spending_by_week[week] = amount

    return render_template('spending_insights.html',
                           spending_by_category=spending_by_category.items(),
                           spending_by_month=spending_by_month.items(),
                           spending_by_week=spending_by_week.items())

if __name__ == '__main__':
    app.run(debug=True)
