
from flask import Flask, render_template, request, redirect, session, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

# ================= FIREBASE CONNECTION =================

cred = credentials.Certificate(
    "sims-87a59-firebase-adminsdk-fbsvc-6b31e8298b.json"
)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)
app.secret_key = "student-internship-secret-key"


# ================= HOME =================

@app.route("/")
def home():
    return render_template("index.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "mobile": request.form.get("mobile"),
            "college": request.form.get("college"),
            "branch": request.form.get("branch"),
            "year": request.form.get("year"),
            "password": request.form.get("password"),
            "role": "student"
        }

        db.collection("students").add(data)

        return redirect("/login")

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        user_type = request.form.get("user_type")

        # Search user in Firebase
        users = db.collection("students").where(
            "email", "==", email
        ).stream()

        for user in users:

            data = user.to_dict()

            # Check password and user type
            if data.get("password") == password:

                if data.get("role") != user_type:
                    return "Invalid User Type"

                # Create session
                session["student_id"] = user.id
                session["student_name"] = data.get("name")
                session["role"] = data.get("role")

                # ================= ADMIN LOGIN =================
                if user_type == "admin":
                    return redirect("/admin-dashboard")

                # ================= STUDENT LOGIN =================
                if user_type == "student":
                    return redirect("/student-dashboard")

        # Login failed
        return "Invalid Email or Password"

    return render_template("login.html")

# ================= STUDENT DASHBOARD =================

@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect("/login")

    return render_template(
        "student-dashboard.html",
        name=session.get("student_name")
    )


# ================= PROFILE =================

@app.route("/profile")
def profile():

    if "student_id" not in session:
        return redirect("/login")

    student = db.collection("students").document(
        session["student_id"]
    ).get()

    if student.exists:
        data = student.to_dict()
    else:
        data = {}

    return render_template(
        "profile.html",
        student=data
    )


# ================= INTERNSHIPS =================

@app.route("/internship")
def internship():

    if "student_id" not in session:
        return redirect("/login")

    internships = db.collection("internships").stream()

    data = []

    for item in internships:
        internship_data = item.to_dict()
        internship_data["id"] = item.id
        data.append(internship_data)

    return render_template(
        "internship.html",
        internships=data
    )

# ================= APPLY =================

@app.route("/apply", methods=["GET", "POST"])
def apply():

    if "student_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        internship = request.form.get("internship")
        company = request.form.get("company")

        # Check duplicate application
        existing = db.collection("applications").where(
            "student_id", "==", session["student_id"]
        ).where(
            "internship", "==", internship
        ).stream()

        for application in existing:
            return "You have already applied for this internship."

        application = {
            "student_id": session["student_id"],
            "student_name": session["student_name"],
            "internship": internship,
            "company": company,
            "location": request.form.get("location", "Not Specified"),
            "appliedOn":__import__("datetime").datetime.now().strftime("%d-%m-%Y"),
            "status": "Pending"
        }

        db.collection("applications").add(application)

        return "Application Submitted Successfully"

    return render_template("apply.html")


# ================= MY APPLICATIONS =================

@app.route("/my-applications")
def my_applications():

    if "student_id" not in session:
        return redirect("/login")

    applications = db.collection("applications").where(
        "student_id", "==", session["student_id"]
    ).stream()

    data = []

    for item in applications:

        application = item.to_dict()
        data.append(application)

    return render_template(
        "my-applications.html",
        applications=data
    )


# ================= ADMIN DASHBOARD =================

@app.route("/admin-dashboard")
def admin_dashboard():

    if "student_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied - Admin Only", 403

    return render_template("admin-dashboard.html")


# ================= ADD INTERNSHIP =================

@app.route("/add-internship", methods=["GET", "POST"])
@app.route("/add-internship.html", methods=["GET", "POST"])
def add_internship():

    if "student_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied - Admin Only", 403

    if request.method == "POST":

        data = {
            "title": request.form.get("title"),
            "company": request.form.get("company"),
            "location": request.form.get("location"),
            "duration": request.form.get("duration"),
            "stipend": request.form.get("stipend"),
            "type": request.form.get("type"),
            "lastDate": request.form.get("lastDate"),
            "description": request.form.get("description")
        }

        db.collection("internships").add(data)

        return "Internship Added Successfully"

    return render_template("add-internship.html")

# ================= VIEW INTERNSHIPS =================

@app.route("/view-internships")
def view_internships():

    if "student_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied - Admin Only", 403

    internships = db.collection("internships").stream()

    data = []

    for internship in internships:
        internship_data = internship.to_dict()
        internship_data["id"] = internship.id
        data.append(internship_data)

    return render_template(
        "view-internship.html",
        internships=data
    )



# ================= VIEW STUDENTS =================

@app.route("/view-students")
def view_students():

    if "student_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied - Admin Only", 403

    students = db.collection("students").stream()

    data = []

    for student in students:

        item = student.to_dict()
        item.pop("password", None)
        data.append(item)

    return render_template(
        "view-students.html",
        students=data
    )


# ================= VIEW APPLICATIONS =================

