import mysql.connector
import random  # Import for generating random IDs

class Bank:
    Bank_Name = "Indian Demo Bank"
    Branch = "Nadia, WB, 741156. IFSC- IDBN0001356"


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Hasan@786",
    database="Banking_Details"
)

mycursor = mydb.cursor()


def create_unique_id(prefix, length):
    """Generates a unique ID with a specific prefix and length."""
    while True:
        unique_id = prefix + str(random.randint(10 ** (length - len(prefix) - 1), 10 ** (length - len(prefix)) - 1))
        sql = f"SELECT * FROM create_accounts WHERE account_number = %s"
        mycursor.execute(sql, (unique_id,))
        if not mycursor.fetchone():
            return unique_id


def create_customer_id():
    """Generates a unique 8-digit customer ID with the prefix 1356."""
    return create_unique_id("1356", 8)  # Ensure 8 digits


def create_account_number():
    """Generates a unique 10-digit account number with the prefix 1356."""
    return create_unique_id("1356", 10)  # Ensure 10 digits


def customers(customer_name, date_of_birth, mobile_number, address, email):
    customer_id = create_customer_id()
    sql = "INSERT INTO customers (customer_id, customer_name, date_of_birth, mobile_number, address, email) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (customer_id, customer_name, date_of_birth, mobile_number, address, email)
    mycursor.execute(sql, val)
    mydb.commit()
    print("Customer Created Successfully!")
    print("Customer ID:", customer_id)  # Display the generated customer ID

    # Call create_account function after creating the customer
    create_account(mycursor.lastrowid, initial_deposit=1000,
                   account_type=input("Enter account type (e.g., Savings, Current, Fixed Deposit): "))


def create_account(customer_id, initial_deposit, account_type):
    account_number = create_account_number()
    sql = "INSERT INTO create_accounts (account_number, customer_id, balance, account_type) VALUES (%s, %s, %s, %s)"
    val = (account_number, customer_id, initial_deposit, account_type)
    mycursor.execute(sql, val)
    mydb.commit()
    print("Account Created Successfully!")
    print("Account Number:", account_number)  # Display the generated account number

    account_number = mycursor.lastrowid  # Retrieve the newly generated account number
    insert_transaction(account_number, initial_deposit, "Opening Balance")


def change_correction_customer_details(customer_id):
    mycursor.execute("SELECT * FROM customers WHERE customer_id=%s", (customer_id,))
    existing_customer_data = mycursor.fetchone()

    if existing_customer_data:
        print("Existing Customer Details:")
        print("Customer Name is: ", existing_customer_data[1])  # Assuming customer_name is the 2nd column
        print("Date of Birth is: ", existing_customer_data[2])
        print("Address is :", existing_customer_data[3])
        print("Mobile Number is: ", existing_customer_data[4])
        print("Email is: ", existing_customer_data[5])

        while True:
            make_corrections = input("Do you want to make Corrections? (yes/no): ").lower()
            if make_corrections in ["yes", "no"]:
                break
            else:
                print("Invalid response. Please enter 'yes' or 'no'.")

        if make_corrections == "yes":
            new_customer_name = input("Enter corrected Name (or leave blank to keep existing): ")
            new_date_of_birth = input("Enter corrected Date of Birth (or leave blank to keep existing): ")
            new_address = input("Enter corrected Address (or leave blank to keep existing): ")
            new_mobile_number = input("Enter corrected Mobile Number (or leave blank to keep existing): ")
            new_email = input("Enter corrected Email (or leave blank to keep existing): ")

            updated_fields = {
                "customer_name": new_customer_name,
                "date_of_birth": new_date_of_birth,
                "address": new_address,
                "mobile_number": new_mobile_number,
                "email": new_email
            }

            updated_fields = {key: value for key, value in updated_fields.items() if value}

            if updated_fields:
                try:
                    sql = "UPDATE customers SET " + ", ".join(
                        [f"{key}=%s" for key in updated_fields]) + " WHERE customer_id=%s"
                    values = tuple(updated_fields.values()) + (customer_id,)
                    mycursor.execute(sql, values)
                    mydb.commit()
                    print("Customer Details Updated Successfully.")
                    print(f"Updated fields: {', '.join(updated_fields)}")
                except mysql.connector.Error as err:
                    print(f"Error updating customer details: {err}")
            else:
                print("No changes made to customer details.")
        else:
            print("Returning to Menu.")
    else:
        print("Customer ID not found in the database.")


