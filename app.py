
import streamlit as st
import pandas as pd
import os
import json
import smtplib
import hashlib
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path

# Configuration
EMAIL_ADDRESS = "emailtracker7171@gmail.com"
EMAIL_PASSWORD = "jcrj wdho mqdv aufd"

# Create data directory if it doesn't exist
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# File paths
users_file = data_dir / "users.csv"
expenses_file = data_dir / "expenses.csv"
budgets_file = data_dir / "budgets.csv"

if not users_file.exists():
    pd.DataFrame(columns=["username", "email", "password", "alert_threshold", "email_alerts"]).to_csv(users_file, index=False)

if not expenses_file.exists():
    pd.DataFrame(columns=["username", "amount", "category", "description", "date", "shared_with"]).to_csv(expenses_file, index=False)

if not budgets_file.exists():
    pd.DataFrame(columns=["username", "category", "amount", "month"]).to_csv(budgets_file, index=False)

# Helper functions
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def load_users():
    return pd.read_csv(users_file)

def load_expenses():
    df = pd.read_csv(expenses_file)
    # Convert date strings to datetime objects
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def load_budgets():
    return pd.read_csv(budgets_file)

def save_users(df):
    df.to_csv(users_file, index=False)

def save_expenses(df):
    df.to_csv(expenses_file, index=False)

def save_budgets(df):
    df.to_csv(budgets_file, index=False)

def user_exists(username):
    users = load_users()
    return not users.empty and username in users['username'].values

def register_user(username, email, password):
    users = load_users()
    hashed_password = hash_password(password)
    new_user = pd.DataFrame({
        "username": [username],
        "email": [email],
        "password": [hashed_password],
        "alert_threshold": [90],
        "email_alerts": [0]
    })
    users = pd.concat([users, new_user], ignore_index=True)
    save_users(users)

def add_expense(username, amount, category, description, date, shared_with=None):
    expenses = load_expenses()
    new_expense = pd.DataFrame({
        "username": [username],
        "amount": [amount],
        "category": [category],
        "description": [description],
        "date": [date],
        "shared_with": [shared_with]
    })
    expenses = pd.concat([expenses, new_expense], ignore_index=True)
    save_expenses(expenses)
    
    # Check the status of the budget
    check_budget_status(username, category, date)
    
    # Create shared expenses
    if shared_with and shared_with != "":
        shared_amount = amount / 2  
        new_shared_expense = pd.DataFrame({
            "username": [shared_with],
            "amount": [shared_amount],
            "category": [category],
            "description": [f"Shared by {username}: {description}"],
            "date": [date],
            "shared_with": [username]
        })
        expenses = pd.concat([expenses, new_shared_expense], ignore_index=True)
        save_expenses(expenses)
        
        # Send email notifications
        if user_exists(shared_with):
            users = load_users()
            user_email = users[users['username'] == shared_with]['email'].iloc[0]
            email_alerts = users[users['username'] == shared_with]['email_alerts'].iloc[0]
            
            if email_alerts:
                send_email(
                    user_email,
                    "Shared Expense Notification",
                    f"Hi {shared_with},\n\n{username} has shared an expense with you.\nCategory: {category}\nAmount: ${shared_amount:.2f}\nDescription: {description}\n\nRegards,\nExpense Tracker App"
                )

def delete_expense(username, index):
    expenses = load_expenses()
    
    user_expenses = expenses[expenses['username'] == username]
    # Get the actual index in the dataframe
    actual_index = user_expenses.index[index]
    expenses = expenses.drop(actual_index).reset_index(drop=True)
    save_expenses(expenses)

def add_budget(username, category, amount, month):
    budgets = load_budgets()
    # Check if this budget already exists
    mask = (budgets['username'] == username) & (budgets['category'] == category) & (budgets['month'] == month)
    
    if mask.any():
        
        budgets.loc[mask, 'amount'] = amount
    else:
        # Create new budget
        new_budget = pd.DataFrame({
            "username": [username],
            "category": [category],
            "amount": [amount],
            "month": [month]
        })
        budgets = pd.concat([budgets, new_budget], ignore_index=True)
    
    save_budgets(budgets)

def delete_budget(username, index):
    budgets = load_budgets()
    # Filter to get only this user's budgets
    user_budgets = budgets[budgets['username'] == username]
    actual_index = user_budgets.index[index]
    budgets = budgets.drop(actual_index).reset_index(drop=True)
    save_budgets(budgets)

