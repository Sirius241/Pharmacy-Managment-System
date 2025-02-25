import streamlit as st
import re
import mysql.connector
import pandas as pd
import datetime
import google.generativeai as genai
from googletrans import Translator
import smtplib
from email.mime.text import MIMEText
from pyzbar.pyzbar import decode
from PIL import Image
import qrcode
import requests


# ✅ Directly define your Gemini API Key here
API_KEY = "put your API here"

# ✅ Configure Gemini API
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Initialize the translator
translator = Translator()

# Language options
LANGUAGES = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Chinese': 'zh-cn',
    'Kannada': 'kn',
    'Hindi': 'hi',
    'Tamil': 'ta',
    'Telugu': 'te',
}

# Function to translate text
def translate_text(text, target_language="en"):
    try:
        translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        st.error(f"Translation Error: {e}")
        return text  # Return the original text if translation fails

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_type = None  # 'Customer' or 'Manager'
    st.session_state.user_id = None    # Stores the user ID
    st.session_state.chat_history = []  # Initialize chat history

# Sidebar for language selection
selected_language = st.sidebar.selectbox("Select Language", list(LANGUAGES.keys()))
target_language = LANGUAGES[selected_language]

# Database Connection Function
def get_db_connection():
    return mysql.connector.connect(
        # Setup your database
        host='', user='', password='', database='PharmacyManagement'
    )

# Validate Email Format
def validate_email(email):
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return False, "Invalid email format. Please enter a valid email address."
    return True, ""

# Validate Password
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

# Validate Phone Number (10 digits)
def validate_phone(phone):
    if not re.match(r"^\d{10}$", phone):
        return False, "Invalid phone number format. It must contain exactly 10 digits."
    return True, ""