@app.route("/view-applications")
def view_applications():

    if "student_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied - Admin Only", 403

    applications = db.collection("applications").stream()

    data = []

    for application in applications:

        application_data = application.to_dict()
        application_data["id"] = application.id
        data.append(application_data)

    return render_template(
        "view-applications.html",
        applications=data
    )


# ================= UPDATE APPLICATION STATUS =================

@app.route(
    "/update-application/<application_id>/<status>",
    methods=["POST"]
)
def update_application(application_id, status):

    if "student_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied - Admin Only", 403

    if status not in ["Approved", "Rejected"]:
        return "Invalid Status", 400

    db.collection("applications").document(
        application_id
    ).update({
        "status": status
    })

    return redirect("/view-applications")


# ================= TEST FIREBASE =================

@app.route("/test")
def test():

    students = db.collection("students").stream()

    data = []

    for student in students:
        data.append(student.to_dict())

    return jsonify(data)


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)

# ================= AI ASSISTANT =================

@app.route("/ai-agent", methods=["POST"])
def ai_agent():

    try:
        data = request.get_json()
        message = data.get("message", "").lower().strip()

        if not message:
            return jsonify({
                "reply": "Please enter your question."
            })

        # ---------------- GREETING ----------------

        if any(word in message for word in [
            "hello", "hi", "hey", "namaste"
        ]):
            reply = (
                "👋 Hello! I am your Internship AI Assistant. "
                "I can help you with internships, applications, "
                "eligibility, profile, resume and interview preparation."
            )

        # ---------------- APPLY INTERNSHIP ----------------

        elif any(word in message for word in [
            "apply", "application", "how to apply"
        ]):
            reply = (
                "📝 To apply for an internship, first login to your student "
                "account. Then open the Internships page, select an internship "
                "and click the Apply button. Fill in the required details and "
                "submit your application."
            )

        # ---------------- INTERNSHIP SEARCH ----------------

        elif any(word in message for word in [
            "internship", "internships", "find internship",
            "available internship", "internship list"
        ]):
            reply = (
                "🔍 You can find available internships from the Internships "
                "section. You can check the internship title, company, location "
                "and other available details before applying."
            )

        # ---------------- ELIGIBILITY ----------------

        elif any(word in message for word in [
            "eligibility", "eligible", "qualification", "criteria"
        ]):
            reply = (
                "✅ Internship eligibility depends on the company and internship. "
                "Check the internship requirements before applying. "
                "Students should make sure they meet the required branch, skills "
                "and educational criteria."
            )

        # ---------------- APPLICATION STATUS ----------------

        elif any(word in message for word in [
            "status", "application status", "approved",
            "rejected", "pending"
        ]):
            reply = (
                "📋 You can check your internship application status from "
                "the My Applications section. Your application may show a "
                "status such as Pending, Approved or Rejected."
            )

        # ---------------- PROFILE ----------------

        elif any(word in message for word in [
            "profile", "edit profile", "my details", "student profile"
        ]):
            reply = (
                "👤 You can view your student information from the Profile "
                "section. Make sure your personal, educational and contact "
                "details are correct."
            )

        # ---------------- RESUME ----------------

        elif any(word in message for word in [
            "resume", "cv", "curriculum"
        ]):
            reply = (
                "📄 A good internship resume should include your education, "
                "technical skills, projects, certifications and achievements. "
                "Keep it clear, simple and relevant to the internship."
            )

        # ---------------- INTERVIEW ----------------

        elif any(word in message for word in [
            "interview", "interview preparation", "interview tips"
        ]):
            reply = (
                "🎯 For an internship interview, prepare your introduction, "
                "technical skills, academic projects and basic questions "
                "related to your branch. Be confident and explain your projects "
                "clearly."
            )

        # ---------------- SKILLS ----------------

        elif any(word in message for word in [
            "skills", "skill", "learn", "technology"
        ]):
            reply = (
                "💡 For an AIML internship, useful skills include Python, "
                "Machine Learning, Data Analysis, SQL, basic AI concepts, "
                "Git/GitHub and communication skills."
            )

        # ---------------- DOCUMENTS ----------------

        elif any(word in message for word in [
            "documents", "document", "certificate", "documents required"
        ]):
            reply = (
                "📑 Common internship documents may include your resume, "
                "college ID, educational details, certificates and other "
                "documents requested by the company."
            )

        # ---------------- LOGOUT ----------------

        elif "logout" in message or "log out" in message:
            reply = (
                "🔐 You can use the Logout option in your dashboard to safely "
                "sign out of your student account."
            )

        # ---------------- THANK YOU ----------------

        elif any(word in message for word in [
            "thank you", "thanks", "thank"
        ]):
            reply = (
                "😊 You're welcome! I'm always here to help you with "
                "your internship journey."
            )

        # ---------------- UNKNOWN QUESTION ----------------

        else:
            reply = (
                "🤖 I can help you with internships, applying for internships, "
                "application status, eligibility, profile, resume, interview "
                "preparation and AIML skills. "
                "\n\nTry asking: "
                "\"How can I apply for an internship?\""
            )

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print("AI Assistant Error:", e)

        return jsonify({
            "reply": "❌ Sorry, something went wrong. Please try again."
        }), 500