def update_user_settings(username, alert_threshold, email_alerts):
    users = load_users()
    users.loc[users['username'] == username, 'alert_threshold'] = alert_threshold
    users.loc[users['username'] == username, 'email_alerts'] = 1 if email_alerts else 0
    save_users(users)

def get_monthly_expenses(username, year, month):
    expenses = load_expenses()
    # Filter expenses for this user and month
    user_expenses = expenses[expenses['username'] == username]
    if not user_expenses.empty:
        user_expenses['date'] = pd.to_datetime(user_expenses['date'])
        month_expenses = user_expenses[
            (user_expenses['date'].dt.year == year) & 
            (user_expenses['date'].dt.month == month)
        ]
        return month_expenses
    return pd.DataFrame()

def check_budget_status(username, category, date):
    expenses = load_expenses()
    budgets = load_budgets()
    users = load_users()
    
    # Extract year and month from date
    date_obj = pd.to_datetime(date)
    year = date_obj.year
    month = date_obj.month
    month_str = f"{year}-{month:02d}"
    
    # Get total spent in this category for the month
    user_expenses = expenses[expenses['username'] == username]
    if not user_expenses.empty:
        user_expenses['date'] = pd.to_datetime(user_expenses['date'])
        month_category_expenses = user_expenses[
            (user_expenses['date'].dt.year == year) & 
            (user_expenses['date'].dt.month == month) &
            (user_expenses['category'] == category)
        ]
        total_spent = month_category_expenses['amount'].sum()
        
        # Get budget for this category and month
        budget_mask = (budgets['username'] == username) & (budgets['category'] == category) & (budgets['month'] == month_str)
        if budget_mask.any():
            budget_amount = budgets.loc[budget_mask, 'amount'].iloc[0]
            
            # Get user alert preferences
            user_prefs = users[users['username'] == username]
            threshold_percentage = user_prefs['alert_threshold'].iloc[0]
            email_alerts = user_prefs['email_alerts'].iloc[0]
            
            # Check if budget is exceeded or approaching threshold
            percentage_used = (total_spent / budget_amount) * 100
            
            # Check for budget alerts
            if total_spent > budget_amount:
                st.warning(f"You have exceeded your budget for {category} in {month_str}!")
                if email_alerts:
                    user_email = user_prefs['email'].iloc[0]
                    send_alert_email(user_email, username, category, budget_amount, total_spent, 'exceeded')
            elif percentage_used >= threshold_percentage:
                st.warning(f"You have used {percentage_used:.1f}% of your budget for {category} in {month_str}!")
                if email_alerts:
                    user_email = user_prefs['email'].iloc[0]
                    send_alert_email(user_email, username, category, budget_amount, total_spent, 'approaching')

def send_alert_email(email, username, category, budget, spent, alert_type):
    subject = f"Budget Alert for {category}"
    
    if alert_type == 'exceeded':
        body = f"Hi {username},\n\nYou have exceeded your budget for {category}.\nBudget: ${budget:.2f}\nSpent: ${spent:.2f}\n\nRegards,\nExpense Tracker App"
    else:
        percentage = (spent / budget) * 100
        body = f"Hi {username},\n\nYou have used {percentage:.1f}% of your budget for {category}.\nBudget: ${budget:.2f}\nSpent: ${spent:.2f}\n\nRegards,\nExpense Tracker App"
    
    send_email(email, subject, body)

