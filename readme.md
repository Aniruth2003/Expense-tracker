# Expense Tracker Application

An interactive web-based expense tracking application built with Streamlit that allows users to track expenses, set budgets, and receive notifications when approaching budget limits.

## Features

- User authentication (register, login, logout)
- Expense tracking with category classification
- Budget management by category and month
- Expense sharing between users
- Email notifications for budget alerts and shared expenses
- Comprehensive reports and visualizations
- Personalized dashboard with spending metrics

## Technologies Used

- Python 3.9+
- Streamlit for the web interface
- Pandas for data manipulation
- SMTP for email notifications
- CSV-based data storage

## Installation

### Prerequisites

- Python 3.9 or higher
- Docker (optional, for containerized deployment)

### Local Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/expense-tracker.git
   cd expense-tracker
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   streamlit run app.py
   ```

### Docker Installation

1. Build the Docker image:
   ```
   docker build -t expense-tracker .
   ```

2. Run the container:
   ```
   docker run -p 8501:8501 expense-tracker
   ```

3. Access the application at `http://localhost:8501`

## Docker Commands

### Building the Docker Image

Run with:
```
docker-compose up
```

## Data Storage

The application uses CSV files to store data, implementing a simple ORM abstraction layer for data manipulation:

- `users.csv`: Stores user credentials and preferences
- `expenses.csv`: Stores all expense transactions
- `budgets.csv`: Stores budget settings by category and month

### Data Access Layer Implementation

The application implements a simple ORM-like abstraction through the following functions:

```python
# Load data
def load_users():
    return pd.read_csv(users_file)

def load_expenses():
    df = pd.read_csv(expenses_file)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def load_budgets():
    return pd.read_csv(budgets_file)

# Save data
def save_users(df):
    df.to_csv(users_file, index=False)

def save_expenses(df):
    df.to_csv(expenses_file, index=False)

def save_budgets(df):
    df.to_csv(budgets_file, index=False)
```

These functions provide a consistent interface for data operations, abstracting the underlying CSV storage mechanism.

## Test Steps to Validate the Application

Follow these steps to test the application's functionality:

### 1. User Registration and Authentication

1. Open the application in your browser
2. Navigate to the "Register" tab
3. Create a new account with username, email, and password
4. Switch to the "Login" tab
5. Login with your new credentials
6. Verify you're redirected to the dashboard

### 2. Managing Expenses

1. Navigate to "Expenses" from the sidebar
2. Select the "Add Expense" tab
3. Enter an expense with:
   - Amount (e.g., 500)
   - Category (e.g., "Groceries")
   - Date (current date)
   - Description (e.g., "Weekly grocery shopping")
4. Submit the expense
5. Navigate to "View Expenses" tab
6. Verify your new expense appears in the list

### 3. Setting Budgets

1. Navigate to "Budgets" from the sidebar
2. Select the "Add Budget" tab
3. Set a budget for:
   - Current month
   - Category (e.g., "Groceries")
   - Amount (e.g., 2000)
4. Submit the budget
5. Navigate to "View Budgets" tab
6. Verify your new budget appears in the list
7. Verify the spending vs. budget visualization shows the correct percentage used

### 4. Testing Budget Alerts

1. Add another expense in the same category with an amount that will exceed the budget threshold
2. Navigate to the Dashboard
3. Verify that a budget alert warning appears
4. If email alerts are enabled, check your email for notifications

### 5. Testing Expense Sharing

1. Register a second user in another browser session
2. Login with your first user account
3. Add an expense and check "Share this expense with someone"
4. Select the second user from the dropdown
5. Submit the expense
6. Login with the second user account
7. Verify the shared expense appears in the second user's expense list
8. Check the second user's email for a notification (if email alerts are enabled)

### 6. Testing Reports

1. Add several expenses with different categories
2. Navigate to "Reports" from the sidebar
3. Set a date range that includes your expenses
4. Verify that the spending by category chart displays correctly
5. Verify that the daily spending trend chart displays correctly
6. Check that the expense details table shows all relevant expenses

### 7. Testing User Settings

1. Navigate to "Settings" from the sidebar
2. Change the budget alert threshold
3. Toggle email alerts
4. Save settings
5. Add an expense that triggers the new threshold
6. Verify the alert behavior matches your new settings

## Code Documentation

The application code is structured as follows:

- **Configuration and Setup**: Establishes file paths, creates necessary directories and default CSV files
- **Helper Functions**: Handles password hashing, data loading/saving, and user validation
- **Data Management Functions**: Manages expenses, budgets, and user settings
- **Email Notification System**: Sends alerts and notifications via SMTP
- **Streamlit UI Components**: Defines the user interface for each section of the application
- **Main Application Logic**: Controls navigation and page rendering

Key components are documented with docstrings and comments to explain their purpose and functionality.

## Security Notes

- Passwords are stored using SHA-256 hashing
- Email credentials are stored in the code (not recommended for production)
- For production use, implement environment variables for sensitive information
- Implement additional security measures for a production deployment
