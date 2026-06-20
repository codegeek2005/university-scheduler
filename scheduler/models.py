from django.db import models
from django.contrib.auth.models import User

# ==========================================
# CORE LOOKUP TABLES
# ==========================================

class AcademicTerm(models.Model):
    name = models.CharField(max_length=100)
    # The ERD marks this as unique, ensuring we only have one 'Semester 1', 'Semester 2', etc. per term definition
    current_semester = models.IntegerField(unique=True) 
    
    def __str__(self):
        return f"{self.name} - Sem {self.current_semester}"

class Room(models.Model):
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name} ({self.department})"

class TimeSlot(models.Model):
    DAY_CHOICES = [
        ('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday')
    ]
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    slot_index = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        # Prevents creating duplicate slots for the exact same day and time index
        constraints = [
            models.UniqueConstraint(fields=['day_of_week', 'slot_index'], name='unique_day_slot')
        ]

    def __str__(self):
        return f"{self.day_of_week} - Slot {self.slot_index} ({self.start_time.strftime('%H:%M')})"

# ==========================================
# ENTITIES
# ==========================================

class Teacher(models.Model):
    name = models.CharField(max_length=100)
    max_courses = models.IntegerField()
    department = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    semester = models.IntegerField()
    lectures_per_week = models.IntegerField()
    
    def __str__(self):
        return f"{self.course_code} - {self.title}"

class Section(models.Model):
    name = models.CharField(max_length=100)
    term_id = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE, related_name='sections')
    department = models.CharField(max_length=100)
    # The Phase 1 Home Room!
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_sections')
    
    def __str__(self):
        return self.name

# ==========================================
# JUNCTION & MASTER TABLES
# ==========================================

class TeacherCourseQualifications(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='qualifications')

    class Meta:
        # A teacher shouldn't be qualified for the exact same course twice
        constraints = [
            models.UniqueConstraint(fields=['teacher', 'course'], name='unique_teacher_course')
        ]

    def __str__(self):
        return f"{self.teacher.name} -> {self.course.course_code}"

class TimeTableEntry(models.Model):
    """The central resting place for the OR-Tools optimized output."""
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)

    class Meta:
        # THE ULTIMATE DATABASE FAILSAFES
        constraints = [
            # 1. A room can only hold one class at a specific time slot
            models.UniqueConstraint(fields=['room', 'time_slot'], name='unique_room_timeslot'),
            
            # 2. A teacher can only teach one class at a specific time slot
            models.UniqueConstraint(fields=['teacher', 'time_slot'], name='unique_teacher_timeslot'),
            
            # 3. A section can only attend one class at a specific time slot
            models.UniqueConstraint(fields=['section', 'time_slot'], name='unique_section_timeslot')
        ]

    def __str__(self):
        return f"{self.section.name} | {self.course.course_code} | {self.time_slot}"
    



class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('coordinator', 'Coordinator')
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    # If Student, link to their Section
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    
    # If Faculty, link to their Teacher record
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"