from flask import Flask, render_template, request, g
import os
import psycopg2
import qrcode
import io
import base64

app = Flask(__name__)


class Database:
    @property
    def connection(self):
        if "db_connection" not in g:
            database_url = os.environ.get("DATABASE_URL")

            if not database_url:
                raise RuntimeError("DATABASE_URL is not configured")

            g.db_connection = psycopg2.connect(
                database_url,
                sslmode="require"
            )

        return g.db_connection


mysql = Database()


@app.teardown_appcontext
def close_db_connection(error=None):
    connection = g.pop("db_connection", None)

    if connection is not None:
        connection.close()



# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM admin WHERE username=%s AND password=%s",
        (username, password)
    )

    admin = cursor.fetchone()

    cursor.close()

    if admin:
        return render_template("dashboard.html")

    return "Invalid Username or Password"


# =========================================================
# STUDENTS
# =========================================================

@app.route("/students")
def students():

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    cursor.close()

    return render_template(
        "students.html",
        students=students
    )


@app.route("/add_student", methods=["POST"])
def add_student():

    register_no = request.form["register_no"]
    student_name = request.form["student_name"]
    department = request.form["department"]
    year = request.form["year"]
    exam_name = request.form["exam_name"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO students
        (register_no, student_name, department, year, exam_name)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            register_no,
            student_name,
            department,
            year,
            exam_name
        )
    )

    mysql.connection.commit()

    cursor.close()

    return students()


