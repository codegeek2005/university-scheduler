import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from scheduler.models import AcademicTerm, Room, Teacher, Course, Section, TeacherCourseQualifications, TimeSlot, TimeTableEntry

class Command(BaseCommand):
    help = 'Wipes the database and seeds a minimal, highly optimized 10-room ecosystem for testing.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🧹 Wiping all previous database records..."))
        
        # 0. WIPE ALL DATA IN REVERSE DEPENDENCY ORDER
        TimeTableEntry.objects.all().delete()
        TeacherCourseQualifications.objects.all().delete()
        Section.objects.all().delete()
        Course.objects.all().delete()
        Teacher.objects.all().delete()
        Room.objects.all().delete()
        AcademicTerm.objects.all().delete()
        TimeSlot.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS("✅ Database wiped cleanly. Initiating rebuild..."))

        # ==========================================
        # 1. ACADEMIC TERMS (Only Semesters 1-4)
        # ==========================================
        term_mapping = {
            1: "Spring 26",
            2: "Fall 25",
            3: "Spring 25",
            4: "Fall 24"
        }
        
        terms = {}
        for sem, term_name in term_mapping.items():
            term = AcademicTerm.objects.create(current_semester=sem, name=term_name)
            terms[sem] = term
            
        self.stdout.write(self.style.SUCCESS("✅ Created 4 Academic Terms."))

        # ==========================================
        # 2. ROOMS (Exactly 10 Rooms)
        # ==========================================
        for r in range(1, 11):
            Room.objects.create(name=f"1.{r:02d}", department="CS & IT")
            
        self.stdout.write(self.style.SUCCESS("✅ Created 10 Rooms."))

        # ==========================================
        # 3. SECTIONS (5 per semester = 20 total)
        # ==========================================
        section_names = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']
        for sem, term in terms.items():
            for sec_name in section_names:
                Section.objects.create(
                    name=f"CS-{sem}{sec_name[0]}", 
                    term_id=term,
                    department='Computer Science'
                )
                
        self.stdout.write(self.style.SUCCESS("✅ Created 20 Sections."))

        # ==========================================
        # 4. COURSES (Strictly mapped by integer semester)
        # ==========================================
        course_data = [
            # Sem 1
            ('CS101', 'Intro to Computing', 1), ('MA101', 'Calculus I', 1), ('EN101', 'English Composition', 1),
            ('PH101', 'Applied Physics', 1), ('IS101', 'Islamic Studies', 1),
            # Sem 2
            ('CS102', 'Programming Fundamentals', 2), ('CS103', 'Digital Logic Design', 2),
            ('MA102', 'Linear Algebra', 2), ('EN102', 'Communication Skills', 2), ('EE101', 'Basic Electronics', 2),
            # Sem 3
            ('CS201', 'Data Structures & Algorithms', 3), ('CS202', 'Discrete Structures', 3),
            ('SE201', 'Software Engineering', 3), ('CS203', 'Database Systems', 3), ('ST201', 'Statistics', 3),
            # Sem 4
            ('SE202', 'Object Oriented Software Eng', 4), ('CS204', 'Web Engineering', 4),
            ('CS205', 'Operating Systems', 4), ('CS206', 'Computer Networks', 4), ('MA201', 'Differential Equations', 4),
        ]
        
        courses = []
        for code, title, sem in course_data:
            course = Course.objects.create(
                course_code=code,
                title=title,
                semester=sem,  # Utilizing your decoupled integer field
                lectures_per_week=3 # 3 slots needed per course
            )
            courses.append(course)
            
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(course_data)} Core Courses."))

        # ==========================================
        # 5. TEACHERS & QUALIFICATIONS (The Minimum Safe Amount)
        # ==========================================
        # 20 sections * 5 courses = 100 course instances to teach. 
        # At max 5 courses per teacher, we need exactly 20. We make 25 to give the solver a little flexibility.
        teachers = []
        for i in range(1, 26):
            teacher = Teacher.objects.create(name=f"Prof. Faculty {i:02d}", department="Computer Science", max_courses=5)
            teachers.append(teacher)

        # Qualify exactly 4 random teachers for every single course
        for course in courses:
            assigned_teachers = random.sample(teachers, 4)
            for teacher in assigned_teachers:
                TeacherCourseQualifications.objects.create(teacher=teacher, course=course)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(teachers)} Teachers and mapped their qualifications."))

        # ==========================================
        # 6. TIMESLOTS (5 days, 9 slots, 1 hr each)
        # ==========================================
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        total_slots = 9
        start_hour = 8 # 08:00 AM
        
        current_dt = datetime(2000, 1, 1, start_hour, 0)
        slot_times = {}

        for index in range(total_slots):
            end_dt = current_dt + timedelta(minutes=60) # 1 hour exactly
            slot_times[index] = (current_dt.time(), end_dt.time())
            current_dt = end_dt

        for day in days:
            for slot_index, (start_t, end_t) in slot_times.items():
                TimeSlot.objects.create(
                    day_of_week=day,
                    slot_index=slot_index,
                    start_time=start_t,
                    end_time=end_t
                )

        self.stdout.write(self.style.SUCCESS("✅ Created 45 TimeSlots (5 Days x 9 One-Hour Slots)."))
        self.stdout.write(self.style.WARNING("🎯 ECOSYSTEM REBUILD COMPLETE. Ready for testing!"))