# Signup Function (New Customer Registration)
def signup_user(email, password, name, age, sex, phone, address):
    # Validate email
    is_email_valid, email_error = validate_email(email)
    if not is_email_valid:
        st.error(email_error)
        return

    # Check if email already exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT C_ID FROM Customer WHERE EmailID = %s", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        st.error("Email is already registered. Please log in instead.")
        cursor.close()
        conn.close()
        return

    # Validate password
    is_password_valid, password_error = validate_password(password)
    if not is_password_valid:
        st.error(password_error)
        cursor.close()
        conn.close()
        return

    # Validate phone number (optional, if phone is provided)
    if phone.strip():
        is_phone_valid, phone_error = validate_phone(phone)
        if not is_phone_valid:
            st.error(phone_error)
            cursor.close()
            conn.close()
            return

    # Proceed with the registration if all validations pass
    try:
        cursor.execute(
            "INSERT INTO Customer (C_name, Age, Sex, Address, Pwd, EmailID) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, age, sex, address, password, email)
        )
        conn.commit()

        # Retrieve customer ID for future references
        cursor.execute("SELECT C_ID FROM Customer WHERE EmailID = %s", (email,))
        customer_id = cursor.fetchone()[0]

        # Insert phone number if provided
        if phone.strip():
            cursor.execute(
                "INSERT INTO CustomerPhone (C_ID, Ph_no) VALUES (%s, %s)",
                (customer_id, phone)
            )
            conn.commit()

        st.success("Signup successful! You can now log in.")
    except mysql.connector.Error as e:
        st.error(f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Login Function
def login_user(username, password, user_type):
    conn = get_db_connection()
    cursor = conn.cursor()

    if user_type == "Customer":
        query = "SELECT C_ID FROM Customer WHERE EmailID = %s AND Pwd = %s"
    else:
        query = "SELECT M_ID FROM Manager WHERE M_name = %s AND M_pwd = %s"

    cursor.execute(query, (username, password))
    result = cursor.fetchone()

    if result:
        st.session_state.logged_in = True
        st.session_state.user_type = user_type
        st.session_state.user_id = result[0]
        st.success(translate_text(f"Logged in as {user_type}!", target_language))
    else:
        st.error(translate_text("Invalid credentials. Please try again.", target_language))

    cursor.close()
    conn.close()

def get_drug_interactions(drug_name):
    url = f"https://api.fda.gov/drug/label.json?search={drug_name}&limit=1"
    
    try:
        response = requests.get(url)
        data = response.json()

        if 'results' in data and 'warnings' in data['results'][0]:
            warnings_list = data['results'][0]['warnings']

            # ✅ Clean and format warnings into multiple bullet points
            formatted_warnings = "\n\n".join([
                f"• {sentence.strip()}" for warning in warnings_list for sentence in warning.split(". ") if sentence
            ])

            return f"⚠ *Warning for {drug_name}:*\n\n{formatted_warnings}"
        
        else:
            return f"✅ *No known harmful interactions for {drug_name}.*"
    
    except Exception as e:
        return f"❌ *Error fetching data: {e}*"


def place_order():
    if not st.session_state.logged_in or st.session_state.user_type != "Customer":
        st.error(translate_text("You must be logged in as a customer!", target_language))
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT Drugs.D_ID, Drugs.D_name, Inventory.Rem_qty FROM Drugs JOIN Inventory ON Drugs.D_ID = Inventory.D_ID")
    drugs = cursor.fetchall()

    drug_dict = {d[1]: (d[0], d[2]) for d in drugs}  # d[0] is D_ID, d[2] is Rem_qty
    drug_name = st.selectbox(translate_text("Select Drug", target_language), list(drug_dict.keys()))
    quantity = st.number_input(translate_text("Enter Quantity", target_language), min_value=1, step=1)

    # Get drug details (ID and remaining quantity)
    drug_id, remaining_qty = drug_dict[drug_name]

    # Check if the requested quantity is available
    if quantity > remaining_qty:
        st.error(translate_text("Insufficient stock. Please reduce the quantity.", target_language))
        cursor.close()
        conn.close()
        return
    
    # ✅ Fetch interaction warnings
    interaction_warning = get_drug_interactions(drug_name)

    # ✅ Display warning properly
    st.write(f"🔍 Checking interactions for: *{drug_name}*")
    if "⚠ Warning" in interaction_warning:
        st.warning(interaction_warning)  # ✅ Show warning in a proper alert
    else:
        st.success(interaction_warning)  # ✅ Show success message if no warning


    if st.button(translate_text("Place Order", target_language)):
        # Insert the order into the Orders table
        cursor.execute(
            "INSERT INTO Orders (C_ID, Qty, Name, Item) VALUES (%s, %s, %s, %s)",
            (st.session_state.user_id, quantity, f"Order for {drug_name}", drug_name)
        )

        # Update the remaining quantity in the Inventory table
        new_qty = remaining_qty - quantity
        cursor.execute(
            "UPDATE Inventory SET Rem_qty = %s WHERE D_ID = %s",
            (new_qty, drug_id)
        )

        conn.commit()
        st.success(translate_text("Successfully placed order!", target_language))

    cursor.close()
    conn.close()

# Function to View Orders (Customer)
def view_orders():
    if not st.session_state.logged_in or st.session_state.user_type != "Customer":
        st.error(translate_text("You must be logged in as a customer!", target_language))
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT Order_ID, Qty, Name, Item FROM Orders WHERE C_ID = %s", (st.session_state.user_id,))
    orders = cursor.fetchall()

    if orders:
        df = pd.DataFrame(orders, columns=["Order ID", "Quantity", "Order Name", "Item"])
        st.subheader(translate_text("Your Orders:", target_language))
        st.table(df)
    else:
        st.info(translate_text("No orders found.", target_language))

    cursor.close()
    conn.close()
# Function to check inventory and notify managers about out-of-stock drugs
def check_inventory_and_notify():
    try:
        # Instead of using db_config, directly use get_db_connection
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Query to find out-of-stock drugs (i.e., Rem_qty <= 0)
        query = """
            SELECT Inventory.D_ID, Drugs.D_name, Manager.M_ID, Manager.M_name, Manager.Ph_no
            FROM Inventory 
            JOIN Drugs ON Inventory.D_ID = Drugs.D_ID
            JOIN Manager ON Inventory.M_ID = Manager.M_ID
            WHERE Inventory.Rem_qty <= 0
        """
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            # Organize notifications per manager if needed
            manager_notifications = {}
            for row in results:
                m_id = row['M_ID']
                if m_id not in manager_notifications:
                    manager_notifications[m_id] = {
                        'M_name': row['M_name'],
                        'Ph_no': row['Ph_no'],  # You can extend this to include email if available
                        'drugs': []
                    }
                manager_notifications[m_id]['drugs'].append(row['D_name'])

            # For each manager, send a notification email
            for m_id, info in manager_notifications.items():
                # For demo purposes, we use a predefined email address.
                # In a real system, you could fetch the manager's email from the database.
                send_notification_email(info['M_name'], info['drugs'], recipient_email='siriabhat.cs22@rvce.edu.in')
        else:
            print("All drugs are in stock.")
    except mysql.connector.Error as err:
        print("Database error:", err)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def send_notification_email(manager_name, drugs, recipient_email):
    # Email server configuration: update with your actual SMTP server settings
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'siriashokbhat@gmail.com'
    smtp_password = 'povxtjpeiyjwauws'
    
    from_email = smtp_username
    subject = "Out of Stock Notification - Pharmacy Management System"
    
    # Compose the email body
    body = (
        f"Dear {manager_name},\n\n"
        f"The following drugs are currently out of stock: {', '.join(drugs)}.\n"
        "Please take the necessary action to reorder these drugs as soon as possible.\n\n"
        "Regards,\n"
        "Pharmacy Management System"
    )
    
    # Create the MIMEText message
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = recipient_email

    server = None  # Initialize server to ensure it is always declared before the 'finally' block
    try:
        # Establish a connection with the SMTP server and send the email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, recipient_email, msg.as_string())
        print(f"Notification email sent to {recipient_email}.")
    except Exception as e:
        print("Error sending email:", e)
    finally:
        if server:
            server.quit()  # Ensure server is only quit if it was initialized

# Function to View Inventory (Manager)
def view_inventory():
    if not st.session_state.logged_in or st.session_state.user_type != "Manager":
        st.error(translate_text("You must be logged in as a manager!", target_language))
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT D_ID, Rem_qty FROM Inventory")
    inventory = cursor.fetchall()

    if inventory:
        # Display inventory as a DataFrame
        df = pd.DataFrame(inventory, columns=["Drug ID", "Remaining Quantity"])
        st.subheader(translate_text("Inventory Status:", target_language))
        st.table(df)

        # Call the function to check inventory and send notifications
        check_inventory_and_notify()

    else:
        st.info(translate_text("No inventory data found.", target_language))

    cursor.close()
    conn.close()


# Function to View Sales Report (Manager)
def view_sales():
    if not st.session_state.logged_in or st.session_state.user_type != "Manager":
        st.error(translate_text("You must be logged in as a manager!", target_language))
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT Sale_ID, Total_amt, Date, Time FROM Sales")
    sales = cursor.fetchall()

    if sales:
        formatted_sales = []
        for sale in sales:
            sale_id, total_amt, date, time = sale
            # Handle the case where time is a timedelta object
            if isinstance(time, datetime.time):
                formatted_time = time.strftime('%H:%M:%S')  # Format time if it's a time object
            else:
                formatted_time = str(time)  # If it's not a time object, convert it to a string
            formatted_sales.append([sale_id, total_amt, date, formatted_time])

        # Convert formatted data to DataFrame
        df = pd.DataFrame(formatted_sales, columns=["Sale ID", "Total Amount", "Date", "Time"])
        st.subheader(translate_text("Sales Report", target_language))
        st.table(df)

    cursor.close()
    conn.close()

# Function to Manage Suppliers (Manager)
def manage_suppliers():
    if not st.session_state.logged_in or st.session_state.user_type != "Manager":
        st.error(translate_text("You must be logged in as a manager!", target_language))
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Display Current Suppliers
    cursor.execute("SELECT S_ID, S_name, S_address, S_phone FROM Supplier")
    suppliers = cursor.fetchall()

    if suppliers:
        df = pd.DataFrame(suppliers, columns=["Supplier ID", "Name", "Address", "Phone"])
        st.subheader(translate_text("Manage Suppliers", target_language))
        st.table(df)

    action = st.selectbox(translate_text("Choose Action", target_language), ["Add", "Update", "Delete"])

    if action == "Add":
        s_name = st.text_input(translate_text("Supplier Name", target_language))
        s_address = st.text_input(translate_text("Supplier Address", target_language))
        s_phone = st.text_input(translate_text("Supplier Phone", target_language))

        if st.button(translate_text("Add Supplier", target_language)):
            cursor.execute("INSERT INTO Supplier (S_name, S_address, S_phone) VALUES (%s, %s, %s)",
                           (s_name, s_address, s_phone))
            conn.commit()
            st.success(translate_text("Supplier added successfully!", target_language))

    elif action == "Update":
        supplier_id = st.number_input(translate_text("Enter Supplier ID to Update", target_language), min_value=1, step=1)
        cursor.execute("SELECT S_name, S_address, S_phone FROM Supplier WHERE S_ID = %s", (supplier_id,))
        supplier = cursor.fetchone()
        if supplier:
            current_name, current_address, current_phone = supplier
            new_name = st.text_input(translate_text("New Name (Leave blank to keep current)", target_language), value=current_name)
            new_address = st.text_input(translate_text("New Address (Leave blank to keep current)", target_language), value=current_address)
            new_phone = st.text_input(translate_text("New Phone (Leave blank to keep current)", target_language), value=current_phone)
            
            if st.button(translate_text("Update Supplier", target_language)):
                update_fields = []
                values = []
                
                if new_name and new_name != current_name:
                    update_fields.append("S_name = %s")
                    values.append(new_name)
                
                if new_address and new_address != current_address:
                    update_fields.append("S_address = %s")
                    values.append(new_address)
                
                if new_phone and new_phone != current_phone:
                    update_fields.append("S_phone = %s")
                    values.append(new_phone)
                if update_fields:
                    query = f"UPDATE Supplier SET {', '.join(update_fields)} WHERE S_ID = %s"
                    values.append(supplier_id)
                    
                    cursor.execute(query, tuple(values))
                    conn.commit()
                    st.success(translate_text("Supplier updated successfully!", target_language))
            else:
                st.info(translate_text("No changes were made.", target_language))

    elif action == "Delete":
        supplier_id_to_delete = st.number_input(translate_text("Enter Supplier ID to Delete", target_language), min_value=1, step=1)
        if st.button(translate_text("Delete Supplier", target_language)):
            cursor.execute("SELECT S_name FROM Supplier WHERE S_ID = %s", (supplier_id_to_delete,))
            supplier = cursor.fetchone()
            
            if supplier:
                supplier_name = supplier[0]
                cursor.execute("DELETE FROM Supplier WHERE S_ID = %s", (supplier_id_to_delete,))
                conn.commit()
                st.success(translate_text(f"Supplier {supplier_name} (ID: {supplier_id_to_delete}) deleted successfully!", target_language))
            else:
                st.warning(translate_text("Supplier ID not found.", target_language))


    cursor.close()
    conn.close()
# Function to get medicine details
def get_medicine_details(medicine_data):
    print(f"DEBUG: Scanned data: {medicine_data}")  # Print the QR code data for debugging
    # Example data retrieval logic (you can replace this with your DB query or API call)
    medicine_info = {
        "Medicine ID: 1\nName: Paracetamol": "Used for pain relief and fever reduction.",
        "Medicine ID: 2\nName: Aspirin": "Used for pain relief and to reduce inflammation.",
        "Medicine ID: 3\nName: Ibuprofen": "Used to reduce fever, pain, and inflammation."
    }
    return medicine_info.get(medicine_data, "Medicine details not found.")
# QR Code Scanner UI
def qr_code_scanner_ui():
    st.title(translate_text("📲 QR Code Scanner for Medicine Info", target_language))
    
    uploaded_file = st.file_uploader("Upload a QR Code Image", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        qr_result = scan_qr_from_image(uploaded_file)

        if qr_result:
            medicine_details = get_medicine_details(qr_result)
            st.success(medicine_details)
        else:
            st.error("❌ No QR code detected.")

# Scan QR Code from an uploaded image
def scan_qr_from_image(uploaded_file):
    image = Image.open(uploaded_file)
    decoded_objects = decode(image)
    if decoded_objects:
        return decoded_objects[0].data.decode("utf-8")
    else:
        return None
# Chat with Gemini AI
def chat_with_gemini(user_input):
    st.session_state.chat_history.append(("User", user_input))
    response = model.generate_content(user_input)
    bot_reply = response.text if response.text else translate_text("Sorry, I couldn't process that.", target_language)
    st.session_state.chat_history.append(("Gemini", bot_reply))
    return bot_reply

# Streamlit Chatbot UI
def chatbot_ui():
    st.title(translate_text("Virtual Chatbot Assistance", target_language))

    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)

    user_input = st.chat_input(translate_text("Ask me anything...", target_language))
    if user_input:
        bot_reply = chat_with_gemini(user_input)
        with st.chat_message("User"):
            st.write(user_input)
        with st.chat_message("Gemini"):
            st.write(bot_reply)

# Main Application for Pharmacy Management System
def main_pharmacy():
    st.title(translate_text("Pharmacy Management System", target_language))

    if not st.session_state.logged_in:
        option = st.radio(translate_text("Choose an option:", target_language), ["Login", "Signup"])

        if option == "Login":
            st.subheader(translate_text("Login", target_language))
            user_type = st.radio(translate_text("Login as:", target_language), ["Customer", "Manager"])
            username = st.text_input(translate_text("Enter your Email (Customer) or Name (Manager)", target_language))
            password = st.text_input(translate_text("Enter your Password", target_language), type="password")

            if st.button(translate_text("Login", target_language)):
                login_user(username, password, user_type)

        elif option == "Signup":
            st.subheader(translate_text("Signup - New Customer", target_language))
            email = st.text_input(translate_text("Email", target_language))
            password = st.text_input(translate_text("Password", target_language), type="password")
            name = st.text_input(translate_text("Full Name", target_language))
            age = st.number_input(translate_text("Age", target_language), min_value=1, step=1)
            sex = st.selectbox(translate_text("Sex", target_language), ["Male", "Female", "Other"])
            phone = st.text_input(translate_text("Phone Number", target_language))
            address = st.text_area(translate_text("Address", target_language))

            if st.button(translate_text("Signup", target_language)):
                if email and password and name and address:
                    signup_user(email, password, name, age, sex, phone, address)
                else:
                    st.error(translate_text("All fields except phone number are required!", target_language))

    else:
        if st.session_state.user_type == "Customer":
            st.subheader(translate_text("Welcome, Customer!", target_language))
            choice = st.selectbox(translate_text("Choose an option:", target_language), ["Place Order", "View Orders"])
            if choice == "Place Order":
                place_order()
            elif choice == "View Orders":
                view_orders()

        elif st.session_state.user_type == "Manager":
            st.subheader(translate_text("Welcome, Manager!", target_language))
            choice = st.selectbox(translate_text("Choose an option:", target_language), ["View Inventory", "Manage Suppliers", "See Sales"])
            if choice == "View Inventory":
                view_inventory()
            elif choice == "Manage Suppliers":
                manage_suppliers()
            elif choice == "See Sales":
                view_sales()

        if st.button(translate_text("Logout", target_language)):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.user_id = None
            st.success(translate_text("You have been logged out. Please refresh the page.", target_language))

# Add navigation to the app
def app_navigation():
    st.sidebar.title(translate_text("Navigation", target_language))
    page = st.sidebar.radio(translate_text("Choose a page:", target_language), ["Pharmacy Management", "AI Chatbot", "QR Code Scanner"])

    if page == "Pharmacy Management":
        main_pharmacy()
    elif page == "AI Chatbot":
        chatbot_ui()
    elif page == "QR Code Scanner":
        qr_code_scanner_ui()

if __name__ == "__main__":
    app_navigation()