@app.route("/delete_student/<int:id>")
def delete_student(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    return students()


@app.route("/edit_student/<int:id>")
def edit_student(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cursor.fetchone()

    cursor.close()

    return render_template(
        "edit_student.html",
        student=student
    )


@app.route("/update_student/<int:id>", methods=["POST"])
def update_student(id):

    register_no = request.form["register_no"]
    student_name = request.form["student_name"]
    department = request.form["department"]
    year = request.form["year"]
    exam_name = request.form["exam_name"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        UPDATE students
        SET register_no=%s,
            student_name=%s,
            department=%s,
            year=%s,
            exam_name=%s
        WHERE id=%s
        """,
        (
            register_no,
            student_name,
            department,
            year,
            exam_name,
            id
        )
    )

    mysql.connection.commit()

    cursor.close()

    return students()


# =========================================================
# HALLS
# =========================================================

@app.route("/halls")
def halls():

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM halls")

    halls_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "halls.html",
        halls=halls_data,
        message=None
    )


def halls_with_message(message):

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM halls")

    halls_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "halls.html",
        halls=halls_data,
        message=message
    )


@app.route("/add_hall", methods=["POST"])
def add_hall():

    hall_name = request.form["hall_name"].strip()
    room_no = request.form["room_no"].strip()
    capacity = request.form["capacity"].strip()

    cursor = mysql.connection.cursor()

    if hall_name == "" or room_no == "" or capacity == "":
        cursor.close()

        return halls_with_message(
            "Please fill all fields"
        )

    try:

        capacity_value = int(capacity)

        if capacity_value <= 0:
            cursor.close()

            return halls_with_message(
                "Invalid capacity"
            )

    except ValueError:

        cursor.close()

        return halls_with_message(
            "Invalid capacity"
        )

    cursor.execute(
        """
        SELECT id
        FROM halls
        WHERE LOWER(TRIM(hall_name)) =
              LOWER(TRIM(%s))
        """,
        (hall_name,)
    )

    existing_hall = cursor.fetchone()

    if existing_hall:

        cursor.close()

        return halls_with_message(
            f"Hall already exists: {hall_name}"
        )

    cursor.execute(
        """
        SELECT id
        FROM halls
        WHERE LOWER(TRIM(room_no)) =
              LOWER(TRIM(%s))
        """,
        (room_no,)
    )

    existing_room = cursor.fetchone()

    if existing_room:

        cursor.close()

        return halls_with_message(
            f"Room {room_no} already exists"
        )

    cursor.execute(
        """
        INSERT INTO halls
        (hall_name, room_no, capacity)
        VALUES (%s, %s, %s)
        """,
        (
            hall_name,
            room_no,
            capacity_value
        )
    )

    mysql.connection.commit()

    cursor.close()

    return halls()


@app.route("/delete_hall/<int:id>")
def delete_hall(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM halls WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    return halls()


@app.route("/edit_hall/<int:id>")
def edit_hall(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM halls WHERE id=%s",
        (id,)
    )

    hall = cursor.fetchone()

    cursor.close()

    return render_template(
        "edit_hall.html",
        hall=hall
    )


@app.route("/update_hall/<int:id>", methods=["POST"])
def update_hall(id):

    hall_name = request.form["hall_name"].strip()
    room_no = request.form["room_no"].strip()
    capacity = request.form["capacity"].strip()

    cursor = mysql.connection.cursor()

    if hall_name == "" or room_no == "" or capacity == "":

        cursor.close()

        return render_template(
            "edit_hall.html",
            hall=(id, hall_name, room_no, capacity),
            message="Please fill all fields"
        )

    try:

        capacity_value = int(capacity)

        if capacity_value <= 0:

            cursor.close()

            return render_template(
                "edit_hall.html",
                hall=(id, hall_name, room_no, capacity),
                message="Invalid capacity"
            )

    except ValueError:

        cursor.close()

        return render_template(
            "edit_hall.html",
            hall=(id, hall_name, room_no, capacity),
            message="Invalid capacity"
        )

    cursor.execute(
        """
        SELECT id
        FROM halls
        WHERE LOWER(TRIM(hall_name)) =
              LOWER(TRIM(%s))
        AND id != %s
        """,
        (
            hall_name,
            id
        )
    )

    existing_hall = cursor.fetchone()

    if existing_hall:

        cursor.close()

        return render_template(
            "edit_hall.html",
            hall=(id, hall_name, room_no, capacity),
            message=f"Hall already exists: {hall_name}"
        )

    cursor.execute(
        """
        SELECT id
        FROM halls
        WHERE LOWER(TRIM(room_no)) =
              LOWER(TRIM(%s))
        AND id != %s
        """,
        (
            room_no,
            id
        )
    )

    existing_room = cursor.fetchone()

    if existing_room:

        cursor.close()

        return render_template(
            "edit_hall.html",
            hall=(id, hall_name, room_no, capacity),
            message=f"Room {room_no} already exists"
        )

    cursor.execute(
        """
        UPDATE halls
        SET hall_name=%s,
            room_no=%s,
            capacity=%s
        WHERE id=%s
        """,
        (
            hall_name,
            room_no,
            capacity_value,
            id
        )
    )

    mysql.connection.commit()

    cursor.close()

    return halls()


# =========================================================
# INVIGILATORS
# =========================================================

@app.route("/invigilators")
def invigilators():

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM invigilators")

    invigilators = cursor.fetchall()

    cursor.close()

    return render_template(
        "invigilators.html",
        invigilators=invigilators
    )


@app.route("/add_invigilator", methods=["POST"])
def add_invigilator():

    name = request.form["name"]
    employee_id = request.form["employee_id"]
    department = request.form["department"]
    phone = request.form["phone"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO invigilators
        (name, employee_id, department, phone)
        VALUES (%s, %s, %s, %s)
        """,
        (
            name,
            employee_id,
            department,
            phone
        )
    )

    mysql.connection.commit()

    cursor.close()

    return invigilators()


@app.route("/edit_invigilator/<int:id>")
def edit_invigilator(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM invigilators WHERE id=%s",
        (id,)
    )

    invigilator = cursor.fetchone()

    cursor.close()

    return render_template(
        "edit_invigilator.html",
        invigilator=invigilator
    )


@app.route("/update_invigilator/<int:id>", methods=["POST"])
def update_invigilator(id):

    name = request.form["name"]
    employee_id = request.form["employee_id"]
    department = request.form["department"]
    phone = request.form["phone"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        UPDATE invigilators
        SET name=%s,
            employee_id=%s,
            department=%s,
            phone=%s
        WHERE id=%s
        """,
        (
            name,
            employee_id,
            department,
            phone,
            id
        )
    )

    mysql.connection.commit()

    cursor.close()

    return invigilators()


@app.route("/delete_invigilator/<int:id>")
def delete_invigilator(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM invigilators WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    return invigilators()


# =========================================================
# INVIGILATOR HALL ASSIGNMENT
# =========================================================

@app.route("/assign_invigilator")
def assign_invigilator():

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM invigilators")

    invigilators = cursor.fetchall()

    cursor.execute("SELECT * FROM halls")

    halls = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            invigilator_assignments.id,
            invigilators.name,
            invigilators.employee_id,
            halls.hall_name,
            halls.room_no,
            invigilator_assignments.invigilator_id,
            invigilator_assignments.hall_id
        FROM invigilator_assignments
        JOIN invigilators
        ON invigilator_assignments.invigilator_id =
           invigilators.id
        JOIN halls
        ON invigilator_assignments.hall_id =
           halls.id
        ORDER BY invigilator_assignments.id
        """
    )

    assignments = cursor.fetchall()

    cursor.close()

    return render_template(
        "assign_invigilator.html",
        invigilators=invigilators,
        halls=halls,
        assignments=assignments
    )


@app.route("/add_assignment", methods=["POST"])
def add_assignment():

    invigilator_id = request.form["invigilator_id"]
    hall_id = request.form["hall_id"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT halls.room_no
        FROM invigilator_assignments
        JOIN halls
        ON invigilator_assignments.hall_id =
           halls.id
        WHERE invigilator_assignments.invigilator_id=%s
        """,
        (invigilator_id,)
    )

    existing = cursor.fetchone()

    if existing:

        cursor.close()

        return render_assign_page(
            message=f"Already Assigned to Room {existing[0]}",
            message_type="error"
        )

    cursor.execute(
        """
        SELECT invigilators.name
        FROM invigilator_assignments
        JOIN invigilators
        ON invigilator_assignments.invigilator_id =
           invigilators.id
        WHERE invigilator_assignments.hall_id=%s
        """,
        (hall_id,)
    )

    hall_existing = cursor.fetchone()

    if hall_existing:

        cursor.close()

        return render_assign_page(
            message=f"Room already assigned to {hall_existing[0]}",
            message_type="error"
        )

    cursor.execute(
        """
        INSERT INTO invigilator_assignments
        (invigilator_id, hall_id)
        VALUES (%s, %s)
        """,
        (
            invigilator_id,
            hall_id
        )
    )

    mysql.connection.commit()

    cursor.close()

    return assign_invigilator()


def render_assign_page(message=None, message_type="error"):

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM invigilators")

    invigilators = cursor.fetchall()

    cursor.execute("SELECT * FROM halls")

    halls = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            invigilator_assignments.id,
            invigilators.name,
            invigilators.employee_id,
            halls.hall_name,
            halls.room_no,
            invigilator_assignments.invigilator_id,
            invigilator_assignments.hall_id
        FROM invigilator_assignments
        JOIN invigilators
        ON invigilator_assignments.invigilator_id =
           invigilators.id
        JOIN halls
        ON invigilator_assignments.hall_id =
           halls.id
        ORDER BY invigilator_assignments.id
        """
    )

    assignments = cursor.fetchall()

    cursor.close()

    return render_template(
        "assign_invigilator.html",
        invigilators=invigilators,
        halls=halls,
        assignments=assignments,
        message=message,
        message_type=message_type
    )


@app.route("/edit_assignment/<int:id>")
def edit_assignment(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM invigilator_assignments WHERE id=%s",
        (id,)
    )

    assignment = cursor.fetchone()

    cursor.execute("SELECT * FROM invigilators")

    invigilators = cursor.fetchall()

    cursor.execute("SELECT * FROM halls")

    halls = cursor.fetchall()

    cursor.close()

    if not assignment:
        return "Assignment not found"

    return render_template(
        "edit_assignment.html",
        assignment=assignment,
        invigilators=invigilators,
        halls=halls
    )


@app.route("/update_assignment/<int:id>", methods=["POST"])
def update_assignment(id):

    invigilator_id = request.form["invigilator_id"]
    hall_id = request.form["hall_id"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT
            invigilator_assignments.id,
            halls.room_no
        FROM invigilator_assignments
        JOIN halls
        ON invigilator_assignments.hall_id =
           halls.id
        WHERE invigilator_assignments.invigilator_id=%s
        AND invigilator_assignments.id!=%s
        """,
        (
            invigilator_id,
            id
        )
    )

    existing = cursor.fetchone()

    if existing:

        cursor.close()

        return render_edit_assignment(
            id,
            f"Already Assigned to Room {existing[1]}"
        )

    cursor.execute(
        """
        SELECT
            invigilator_assignments.id,
            invigilators.name
        FROM invigilator_assignments
        JOIN invigilators
        ON invigilator_assignments.invigilator_id =
           invigilators.id
        WHERE invigilator_assignments.hall_id=%s
        AND invigilator_assignments.id!=%s
        """,
        (
            hall_id,
            id
        )
    )

    hall_existing = cursor.fetchone()

    if hall_existing:

        cursor.close()

        return render_edit_assignment(
            id,
            f"Room already assigned to {hall_existing[1]}"
        )

    cursor.execute(
        """
        UPDATE invigilator_assignments
        SET invigilator_id=%s,
            hall_id=%s
        WHERE id=%s
        """,
        (
            invigilator_id,
            hall_id,
            id
        )
    )

    mysql.connection.commit()

    cursor.close()

    return assign_invigilator()


def render_edit_assignment(id, message=None):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM invigilator_assignments WHERE id=%s",
        (id,)
    )

    assignment = cursor.fetchone()

    cursor.execute("SELECT * FROM invigilators")

    invigilators = cursor.fetchall()

    cursor.execute("SELECT * FROM halls")

    halls = cursor.fetchall()

    cursor.close()

    return render_template(
        "edit_assignment.html",
        assignment=assignment,
        invigilators=invigilators,
        halls=halls,
        message=message
    )


@app.route("/delete_assignment/<int:id>")
def delete_assignment(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM invigilator_assignments WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    return assign_invigilator()


# =========================================================
# SEAT ALLOCATION
# =========================================================

@app.route("/seat_allocation")
def seat_allocation():

    view_hall_id = request.args.get("view_hall_id")

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM halls ORDER BY id")
    halls = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            seat_allocations.id,
            students.register_no,
            students.student_name,
            halls.hall_name,
            halls.room_no,
            seat_allocations.seat_no
        FROM seat_allocations
        JOIN students
        ON seat_allocations.student_id = students.id
        JOIN halls
        ON seat_allocations.hall_id = halls.id
        ORDER BY seat_allocations.id
        """
    )

    allocations = cursor.fetchall()

    selected_hall = None
    seats = []
    allocated_count = 0

    if view_hall_id:

        cursor.execute(
            "SELECT * FROM halls WHERE id=%s",
            (view_hall_id,)
        )

        selected_hall = cursor.fetchone()

        if selected_hall:

            capacity = selected_hall[3]

            cursor.execute(
                """
                SELECT
                    seat_allocations.seat_no,
                    students.register_no,
                    students.student_name,
                    students.department
                FROM seat_allocations
                JOIN students
                ON seat_allocations.student_id = students.id
                WHERE seat_allocations.hall_id=%s
                ORDER BY seat_allocations.id
                """,
                (view_hall_id,)
            )

            hall_allocations = cursor.fetchall()

            allocation_map = {}

            for allocation in hall_allocations:

                allocation_map[allocation[0]] = {
                    "register_no": allocation[1],
                    "student_name": allocation[2],
                    "department": allocation[3]
                }

            for number in range(1, capacity + 1):

                seat_no = "S" + str(number)

                if seat_no in allocation_map:

                    data = allocation_map[seat_no]

                    seats.append({
                        "seat_no": seat_no,
                        "register_no": data["register_no"],
                        "student_name": data["student_name"],
                        "department": data["department"]
                    })

                    allocated_count += 1

                else:

                    seats.append({
                        "seat_no": seat_no,
                        "register_no": "",
                        "student_name": "",
                        "department": ""
                    })

    cursor.close()

    return render_template(
        "seat_allocation.html",
        halls=halls,
        allocations=allocations,
        selected_hall=selected_hall,
        seats=seats,
        allocated_count=allocated_count
    )


@app.route("/allocate_seats", methods=["POST"])
def allocate_seats():

    hall_id = request.form["hall_id"]

    cursor = mysql.connection.cursor()

    # =====================================================
    # CHECK HALL
    # =====================================================

    cursor.execute(
        "SELECT hall_name, room_no, capacity FROM halls WHERE id=%s",
        (hall_id,)
    )

    hall = cursor.fetchone()

    if not hall:

        cursor.close()

        return """
        <script>
            alert("❌ Hall not found!");
            window.location.href="/seat_allocation";
        </script>
        """


    hall_name = hall[0]
    room_no = hall[1]
    capacity = hall[2]


    # =====================================================
    # GET TOTAL STUDENTS
    # =====================================================

    cursor.execute(
        "SELECT id FROM students ORDER BY id"
    )

    students = cursor.fetchall()

    total_students = len(students)


    # =====================================================
    # SMART CAPACITY VALIDATION
    # =====================================================

    if total_students > capacity:

        cursor.close()

        return f"""
        <script>

            alert(
                "⚠️ SMART ALLOCATION WARNING\\n\\n"
                + "Hall: {hall_name}\\n"
                + "Room: {room_no}\\n"
                + "Hall Capacity: {capacity}\\n"
                + "Total Students: {total_students}\\n\\n"
                + "❌ Hall capacity exceeded!\\n"
                + "Please select a larger hall or multiple halls."
            );

            window.location.href="/seat_allocation";

        </script>
        """


    # =====================================================
    # DELETE OLD ALLOCATIONS
    # =====================================================

    cursor.execute(
        "DELETE FROM seat_allocations"
    )


    # =====================================================
    # AUTOMATIC SEAT ALLOCATION
    # =====================================================

    seat_number = 1

    for student in students:

        seat_no = "S" + str(seat_number)

        cursor.execute(
            """
            INSERT INTO seat_allocations
            (student_id, hall_id, seat_no)
            VALUES (%s, %s, %s)
            """,
            (
                student[0],
                hall_id,
                seat_no
            )
        )

        seat_number += 1


    mysql.connection.commit()

    cursor.close()


    # =====================================================
    # SUCCESS MESSAGE
    # =====================================================

    return f"""
    <script>

        alert(
            "✅ SMART SEAT ALLOCATION COMPLETED!\\n\\n"
            + "Hall: {hall_name}\\n"
            + "Room: {room_no}\\n"
            + "Students Allocated: {total_students}\\n"
            + "Capacity: {capacity}\\n\\n"
            + "🤖 AI Seating Intelligence verified the allocation."
        );

        window.location.href="/seat_allocation";

    </script>
    """
@app.route("/edit_seat_allocation/<int:id>")
def edit_seat_allocation(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT
            seat_allocations.id,
            seat_allocations.student_id,
            students.register_no,
            students.student_name,
            seat_allocations.hall_id,
            halls.hall_name,
            halls.room_no,
            seat_allocations.seat_no
        FROM seat_allocations
        JOIN students
        ON seat_allocations.student_id = students.id
        JOIN halls
        ON seat_allocations.hall_id = halls.id
        WHERE seat_allocations.id=%s
        """,
        (id,)
    )

    allocation = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM students ORDER BY register_no"
    )

    students = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM halls ORDER BY id"
    )

    halls = cursor.fetchall()

    cursor.close()

    if not allocation:
        return "Seat allocation not found."

    return render_template(
        "edit_seat_allocation.html",
        allocation=allocation,
        students=students,
        halls=halls
    )


@app.route("/update_seat_allocation/<int:id>", methods=["POST"])
def update_seat_allocation(id):

    student_id = request.form["student_id"]
    hall_id = request.form["hall_id"]
    seat_no = request.form["seat_no"].strip().upper()

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM seat_allocations
        WHERE student_id=%s
        AND id!=%s
        """,
        (student_id, id)
    )

    existing_student = cursor.fetchone()

    if existing_student:

        cursor.close()

        return """
        <div style="font-family:Arial;text-align:center;margin-top:100px;">
            <h2 style="color:red;">
                Student Already Allocated
            </h2>

            <p>
                This student already has another seat allocation.
            </p>

            <a href="/edit_seat_allocation/%s">
                Go Back
            </a>
        </div>
        """ % id

    cursor.execute(
        """
        SELECT id
        FROM seat_allocations
        WHERE hall_id=%s
        AND seat_no=%s
        AND id!=%s
        """,
        (hall_id, seat_no, id)
    )

    existing_seat = cursor.fetchone()

    if existing_seat:

        cursor.close()

        return """
        <div style="font-family:Arial;text-align:center;margin-top:100px;">
            <h2 style="color:red;">
                Seat Already Occupied
            </h2>

            <p>
                Seat %s is already occupied in this hall.
            </p>

            <a href="/edit_seat_allocation/%s">
                Go Back
            </a>
        </div>
        """ % (seat_no, id)

    cursor.execute(
        """
        UPDATE seat_allocations
        SET student_id=%s,
            hall_id=%s,
            seat_no=%s
        WHERE id=%s
        """,
        (
            student_id,
            hall_id,
            seat_no,
            id
        )
    )

    mysql.connection.commit()

    cursor.close()

    return seat_allocation()


@app.route("/delete_seat_allocation/<int:id>")
def delete_seat_allocation(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        DELETE FROM seat_allocations
        WHERE id=%s
        """,
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    return seat_allocation()
# =========================================================
# AI SEATING INTELLIGENCE
# =========================================================

@app.route("/ai_seating")
def ai_seating():

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM students"
    )

    total_students = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM halls"
    )

    total_halls = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(capacity), 0) FROM halls"
    )

    total_capacity = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM seat_allocations"
    )

    allocated_seats = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT
            id,
            hall_name,
            room_no,
            capacity
        FROM halls
        ORDER BY id
        """
    )

    halls_data = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            students.register_no,
            students.student_name,
            students.department,
            halls.hall_name,
            halls.room_no,
            seat_allocations.seat_no
        FROM seat_allocations
        JOIN students
        ON seat_allocations.student_id =
           students.id
        JOIN halls
        ON seat_allocations.hall_id =
           halls.id
        ORDER BY halls.id,
                 seat_allocations.id
        """
    )

    allocations = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            invigilators.name,
            invigilators.employee_id,
            halls.room_no
        FROM invigilator_assignments
        JOIN invigilators
        ON invigilator_assignments.invigilator_id =
           invigilators.id
        JOIN halls
        ON invigilator_assignments.hall_id =
           halls.id
        ORDER BY halls.id
        """
    )

    invigilators = cursor.fetchall()

    cursor.close()

    if total_capacity > 0:

        utilization = round(
            (total_students / total_capacity) * 100,
            1
        )

    else:

        utilization = 0

    if total_capacity == 0:

        status = "ACTION REQUIRED"

        recommendation = (
            "No examination halls are available. "
            "Please add halls before starting seating allocation."
        )

    elif total_students > total_capacity:

        status = "CAPACITY WARNING"

        recommendation = (
            "Student count exceeds available hall capacity. "
            "Additional hall capacity is required."
        )

    elif allocated_seats < total_students:

        status = "READY FOR ALLOCATION"

        recommendation = (
            "Students are available for automatic "
            "hall and seat allocation."
        )

    elif utilization >= 80:

        status = "HIGH UTILIZATION"

        recommendation = (
            "Hall capacity is highly utilized. "
            "Please monitor seating carefully."
        )

    else:

        status = "OPTIMAL"

        recommendation = (
            "Current hall capacity is suitable for "
            "smart examination seating."
        )

    if total_students > 0 and halls_data:

        capacities = [
            hall[3]
            for hall in halls_data
        ]

        capacities.sort(reverse=True)

        remaining = total_students

        halls_required = 0

        for capacity in capacities:

            remaining -= capacity

            halls_required += 1

            if remaining <= 0:
                break

    else:

        halls_required = 0

    return render_template(
        "ai_seating.html",
        total_students=total_students,
        total_halls=total_halls,
        total_capacity=total_capacity,
        allocated_seats=allocated_seats,
        utilization=utilization,
        halls_required=halls_required,
        status=status,
        recommendation=recommendation,
        halls=halls_data,
        allocations=allocations,
        invigilators=invigilators
    )


# =========================================================
# STUDENT SEAT SEARCH
# =========================================================

@app.route("/student_search", methods=["GET", "POST"])
def student_search():

    student = None
    error = None

    if request.method == "POST":

        register_no = request.form["register_no"].strip()

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT
                students.id,
                students.register_no,
                students.student_name,
                students.department,
                halls.hall_name,
                halls.room_no,
                seat_allocations.seat_no
            FROM seat_allocations
            JOIN students
            ON seat_allocations.student_id =
               students.id
            JOIN halls
            ON seat_allocations.hall_id =
               halls.id
            WHERE students.register_no=%s
            """,
            (register_no,)
        )

        student = cursor.fetchone()

        cursor.close()

        if not student:

            error = (
                "No seat allocation found "
                "for this Register Number."
            )

    return render_template(
        "student_search.html",
        student=student,
        error=error
    )


# =========================================================
# LIVE EXAM HALL VIEW
# =========================================================

@app.route("/hall_view")
def hall_view():

    hall_id = request.args.get("hall_id")

    cursor = mysql.connection.cursor()

    # Get all halls
    cursor.execute(
        "SELECT * FROM halls ORDER BY id"
    )

    halls = cursor.fetchall()

    selected_hall = None
    seats = []
    allocated_count = 0

    if hall_id:

        cursor.execute(
            "SELECT * FROM halls WHERE id=%s",
            (hall_id,)
        )

        selected_hall = cursor.fetchone()

        if selected_hall:

            capacity = selected_hall[3]

            cursor.execute(
                """
                SELECT
                    seat_allocations.seat_no,
                    students.register_no,
                    students.student_name,
                    students.department
                FROM seat_allocations
                JOIN students
                ON seat_allocations.student_id =
                   students.id
                WHERE seat_allocations.hall_id=%s
                ORDER BY seat_allocations.id
                """,
                (hall_id,)
            )

            allocations = cursor.fetchall()

            allocation_map = {}

            for allocation in allocations:

                allocation_map[allocation[0]] = {
                    "register_no": allocation[1],
                    "student_name": allocation[2],
                    "department": allocation[3]
                }

            # Create complete seat layout
            for number in range(1, capacity + 1):

                seat_no = "S" + str(number)

                if seat_no in allocation_map:

                    student_data = allocation_map[seat_no]

                    seats.append({
                        "seat_no": seat_no,
                        "register_no": student_data["register_no"],
                        "student_name": student_data["student_name"],
                        "department": student_data["department"]
                    })

                    allocated_count += 1

                else:

                    seats.append({
                        "seat_no": seat_no,
                        "register_no": "",
                        "student_name": "",
                        "department": ""
                    })

    cursor.close()

    return render_template(
        "hall_view.html",
        halls=halls,
        selected_hall=selected_hall,
        seats=seats,
        allocated_count=allocated_count
    )


# =========================================================
# QR HALL TICKET
# =========================================================
@app.route("/invigilator_qr/<int:invigilator_id>")
def invigilator_qr(invigilator_id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT
            invigilators.id,
            invigilators.name,
            invigilators.employee_id,
            invigilators.department,
            invigilators.phone,
            halls.hall_name,
            halls.room_no
        FROM invigilators
        LEFT JOIN invigilator_assignments
        ON invigilators.id = invigilator_assignments.invigilator_id
        LEFT JOIN halls
        ON invigilator_assignments.hall_id = halls.id
        WHERE invigilators.id=%s
        """,
        (invigilator_id,)
    )

    invigilator = cursor.fetchone()

    cursor.close()

    if not invigilator:
        return "Invigilator not found."

    qr_data = (
        "INVIGILATOR VERIFICATION\n"
        f"Name: {invigilator[1]}\n"
        f"Employee ID: {invigilator[2]}\n"
        f"Department: {invigilator[3]}\n"
        f"Phone: {invigilator[4]}\n"
        f"Hall: {invigilator[5]}\n"
        f"Room No: {invigilator[6]}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    qr_buffer = io.BytesIO()

    qr_image.save(
        qr_buffer,
        format="PNG"
    )

    qr_buffer.seek(0)

    qr_base64 = base64.b64encode(
        qr_buffer.getvalue()
    ).decode("utf-8")

    qr_url = "data:image/png;base64," + qr_base64

    return render_template(
        "invigilator_qr.html",
        invigilator=invigilator,
        qr_url=qr_url
    )

@app.route("/hall_ticket/<int:student_id>")
def hall_ticket(student_id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT
            students.id,
            students.register_no,
            students.student_name,
            students.department,
            students.year,
            students.exam_name,
            halls.hall_name,
            halls.room_no,
            halls.capacity,
            seat_allocations.seat_no
        FROM students
        LEFT JOIN seat_allocations
        ON students.id = seat_allocations.student_id
        LEFT JOIN halls
        ON seat_allocations.hall_id = halls.id
        WHERE students.id=%s
        """,
        (student_id,)
    )

    student = cursor.fetchone()

    cursor.close()

    if not student:
        return "Student not found."

    if not student[9]:
        return """
        <div style="font-family:Arial;text-align:center;margin-top:100px;">
            <h2>No seat allocated for this student.</h2>
            <p>Please allocate seats first.</p>
            <a href="/seat_allocation">Go to Seat Allocation</a>
        </div>
        """

    # =====================================================
    # QR CODE DATA
    # =====================================================

    qr_data = (
        "EXAMINATION HALL TICKET\n"
        f"Register No: {student[1]}\n"
        f"Student Name: {student[2]}\n"
        f"Department: {student[3]}\n"
        f"Year: {student[4]}\n"
        f"Exam: {student[5]}\n"
        f"Hall: {student[6]}\n"
        f"Room No: {student[7]}\n"
        f"Seat No: {student[9]}"
    )

    # =====================================================
    # CREATE QR CODE IN MEMORY
    # =====================================================

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )

    qr.add_data(qr_data)

    qr.make(
        fit=True
    )

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    # =====================================================
    # CONVERT QR IMAGE TO BASE64
    # =====================================================

    qr_buffer = io.BytesIO()

    qr_image.save(
        qr_buffer,
        format="PNG"
    )

    qr_buffer.seek(0)

    qr_base64 = base64.b64encode(
        qr_buffer.getvalue()
    ).decode("utf-8")

    # =====================================================
    # QR IMAGE DATA URL
    # =====================================================

    qr_url = (
        "data:image/png;base64,"
        + qr_base64
    )

    return render_template(
        "hall_ticket.html",
        student=student,
        qr_url=qr_url
    )
@app.route("/reports")
def reports():

    cursor = mysql.connection.cursor()

    # =====================================================
    # TOTAL STUDENTS
    # =====================================================

    cursor.execute(
        "SELECT COUNT(*) FROM students"
    )

    total_students = cursor.fetchone()[0]


    # =====================================================
    # TOTAL HALLS
    # =====================================================

    cursor.execute(
        "SELECT COUNT(*) FROM halls"
    )

    total_halls = cursor.fetchone()[0]


    # =====================================================
    # TOTAL HALL CAPACITY
    # =====================================================

    cursor.execute(
        "SELECT COALESCE(SUM(capacity), 0) FROM halls"
    )

    total_capacity = cursor.fetchone()[0]


    # =====================================================
    # ALLOCATED SEATS
    # =====================================================

    cursor.execute(
        "SELECT COUNT(*) FROM seat_allocations"
    )

    allocated_seats = cursor.fetchone()[0]


    # =====================================================
    # EMPTY SEATS
    # =====================================================

    empty_seats = total_capacity - allocated_seats


    # =====================================================
    # TOTAL INVIGILATORS
    # =====================================================

    cursor.execute(
        "SELECT COUNT(*) FROM invigilators"
    )

    total_invigilators = cursor.fetchone()[0]


    # =====================================================
    # HALL-WISE REPORT
    # =====================================================

    cursor.execute(
        """
        SELECT
            halls.hall_name,
            halls.room_no,
            halls.capacity,
            COUNT(seat_allocations.id) AS allocated
        FROM halls
        LEFT JOIN seat_allocations
        ON halls.id = seat_allocations.hall_id
        GROUP BY
            halls.id,
            halls.hall_name,
            halls.room_no,
            halls.capacity
        ORDER BY halls.id
        """
    )

    hall_reports = cursor.fetchall()


    # =====================================================
    # STUDENT-WISE ALLOCATION REPORT
    # =====================================================

    cursor.execute(
        """
        SELECT
            students.register_no,
            students.student_name,
            students.department,
            students.year,
            halls.hall_name,
            halls.room_no,
            seat_allocations.seat_no
        FROM seat_allocations
        JOIN students
        ON seat_allocations.student_id = students.id
        JOIN halls
        ON seat_allocations.hall_id = halls.id
        ORDER BY halls.id,
                 seat_allocations.id
        """
    )

    student_reports = cursor.fetchall()


    cursor.close()


    # =====================================================
    # SEND DATA TO REPORTS PAGE
    # =====================================================

    return render_template(
        "reports.html",

        total_students=total_students,

        total_halls=total_halls,

        total_capacity=total_capacity,

        allocated_seats=allocated_seats,

        empty_seats=empty_seats,

        total_invigilators=total_invigilators,

        hall_reports=hall_reports,

        student_reports=student_reports
    )# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