def view_account_details(account_number):
    try:
        if mycursor is not None:
            # Modified query to match column names and table aliases
            mycursor.execute("""
                SELECT c.customer_id, c.customer_name, ca.account_number, ca.account_type, ca.balance, ca.status
                FROM customers c
                INNER JOIN create_accounts ca ON c.customer_id = ca.customer_id
                WHERE ca.account_number = %s
            """, (account_number,))
            account_details = mycursor.fetchone()

            # Handle account status and display details
            if account_details:
                status = account_details[5]
                if status == "Closed/Inactive":
                    print("Account is Closed/Inactive and cannot view Account Details.")
                else:
                    print("Account Details:")
                    print(
                        "   Customer ID  |    Customer Name     |   Account Number  |  Account Type  |Account Balance |Account Status ")
                    print(
                        "----------------|----------------------|-------------------|----------------|----------------|---------------")
                    print(
                        f"    {account_details[0]}    | {account_details[1]}      |    {account_details[2]}     |    {account_details[3]}     |    {account_details[4]}     |    {account_details[5]}")
                    print(
                        "----------------|----------------------|-------------------|----------------|----------------|---------------")
            else:
                print("Account Number not found.")
        else:
            print("Cursor is None. Please check your database connection.")
    except Exception as e:
        print(f"Error: {e}")


def deposit(account_number, amount, transaction_type="Deposit by Cash"):
    mycursor.execute("SELECT status FROM create_accounts WHERE account_number = %s", (account_number,))
    status = mycursor.fetchone()[0]
    if status == "Closed/Inactive":
        print("Account is Closed/Inactive and cannot receive Deposits.")
        return
    else:
        sql = "UPDATE create_accounts SET balance = balance + %s WHERE account_number = %s"
        val = (amount, account_number)
        mycursor.execute(sql, val)
        mydb.commit()
        insert_transaction(account_number, amount, transaction_type)
        print(f"Your Account_Number: {account_number} Rs. {amount} Deposit Successfully!")


def withdraw(account_number, amount, transaction_type="Withdrawal by Cash"):
    mycursor.execute("SELECT status FROM create_accounts WHERE account_number = %s", (account_number,))
    status = mycursor.fetchone()[0]
    if status == "Closed/Inactive":
        print("Account is Closed/Inactive and cannot Withdrawal.")
        return
    mycursor.execute("SELECT balance FROM create_accounts WHERE account_number = %s", (account_number,))
    balance = mycursor.fetchone()[0]
    if balance >= amount:
        sql = "UPDATE create_accounts SET balance = balance - %s WHERE account_number = %s"
        val = (amount, account_number)
        mycursor.execute(sql, val)
        mydb.commit()
        insert_transaction(account_number, amount, transaction_type)
        print(f"Your Account_Number: {account_number} Rs. {amount} Withdrawal Successfully!")
    else:
        print("Insufficient funds!")