def send_email(recipient, subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

# Streamlit UI
st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# Authentication pages
def login_page():
    st.title("Expense Tracker - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            users = load_users()
            if not users.empty and username in users['username'].values:
                user_row = users[users['username'] == username]
                stored_password = user_row['password'].iloc[0]
                
                if verify_password(stored_password, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid password")
            else:
                st.error("Username not found")
    
    st.markdown("---")
    st.markdown("Don't have an account? [Register here](#register)")

def register_page():
    st.title("Expense Tracker - Register")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")
        
        if submit:
            if password != confirm_password:
                st.error("Passwords do not match")
            elif user_exists(username):
                st.error("Username already exists")
            else:
                register_user(username, email, password)
                st.success("Registration successful! You can now log in.")

# Main application pages
def dashboard_page():
    st.title(f"Welcome, {st.session_state.username}!")
    
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    month_str = f"{current_year}-{current_month:02d}"
    
    # Load user's expenses and budgets
    expenses = load_expenses()
    user_expenses = expenses[expenses['username'] == st.session_state.username]
    budgets = load_budgets()
    user_budgets = budgets[budgets['username'] == st.session_state.username]
    
    # Monthly stats
    month_expenses = get_monthly_expenses(st.session_state.username, current_year, current_month)
    total_spent = month_expenses['amount'].sum() if not month_expenses.empty else 0
    
    # Display stats in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Spent This Month", f"Rs.{total_spent:.2f}")
    
    with col2:
        category_count = len(month_expenses['category'].unique()) if not month_expenses.empty else 0
        st.metric("Categories This Month", category_count)
    
    with col3:
        budget_count = len(user_budgets[user_budgets['month'] == month_str]) if not user_budgets.empty else 0
        st.metric("Active Budgets", budget_count)
    
    # Category spending vs budget
    st.subheader("Spending vs Budget by Category")
    
    if not month_expenses.empty:
        # Group expenses by category
        category_spending = month_expenses.groupby('category')['amount'].sum().reset_index()
        
        # For each category with spending, check if there's a budget
        for _, row in category_spending.iterrows():
            category = row['category']
            spent = row['amount']
            
            # Look for a budget for this category and month
            budget_mask = (user_budgets['category'] == category) & (user_budgets['month'] == month_str)
            budget_amount = user_budgets.loc[budget_mask, 'amount'].iloc[0] if budget_mask.any() else 0
            
            # Display progress bar
            if budget_amount > 0:
                percentage = min((spent / budget_amount) * 100, 100)
                st.write(f"{category}: Rs.{spent:.2f} / Rs.{budget_amount:.2f} ({percentage:.1f}%)")
                
                color = "green"
                if percentage >= 90:
                    color = "orange"
                if percentage >= 100:
                    color = "red"
                
                st.progress(percentage/100)
            else:
                st.write(f"{category}: Rs.{spent:.2f} (No budget set)")
                st.progress(0.0)
    else:
        st.info("No expenses recorded for this month yet.")
    
    # Recent expenses
    st.subheader("Recent Expenses")
    
    if not user_expenses.empty:
        recent = user_expenses.sort_values(by='date', ascending=False).head(5)
        for _, row in recent.iterrows():
            with st.expander(f"{row['date'].strftime('%Y-%m-%d')} - {row['category']} - Rs.{row['amount']:.2f}"):
                st.write(f"Description: {row['description']}")
                if pd.notna(row['shared_with']) and row['shared_with'] != "":
                    st.write(f"Shared with: {row['shared_with']}")
    else:
        st.info("No expenses recorded yet.")

def expenses_page():
    st.title("Manage Expenses")
    
    tab1, tab2 = st.tabs(["View Expenses", "Add Expense"])
    
    with tab1:
        expenses = load_expenses()
        user_expenses = expenses[expenses['username'] == st.session_state.username]
        
        if not user_expenses.empty:
            user_expenses = user_expenses.sort_values(by='date', ascending=False).reset_index(drop=True)
            
            # Display expenses in a table
            st.dataframe(
                user_expenses[['date', 'category', 'amount', 'description', 'shared_with']],
                column_config={
                    "date": "Date",
                    "category": "Category",
                    "amount": st.column_config.NumberColumn("Amount", format="Rs.%.2f"),
                    "description": "Description",
                    "shared_with": "Shared With"
                },
                hide_index=False
            )
            
            # Delete expense
            with st.form("delete_expense_form"):
                expense_index = st.selectbox("Select expense to delete:", range(len(user_expenses)), 
                                           format_func=lambda i: f"{user_expenses['date'].iloc[i].strftime('%Y-%m-%d')} - {user_expenses['category'].iloc[i]} - ${user_expenses['amount'].iloc[i]:.2f}")
                delete_button = st.form_submit_button("Delete Expense")
                
                if delete_button:
                    delete_expense(st.session_state.username, expense_index)
                    st.success("Expense deleted successfully!")
                    st.experimental_rerun()
        else:
            st.info("No expenses recorded yet.")
    
    with tab2:
        # Load existing categories for the dropdown
        expenses = load_expenses()
        user_expenses = expenses[expenses['username'] == st.session_state.username]
        categories = user_expenses['category'].unique().tolist() if not user_expenses.empty else []
        
        # Add "Other" to allow for new categories
        if "Other" not in categories:
            categories.append("Other")
        
        # Load users for sharing expenses
        users = load_users()
        other_users = users[users['username'] != st.session_state.username]['username'].tolist()
        
        with st.form("add_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                amount = st.number_input("Amount (Rs.)", min_value=0.01, step=0.01)
                category_select = st.selectbox("Category", categories)
                
                if category_select == "Other":
                    category = st.text_input("Enter new category")
                else:
                    category = category_select
            
            with col2:
                date = st.date_input("Date")
                description = st.text_input("Description")
                
                share_expense = st.checkbox("Share this expense with someone")
                if share_expense and other_users:
                    shared_with = st.selectbox("Share with", other_users)
                else:
                    shared_with = None
            
            submit_button = st.form_submit_button("Add Expense")
            
            if submit_button:
                if category_select == "Other" and not category:
                    st.error("Please enter a category name")
                else:
                    add_expense(
                        st.session_state.username, 
                        amount, 
                        category, 
                        description, 
                        date, 
                        shared_with if share_expense else None
                    )
                    st.success("Expense added successfully!")
                    st.experimental_rerun()

def budgets_page():
    st.title("Manage Budgets")
    
    # Get current year and month for default values
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    
    tab1, tab2 = st.tabs(["View Budgets", "Add Budget"])
    
    with tab1:
        # Allow user to select month to view
        year = st.selectbox("Year", range(current_year-1, current_year+2), index=1)
        month = st.selectbox("Month", range(1, 13), index=current_month-1)
        month_str = f"{year}-{month:02d}"
        
        budgets = load_budgets()
        month_budgets = budgets[(budgets['username'] == st.session_state.username) & (budgets['month'] == month_str)]
        
        if not month_budgets.empty:
            # Display budgets in a table
            st.dataframe(
                month_budgets[['category', 'amount']],
                column_config={
                    "category": "Category",
                    "amount": st.column_config.NumberColumn("Budget Amount", format="Rs.%.2f"),
                },
                hide_index=False
            )
            
            # Show spending vs budget
            st.subheader("Spending vs Budget")
            expenses = load_expenses()
            user_expenses = expenses[expenses['username'] == st.session_state.username]
            
            if not user_expenses.empty:
                user_expenses['date'] = pd.to_datetime(user_expenses['date'])
                month_expenses = user_expenses[
                    (user_expenses['date'].dt.year == year) & 
                    (user_expenses['date'].dt.month == month)
                ]
                
                if not month_expenses.empty:
                    # Group expenses by category
                    category_spending = month_expenses.groupby('category')['amount'].sum().reset_index()
                    
                    for _, budget_row in month_budgets.iterrows():
                        category = budget_row['category']
                        budget_amount = budget_row['amount']
                        
                        # Find spending for this category
                        category_mask = category_spending['category'] == category
                        spent = category_spending.loc[category_mask, 'amount'].iloc[0] if category_mask.any() else 0
                        
                        # Display progress bar
                        percentage = min((spent / budget_amount) * 100, 100)
                        st.write(f"{category}: Rs.{spent:.2f} / Rs.{budget_amount:.2f} ({percentage:.1f}%)")
                        
                        # Change color based on percentage
                        st.progress(percentage/100)
                else:
                    st.info("No expenses recorded for this month yet.")
            
            # Delete budget
            with st.form("delete_budget_form"):
                budget_index = st.selectbox("Select budget to delete:", range(len(month_budgets)), 
                                         format_func=lambda i: f"{month_budgets['category'].iloc[i]} - Rs.{month_budgets['amount'].iloc[i]:.2f}")
                delete_button = st.form_submit_button("Delete Budget")
                
                if delete_button:
                    delete_budget(st.session_state.username, budget_index)
                    st.success("Budget deleted successfully!")
                    st.experimental_rerun()
        else:
            st.info(f"No budgets set for {month_str}.")
    
    with tab2:
        # Load existing categories for the dropdown
        expenses = load_expenses()
        user_expenses = expenses[expenses['username'] == st.session_state.username]
        categories = user_expenses['category'].unique().tolist() if not user_expenses.empty else []
        
        # Add "Other" to allow for new categories
        if "Other" not in categories:
            categories.append("Other")
        
        with st.form("add_budget_form"):
            year = st.selectbox("Year", range(current_year-1, current_year+2), index=1, key="add_year")
            month = st.selectbox("Month", range(1, 13), index=current_month-1, key="add_month")
            month_str = f"{year}-{month:02d}"
            
            category_select = st.selectbox("Category", categories)
            if category_select == "Other":
                category = st.text_input("Enter new category")
            else:
                category = category_select
                
            amount = st.number_input("Budget Amount (Rs.)", min_value=1.0, step=10.0)
            
            submit_button = st.form_submit_button("Add Budget")
            
            if submit_button:
                if category_select == "Other" and not category:
                    st.error("Please enter a category name")
                else:
                    add_budget(st.session_state.username, category, amount, month_str)
                    st.success("Budget added successfully!")
                    st.experimental_rerun()

def reports_page():
    st.title("Expense Reports")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().replace(day=1))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Load expenses
    expenses = load_expenses()
    user_expenses = expenses[expenses['username'] == st.session_state.username]
    
    if not user_expenses.empty:
        user_expenses['date'] = pd.to_datetime(user_expenses['date'])
        filtered_expenses = user_expenses[
            (user_expenses['date'] >= pd.Timestamp(start_date)) & 
            (user_expenses['date'] <= pd.Timestamp(end_date))
        ]
        
        if not filtered_expenses.empty:
            # Total spending
            total_spent = filtered_expenses['amount'].sum()
            st.metric("Total Spending", f"Rs.{total_spent:.2f}")
            
            # Spending by category
            st.subheader("Spending by Category")
            category_spending = filtered_expenses.groupby('category')['amount'].sum().sort_values(ascending=False)
            
            # Create a bar chart
            st.bar_chart(category_spending)
            
            # Spending by day
            st.subheader("Daily Spending Trend")
            daily_spending = filtered_expenses.groupby(filtered_expenses['date'].dt.date)['amount'].sum()
            st.line_chart(daily_spending)
            
            # Detailed table
            st.subheader("Expense Details")
            st.dataframe(
                filtered_expenses[['date', 'category', 'amount', 'description']].sort_values(by='date', ascending=False),
                column_config={
                    "date": "Date",
                    "category": "Category",
                    "amount": st.column_config.NumberColumn("Amount", format="Rs.%.2f"),
                    "description": "Description"
                }
            )
        else:
            st.info("No expenses found in the selected date range.")
    else:
        st.info("No expenses recorded yet.")

def settings_page():
    st.title("Settings")
    
    users = load_users()
    user_row = users[users['username'] == st.session_state.username]
    
    current_threshold = user_row['alert_threshold'].iloc[0]
    current_email_alerts = bool(user_row['email_alerts'].iloc[0])
    
    with st.form("settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            threshold = st.slider("Budget Alert Threshold (%)", 
                                min_value=10, max_value=100, 
                                value=int(current_threshold),
                                help="Alert when spending reaches this percentage of budget")
        
        with col2:
            email_alerts = st.checkbox("Enable Email Alerts", 
                                    value=current_email_alerts,
                                    help="Send email notifications for budget alerts")
        
        submit = st.form_submit_button("Save Settings")
        
        if submit:
            update_user_settings(st.session_state.username, threshold, email_alerts)
            st.success("Settings updated successfully!")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.experimental_rerun()

# Main app logic
def main():
    # Sidebar navigation
    if st.session_state.logged_in:
        with st.sidebar:
            st.title("Expense Tracker")
            st.write(f"Logged in as: {st.session_state.username}")
            
            page = st.radio("Navigation", [
                "Dashboard",
                "Expenses",
                "Budgets", 
                "Reports",
                "Settings"
            ])
            
            if st.button("Logout"):
                logout()
        
        # Display the selected page
        if page == "Dashboard":
            dashboard_page()
        elif page == "Expenses":
            expenses_page()
        elif page == "Budgets":
            budgets_page()
        elif page == "Reports":
            reports_page()
        elif page == "Settings":
            settings_page()
            
    else:
        # Show tabs for login/register
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            login_page()
        
        with tab2:
            register_page()

if __name__ == "__main__":
    main()