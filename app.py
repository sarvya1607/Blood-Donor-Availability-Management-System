from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps
from datetime import date

from config import get_db_connection


app = Flask(__name__)

# Secret key used for Flask sessions
app.config["SECRET_KEY"] = "change-this-secret-key-before-deployment"


# =========================================================
# DATABASE HELPER FUNCTIONS
# =========================================================

def fetch_one(query, params=()):
    """Fetch a single record from MySQL."""

    connection = get_db_connection()

    if connection is None:
        return None

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchone()

    except Exception as error:
        print("Database Fetch Error:", error)
        return None

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


def fetch_all(query, params=()):
    """Fetch multiple records from MySQL."""

    connection = get_db_connection()

    if connection is None:
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()

    except Exception as error:
        print("Database Fetch Error:", error)
        return []

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


def execute_query(query, params=()):
    """Execute INSERT, UPDATE or DELETE queries."""

    connection = get_db_connection()

    if connection is None:
        return False

    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        return True

    except Exception as error:
        connection.rollback()
        print("Database Execute Error:", error)
        return False

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


# =========================================================
# LOGIN REQUIRED DECORATOR
# =========================================================

def login_required(route_function):
    """Allow access only to logged-in users."""

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


def admin_required(route_function):
    """Allow access only to logged-in administrators."""

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if "admin_id" not in session:
            flash("Please login as administrator.", "warning")
            return redirect(url_for("admin_login"))

        return route_function(*args, **kwargs)

    return wrapper


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def index():

    donor_record = fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM donors
        WHERE is_available = 1
        """
    )

    request_record = fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM blood_requests
        """
    )

    donor_count = donor_record["total"] if donor_record else 0
    request_count = request_record["total"] if request_record else 0

    return render_template(
        "index.html",
        donor_count=donor_count,
        request_count=request_count
    )


# =========================================================
# USER REGISTRATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password", ""
        )

        # Validate required fields
        if not all([full_name, email, phone, password]):
            flash("Please fill in all required fields.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "danger"
            )
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if not phone.isdigit() or len(phone) != 10:
            flash(
                "Please enter a valid 10-digit mobile number.",
                "danger"
            )
            return render_template("register.html")

        # Check whether the email already exists
        existing_user = fetch_one(
            "SELECT user_id FROM users WHERE email = %s",
            (email,)
        )

        if existing_user:
            flash("This email is already registered.", "danger")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        success = execute_query(
            """
            INSERT INTO users
            (full_name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (
                full_name,
                email,
                phone,
                password_hash
            )
        )

        if success:
            flash(
                "Registration successful! Please login.",
                "success"
            )
            return redirect(url_for("login"))

        flash(
            "Registration failed. Please check the database connection.",
            "danger"
        )

    return render_template("register.html")


# =========================================================
# USER LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter email and password.", "danger")
            return render_template("login.html")

        user = fetch_one(
            """
            SELECT user_id, full_name, email, password_hash
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        if user and check_password_hash(
            user["password_hash"], password
        ):

            session.clear()

            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]

            flash("Login successful. Welcome!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# =========================================================
# USER LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("index"))


# =========================================================
# USER DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    donor = fetch_one(
        """
        SELECT donor_id, blood_group, city, is_available
        FROM donors
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total_requests_record = fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM blood_requests
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total_requests = (
        total_requests_record["total"]
        if total_requests_record else 0
    )

    return render_template(
        "dashboard.html",
        donor=donor,
        total_requests=total_requests
    )


# =========================================================
# DONOR REGISTRATION
# =========================================================

@app.route("/donor-register", methods=["GET", "POST"])
@login_required
def donor_register():

    user_id = session["user_id"]

    existing_donor = fetch_one(
        """
        SELECT donor_id
        FROM donors
        WHERE user_id = %s
        """,
        (user_id,)
    )

    if request.method == "POST":

        blood_group = request.form.get(
            "blood_group", ""
        ).strip().upper()

        age_text = request.form.get("age", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get(
            "state", "Maharashtra"
        ).strip()

        last_donation_date = request.form.get(
            "last_donation_date", ""
        ).strip()

        availability_text = request.form.get(
            "is_available", "1"
        )

        allowed_blood_groups = [
            "A+", "A-", "B+", "B-",
            "AB+", "AB-", "O+", "O-"
        ]

        if blood_group not in allowed_blood_groups:
            flash("Please select a valid blood group.", "danger")
            return render_template("donor_register.html")

        if not age_text.isdigit():
            flash("Please enter a valid age.", "danger")
            return render_template("donor_register.html")

        age = int(age_text)

        if age < 18 or age > 65:
            flash(
                "Donor age must be between 18 and 65 for this system.",
                "danger"
            )
            return render_template("donor_register.html")

        if not city:
            flash("Please enter your city.", "danger")
            return render_template("donor_register.html")

        if not state:
            state = "Maharashtra"

        if availability_text not in ("0", "1"):
            availability_text = "1"

        is_available = int(availability_text)

        # An empty date is stored as SQL NULL
        if not last_donation_date:
            last_donation_date = None
        else:
            try:
                parsed_date = date.fromisoformat(
                    last_donation_date
                )

                if parsed_date > date.today():
                    flash(
                        "Last donation date cannot be in the future.",
                        "danger"
                    )
                    return render_template(
                        "donor_register.html"
                    )

            except ValueError:
                flash("Please enter a valid donation date.", "danger")
                return render_template("donor_register.html")

        if existing_donor:

            success = execute_query(
                """
                UPDATE donors
                SET blood_group = %s,
                    age = %s,
                    city = %s,
                    state = %s,
                    last_donation_date = %s,
                    is_available = %s
                WHERE user_id = %s
                """,
                (
                    blood_group,
                    age,
                    city,
                    state,
                    last_donation_date,
                    is_available,
                    user_id
                )
            )

        else:

            success = execute_query(
                """
                INSERT INTO donors
                (
                    user_id,
                    blood_group,
                    age,
                    city,
                    state,
                    last_donation_date,
                    is_available
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    blood_group,
                    age,
                    city,
                    state,
                    last_donation_date,
                    is_available
                )
            )

        if success:
            flash(
                "Donor profile saved successfully.",
                "success"
            )
            return redirect(url_for("dashboard"))

        flash(
            "Unable to save donor profile. Please try again.",
            "danger"
        )

    return render_template("donor_register.html")