def funds_transfer(from_account, to_account, amount, transaction_type="Funds Transfer"):
    mycursor.execute("SELECT balance FROM create_accounts WHERE account_number = %s", (from_account,))
    from_balance = mycursor.fetchone()[0]

    if from_balance >= amount:
        # Debit from 'from_account'
        debit_sql = "UPDATE create_accounts SET balance = balance - %s WHERE account_number = %s"
        debit_val = (amount, from_account)
        mycursor.execute(debit_sql, debit_val)

        # Credit to 'to_account'
        credit_sql = "UPDATE create_accounts SET balance = balance + %s WHERE account_number = %s"
        credit_val = (amount, to_account)
        mycursor.execute(credit_sql, credit_val)

        mydb.commit()

        account_exists_query = "SELECT account_number FROM create_accounts WHERE account_number = %s"
        mycursor.execute(account_exists_query, (from_account,))
        if not mycursor.fetchone():
            print(f"Invalid 'from_account' number: {from_account}")
            return
        mycursor.execute(account_exists_query, (to_account,))
        if not mycursor.fetchone():
            print(f"Invalid 'to_account' number: {to_account}")
            return

        # Insert transactions for both accounts
        try:
            insert_transaction(from_account, amount, transaction_type)
            insert_transaction(to_account, amount, f"Credit from A/c.{from_account}")
        except Exception as e:
            print(f"Error while inserting transactions: {e}")
            # Consider rolling back the transaction here using mydb.rollback()
            return
        print(f"Account_Number: {to_account} Rs. {amount} Funds_Transfer Successfully!")
    else:
        print("Insufficient funds!")


def check_balance(account_number):
    mycursor.execute("SELECT balance FROM create_accounts WHERE account_number = %s", (account_number,))
    balance = mycursor.fetchone()[0]
    mycursor.execute("SELECT status FROM create_accounts WHERE account_number = %s", (account_number,))
    status = mycursor.fetchone()[0]
    if status == "Closed/Inactive":
        print("Account is Closed/Inactive and cannot check Balance.")
        return
    else:
        print(f"Your balance is: Rs. ", balance)


def view_transactions(account_number):
    try:
        with mydb.cursor() as mycursor:
            mycursor.execute("SELECT * FROM transactions WHERE account_number = %s", (account_number,))
            transactions = mycursor.fetchall()

            mycursor.execute("SELECT status FROM create_accounts WHERE account_number = %s", (account_number,))
            status = mycursor.fetchone()[0]
            if status == "Closed/Inactive":
                print("Account is Closed/Inactive and cannot view Transactions.")
                return

            if transactions:
                print("Transaction History:")
                print(
                    "Transaction Date    | Account Number  |   Transaction ID   |        Transaction  Type           |           Amount         |    Total Balance    ")
                print(
                    "--------------------|-----------------|--------------------|------------------------------------|--------------------------|---------------------")
                for transaction in transactions:
                    print(
                        f"{transaction[0]} |   {transaction[1]:10}    |     {transaction[2]:8}       | {transaction[3]}                  |       {transaction[4]:8}           |      {transaction[5]}    ")
                    print(
                        "--------------------|-----------------|--------------------|------------------------------------|--------------------------|---------------------")
            else:
                print("No transactions found for this account.")

    except mysql.connector.Error as err:
        print("Error fetching transactions:", err)


def insert_transaction(account_number, amount, transaction_type):
    sql = "INSERT INTO transactions (account_number, amount, transaction_type) VALUES (%s, %s, %s)"
    val = (account_number, amount, transaction_type)
    mycursor.execute(sql, val)
    mydb.commit()

    # Retrieve and store the total balance after the transaction
    sql = "SELECT balance AS total_balance FROM create_accounts WHERE account_number = %s"
    val = (account_number,)
    mycursor.execute(sql, val)
    total_balance = mycursor.fetchone()[0]

    # Update the total_balance in the transactions table
    sql = "UPDATE transactions SET total_balance = %s WHERE transaction_id = LAST_INSERT_ID()"
    val = (total_balance,)
    mycursor.execute(sql, val)
    mydb.commit()


