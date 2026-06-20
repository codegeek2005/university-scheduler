from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from scheduler.forms import CustomRegistrationForm
from scheduler.models import Section, Teacher, TimeTableEntry, UserProfile

# ==========================================
# SECURITY ROLE DEFINITIONS
# ==========================================
def is_coordinator(user):
    return user.is_staff or user.groups.filter(name='Coordinator').exists()

def is_faculty(user):
    return user.groups.filter(name='Faculty').exists() or is_coordinator(user)

def is_student(user):
    return user.groups.filter(name='Student').exists() or is_coordinator(user)

# ==========================================
# HELPER: The Matrix Builder
# ==========================================
def build_matrix(entries):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    matrix = {day: {slot: None for slot in range(9)} for day in days}
    
    for entry in entries:
        try:
            # Corrected: Accessing through the time_slot ForeignKey
            day = entry.time_slot.day_of_week
            slot = entry.time_slot.slot_index
            if day in matrix and slot in matrix[day]:
                matrix[day][slot] = entry
        except AttributeError:
            continue
    return matrix

# ==========================================
# 1. AUTHENTICATION VIEWS
# ==========================================
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data.get('role')
            
            selected_section = form.cleaned_data.get('section')
            selected_teacher = form.cleaned_data.get('teacher')
            
            # Fallback: ensure POSTed IDs are converted to model instances if needed
            if role == 'student' and selected_section is None:
                section_id = request.POST.get('section')
                if section_id:
                    selected_section = Section.objects.filter(pk=section_id).first()

            if role == 'faculty' and selected_teacher is None:
                teacher_id = request.POST.get('teacher')
                if teacher_id:
                    selected_teacher = Teacher.objects.filter(pk=teacher_id).first()

            if role == 'student' and selected_section is None:
                form.add_error('section', 'Students must select a section.')
            if role == 'faculty' and selected_teacher is None:
                form.add_error('teacher', 'Faculty must select their profile.')

            if form.errors:
                return render(request, 'registration/signup.html', {'form': form})

            user = form.save()
            profile = UserProfile.objects.create(
                user=user,
                role=role,
                section=selected_section if role == 'student' else None,
                teacher=selected_teacher if role == 'faculty' else None
            )

            print(f"DEBUG: Saved User {user.username} as {role}. Section: {selected_section}, Teacher: {selected_teacher}")
            
            group_name = 'Student' if role == 'student' else 'Faculty'
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            
            login(request, user)
            return redirect('home')
    else:
        form = CustomRegistrationForm()
        
    return render(request, 'registration/signup.html', {'form': form})

# ==========================================
# 2. DASHBOARD TRAFFIC DIRECTOR
# ==========================================
def home(request):
    if request.user.is_authenticated:
        if is_coordinator(request.user):
            return redirect('coordinator_dashboard')
        elif is_faculty(request.user):
            return redirect('teacher_dashboard')
        elif is_student(request.user):
            return redirect('student_dashboard')
    return render(request, 'scheduler/home.html')

# ==========================================
# 3. ROLE-BASED DASHBOARDS
# ==========================================
@login_required(login_url='/login/')
@user_passes_test(is_student, login_url='/login/')
def student_dashboard(request):
    try:
        # Check if profile exists
        profile = request.user.userprofile
        my_section = profile.section
        print(f"DEBUG: User {request.user.username} - Section: {my_section}")
        
        if my_section:
            entries = TimeTableEntry.objects.filter(section=my_section).select_related('course', 'teacher', 'room', 'time_slot')
            matrix = build_matrix(entries)
            print(f"DEBUG: Found {entries.count()} entries.")
        else:
            matrix = None
            
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        my_section, matrix = None, None

    return render(request, 'scheduler/student_dashboard.html', {
        'my_section': my_section, 'matrix': matrix,
        'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], 'slots': range(9)
    })


@login_required(login_url='/login/')
@user_passes_test(is_faculty, login_url='/login/')
def teacher_dashboard(request):
    try:
        # Get the teacher linked to the user's profile
        my_teacher = request.user.userprofile.teacher
        
        # Query entries where this teacher is assigned
        entries = TimeTableEntry.objects.filter(teacher=my_teacher).select_related(
            'course', 'section', 'room', 'time_slot'
        )
        matrix = build_matrix(entries)
    except Exception as e:
        print(f"DEBUG: Teacher Dashboard Error: {e}")
        my_teacher, matrix = None, None

    return render(request, 'scheduler/teacher_dashboard.html', {
        'my_teacher': my_teacher, 
        'matrix': matrix,
        'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], 
        'slots': range(9)
    })

@login_required(login_url='/login/')
@user_passes_test(is_coordinator, login_url='/login/')
def coordinator_dashboard(request):
    return render(request, 'scheduler/coordinator_dashboard.html')

# ==========================================
# 4. MASTER TIMETABLE (Global View)
# ==========================================

@login_required(login_url='/login/')
def master_timetable(request):
    sections = Section.objects.all().order_by('name')
    selected_section_id = request.GET.get('section')
    
    print(f"DEBUG: Searching for Section ID: {selected_section_id}")
    
    matrix = None
    selected_section = None

    if selected_section_id:
        try:
            selected_section = Section.objects.get(pk=selected_section_id)
            print(f"DEBUG: Found Section: {selected_section.name}")
            
            entries = TimeTableEntry.objects.filter(section=selected_section).select_related('course', 'teacher', 'room', 'time_slot')
            matrix = build_matrix(entries)
            print(f"DEBUG: Matrix generated with {len(entries)} entries")
            
        except Section.DoesNotExist:
            print("DEBUG: Section ID does not exist in Database!")
            matrix = None

    context = {
            'sections': sections, 
            'selected_section': selected_section, 
            'matrix': matrix,
            'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat',], 
            'slots': range(9)
        }
        
    return render(request, 'scheduler/timetable_view.html', context)