# =========================================================
# SEARCH DONORS
# =========================================================

@app.route("/search-donor", methods=["GET", "POST"])
def search_donor():

    donors = []
    searched = False
    selected_blood_group = ""
    selected_city = ""

    if request.method == "POST":

        selected_blood_group = request.form.get(
            "blood_group", ""
        ).strip().upper()

        selected_city = request.form.get(
            "city", ""
        ).strip()

        searched = True

        query = """
            SELECT
                d.donor_id,
                u.full_name,
                u.phone,
                d.blood_group,
                d.age,
                d.city,
                d.state
            FROM donors d
            INNER JOIN users u ON d.user_id = u.user_id
            WHERE d.is_available = 1
        """

        params = []

        if selected_blood_group:
            query += " AND d.blood_group = %s"
            params.append(selected_blood_group)

        if selected_city:
            query += " AND d.city LIKE %s"
            params.append(f"%{selected_city}%")

        query += " ORDER BY d.created_at DESC"

        donors = fetch_all(query, tuple(params))

    return render_template(
        "search_donor.html",
        donors=donors,
        searched=searched,
        selected_blood_group=selected_blood_group,
        selected_city=selected_city
    )


# =========================================================
# CREATE BLOOD REQUEST
# =========================================================

@app.route("/blood-request", methods=["GET", "POST"])
@login_required
def blood_request():

    if request.method == "POST":

        patient_name = request.form.get(
            "patient_name", ""
        ).strip()

        blood_group = request.form.get(
            "blood_group", ""
        ).strip().upper()

        units_text = request.form.get(
            "units_required", "1"
        ).strip()

        hospital_name = request.form.get(
            "hospital_name", ""
        ).strip()

        city = request.form.get("city", "").strip()

        contact_phone = request.form.get(
            "contact_phone", ""
        ).strip()

        urgency = request.form.get(
            "urgency", "Normal"
        ).strip()

        allowed_blood_groups = [
            "A+", "A-", "B+", "B-",
            "AB+", "AB-", "O+", "O-"
        ]

        allowed_urgencies = [
            "Normal", "Urgent", "Emergency"
        ]

        if not all([
            patient_name,
            blood_group,
            units_text,
            hospital_name,
            city,
            contact_phone
        ]):
            flash("Please fill in all required fields.", "danger")
            return render_template("blood_request.html")

        if blood_group not in allowed_blood_groups:
            flash("Please select a valid blood group.", "danger")
            return render_template("blood_request.html")

        if not units_text.isdigit():
            flash("Please enter a valid number of units.", "danger")
            return render_template("blood_request.html")

        units_required = int(units_text)

        if units_required < 1 or units_required > 20:
            flash(
                "Units required must be between 1 and 20.",
                "danger"
            )
            return render_template("blood_request.html")

        if not contact_phone.isdigit() or len(contact_phone) != 10:
            flash(
                "Please enter a valid 10-digit contact number.",
                "danger"
            )
            return render_template("blood_request.html")

        if urgency not in allowed_urgencies:
            urgency = "Normal"

        success = execute_query(
            """
            INSERT INTO blood_requests
            (
                user_id,
                patient_name,
                blood_group,
                units_required,
                hospital_name,
                city,
                contact_phone,
                urgency,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                patient_name,
                blood_group,
                units_required,
                hospital_name,
                city,
                contact_phone,
                urgency,
                "Pending"
            )
        )

        if success:
            flash(
                "Blood request submitted successfully.",
                "success"
            )
            return redirect(url_for("my_requests"))

        flash(
            "Unable to submit the blood request.",
            "danger"
        )

    return render_template("blood_request.html")


# =========================================================
# MY BLOOD REQUESTS
# =========================================================

@app.route("/my-requests")
@login_required
def my_requests():

    user_id = session["user_id"]

    requests_list = fetch_all(
        """
        SELECT
            request_id,
            patient_name,
            blood_group,
            units_required,
            hospital_name,
            city,
            contact_phone,
            urgency,
            status,
            created_at
        FROM blood_requests
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    return render_template(
        "my_requests.html",
        requests=requests_list
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get("password", "")

        if not username or not password:
            flash("Enter username and password.", "danger")
            return render_template("admin_login.html")

        admin = fetch_one(
            """
            SELECT admin_id, username, password_hash
            FROM admin
            WHERE username = %s
            """,
            (username,)
        )

        if admin and check_password_hash(
            admin["password_hash"], password
        ):

            session.clear()

            session["admin_id"] = admin["admin_id"]
            session["admin_username"] = admin["username"]

            flash("Admin login successful.", "success")

            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin username or password.", "danger")

    return render_template("admin_login.html")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():

    donor_record = fetch_one(
        "SELECT COUNT(*) AS total FROM donors"
    )

    request_record = fetch_one(
        "SELECT COUNT(*) AS total FROM blood_requests"
    )

    pending_record = fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM blood_requests
        WHERE status = 'Pending'
        """
    )

    donor_count = donor_record["total"] if donor_record else 0
    request_count = request_record["total"] if request_record else 0
    pending_count = pending_record["total"] if pending_record else 0

    requests_list = fetch_all(
        """
        SELECT
            request_id,
            patient_name,
            blood_group,
            units_required,
            hospital_name,
            city,
            contact_phone,
            urgency,
            status,
            created_at
        FROM blood_requests
        ORDER BY
            CASE urgency
                WHEN 'Emergency' THEN 1
                WHEN 'Urgent' THEN 2
                ELSE 3
            END,
            created_at DESC
        """
    )

    all_donors = fetch_all(
        """
        SELECT
            d.donor_id,
            u.full_name,
            u.email,
            u.phone,
            d.blood_group,
            d.age,
            d.city,
            d.state,
            d.is_available
        FROM donors d
        INNER JOIN users u ON d.user_id = u.user_id
        ORDER BY d.created_at DESC
        """
    )

    return render_template(
        "admin_dashboard.html",
        donor_count=donor_count,
        request_count=request_count,
        pending_count=pending_count,
        requests=requests_list,
        donors=all_donors
    )


# =========================================================
# UPDATE BLOOD REQUEST STATUS
# =========================================================

@app.route(
    "/admin/request-status/<int:request_id>",
    methods=["POST"]
)
@admin_required
def update_request_status(request_id):

    new_status = request.form.get("status", "").strip()

    allowed_statuses = [
        "Pending",
        "Approved",
        "Completed",
        "Rejected"
    ]

    if new_status not in allowed_statuses:
        flash("Invalid request status.", "danger")
        return redirect(url_for("admin_dashboard"))

    existing_request = fetch_one(
        """
        SELECT request_id
        FROM blood_requests
        WHERE request_id = %s
        """,
        (request_id,)
    )

    if not existing_request:
        flash("Blood request not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    success = execute_query(
        """
        UPDATE blood_requests
        SET status = %s
        WHERE request_id = %s
        """,
        (new_status, request_id)
    )

    if success:
        flash(
            "Blood request status updated successfully.",
            "success"
        )
    else:
        flash(
            "Unable to update the request status.",
            "danger"
        )

    return redirect(url_for("admin_dashboard"))


# =========================================================
# CONTACT US
# =========================================================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        subject = request.form.get(
            "subject", ""
        ).strip()

        message = request.form.get(
            "message", ""
        ).strip()

        if not all([full_name, email, subject, message]):
            flash("Please complete all contact form fields.", "danger")
            return render_template("contact.html")

        success = execute_query(
            """
            INSERT INTO contact_messages
            (full_name, email, subject, message)
            VALUES (%s, %s, %s, %s)
            """,
            (
                full_name,
                email,
                subject,
                message
            )
        )

        if success:
            flash(
                "Your message has been submitted successfully.",
                "success"
            )
            return redirect(url_for("contact"))

        flash(
            "Unable to submit your message. Please try again.",
            "danger"
        )

    return render_template("contact.html")


# =========================================================
# PAGE NOT FOUND
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template("index.html"), 404


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)