def close_account(account_number):
    try:
        with mydb.cursor() as mycursor:
            # Check if the account exists and has a zero balance
            sql = "SELECT * FROM create_accounts WHERE account_number = %s AND balance = 0.00"
            val = (account_number,)
            mycursor.execute(sql, val)
            account = mycursor.fetchone()

            if account:
                # Update the account status to 'closed'
                sql = "UPDATE create_accounts SET status = 'Closed/Inactive' WHERE account_number = %s"
                mycursor.execute(sql, val)
                mydb.commit()
                print("Account Closed/Inactive Successfully.")
            else:
                print("Account not found or has a non-zero balance.")

    except mysql.connector.Error as err:
        print("Error closing account:", err)


def activate_account(account_number):
    try:
        with mydb.cursor() as mycursor:
            sql = "UPDATE create_accounts SET status = 'Active' WHERE account_number = %s"
            val = (account_number,)
            mycursor.execute(sql, val)
            mydb.commit()
            print("Account Activated Successfully.")
    except mysql.connector.Error as err:
        print("Error activating account:", err)

    mydb.close()


print(f"\nWelcome To {Bank.Bank_Name}")


def employee_menu():
    # Full access options for employees
    while True:
        print("\nEmployee Menu:")
        print("1. Account Open")
        print("2. View and Change/Correction Customer Details: ")
        print("3. View_Account_Details")
        print("4. Deposit")
        print("5. Withdraw")
        print("6. Transfer_Funds")
        print("7. Check Balance")
        print("8. View Transactions")
        print("9. Account Closed")
        print("10. Activate_Account")
        print("11. Logout")

        choice = int(input("Enter your choice: "))

        if choice == 1:
            customer_name = input("Enter your name: ")
            date_of_birth = input("Enter Your Date of Birth: ")
            mobile_number = input("Enter your Mobile Number: ")
            address = input("Enter your Address: ")
            email = input("Enter your Email ID: ")
            customers(customer_name, date_of_birth, mobile_number, address, email)

        elif choice == 2:
            customer_id = input("Enter Your Customer ID: ")
            change_correction_customer_details(customer_id)

        elif choice == 3:
            account_number = input("Enter your account number: ")
            view_account_details(account_number)

        elif choice == 4:
            account_number = input("Enter your account number: ")
            amount = float(input("Enter amount to deposit: "))
            deposit(account_number, amount)

        elif choice == 5:
            account_number = input("Enter your account number: ")
            amount = float(input("Enter amount to withdraw: "))
            withdraw(account_number, amount)

        elif choice == 6:
            from_account = input("Enter Debit Account Number: ")
            to_account = input("Enter Credit Account Number:  ")
            amount = float(input("Enter Amount: "))
            funds_transfer(from_account, to_account, amount)

        elif choice == 7:
            account_number = input("Enter your account number: ")
            check_balance(account_number)

        elif choice == 8:
            account_number = input("Enter your account number: ")
            view_transactions(account_number)

        elif choice == 9:
            account_number = input("Enter your account number: ")
            close_account(account_number)

        elif choice == 10:
            account_number = input("Enter your account number: ")
            activate_account(account_number)

        elif choice == 11:
            print("User logged out Successfully!")
            print(f"\nThank You for Visiting Us.\n{Bank.Bank_Name}")
            main_menu()

        else:
            break
    main_menu()


def get_logged_in_customer_id(customer_id):
    mycursor.execute("SELECT * FROM create_accounts WHERE customer_id=%s", (customer_id,))
    result = mycursor.fetchone()
    if result:
        return result[0]  # Assuming "customer_id" is the column name
    else:
        return None


def get_customer_account_number(customer_id):
    cursor = mydb.cursor()
    cursor.execute("SELECT account_number FROM create_accounts WHERE Customer_ID = %s", (customer_id,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Account number found
    else:
        print("Customer does not have an account or account number not found.")
        return None


def customer_menu(customer_id):
    if customer_id:
        while True:
            print("\nCustomer Menu:")
            print("1. View Account Details")
            print("2. Transfer Funds")
            print("3. Check Balance")
            print("4. View Transactions")
            print("5. Logout")

            choice = int(input("Enter your choice: "))

            if choice == 1:
                account_number = get_customer_account_number(customer_id)  # Retrieve customer's account number
                view_account_details(account_number)

            elif choice == 2:
                from_account = get_customer_account_number(customer_id)  # Retrieve customer's account number
                to_account = input("Enter Credit Account Number: ")
                amount = float(input("Enter Amount: "))
                funds_transfer(from_account, to_account, amount)

            elif choice == 3:
                account_number = get_customer_account_number(customer_id)  # Retrieve customer's account number
                check_balance(account_number)

            elif choice == 4:
                account_number = get_customer_account_number(customer_id)  # Retrieve customer's account number
                view_transactions(account_number)

            elif choice == 5:
                print("User logged out Successfully!")
                print(f"\nThank You for Visiting Us.\n{Bank.Bank_Name}")
                main_menu()

            else:
                break

        main_menu()


def login():
    role = input("Enter your role (employee/customer): ")
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    sql = "SELECT * FROM user_details WHERE username = %s AND password = %s AND role = %s"
    val = (username, password, role)
    mycursor.execute(sql, val)
    result = mycursor.fetchone()

    mycursor.execute("SELECT role FROM user_details WHERE role = %s", (role,))
    role = mycursor.fetchone()[0]

    if result:
        print("User Logged in Successfully!")
        if role == "employee":
            employee_menu()
        elif role == "customer":
            customer_id = input("Enter your customer ID: ")
            customer_menu(customer_id)
        else:
            print("Invalid user type in database.")
    else:
        print("Invalid username, password, or role. Please try again.")


def register_user():
    name = input("Enter your Name: ")
    employee_or_customer_id = int(input("Enter your Employee or Customer_id: "))
    username = input("Enter a new username: ")
    password = input("Enter a new password: ")
    role = input("Enter role (employee/customer): ")

    if role not in ['employee', 'customer']:
        print("Invalid role. User must be either 'employee' or 'customer'.")
        return

    sql = "INSERT INTO user_details (name, employee_or_customer_id, username, password, role) VALUES (%s, %s, %s, %s, %s)"
    val = (name, employee_or_customer_id, username, password, role)

    try:
        mycursor.execute(sql, val)
        mydb.commit()
        print(
            f"Hello! {name} Your user details is : Username: {username} Password: {password}\nUser Registered Successfully!")
        main_menu()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        main_menu()


def forgot_username():
    employee_or_customer_id = int(input("Enter your Employee or Customer ID: "))
    role = input("Enter your role (employee/customer): ")

    sql = "SELECT username FROM user_details WHERE employee_or_customer_id = %s AND role = %s"
    val = (employee_or_customer_id, role)
    mycursor.execute(sql, val)
    result = mycursor.fetchone()

    if result:
        print(f"Your username is: {result[0]}")
        main_menu()
    else:
        print("No matching user found.")
        main_menu()


def forgot_password():
    username = input("Enter your username: ")
    role = input("Enter your role (employee/customer): ")
    new_password = input("Enter a new Password: ")

    sql = "UPDATE user_details SET password = %s WHERE username = %s AND role = %s"
    val = (new_password, username, role)
    mycursor.execute(sql, val)

    if mycursor.rowcount > 0:
        mydb.commit()
        print("Your password has been reset to:", new_password)
        main_menu()
    else:
        print("No matching user found.")
        main_menu()


print(f"\nWelcome To {Bank.Bank_Name}\n{Bank.Branch}")


def main_menu():
    while True:
        print("\nUsers Menu:")
        print("1. Existing User")
        print("2. New User")
        print("3. Forget Username")
        print("4. Forget Password")

        choice = int(input("Enter Your Choice: "))

        if choice == 1:  # Handle login option
            login()
            break
        elif choice == 2:  # Handle register user option
            register_user()
            break
        elif choice == 3:  # Handle forgot username option
            forgot_username()
            break
        elif choice == 4:  # Handle forgot password option
            forgot_password()
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main_menu()