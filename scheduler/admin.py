from django.contrib import admin
from .models import (
    AcademicTerm, Room, TimeSlot, Teacher, Course, 
    Section, TeacherCourseQualifications, TimeTableEntry
)

@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_semester')
    search_fields = ('name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    search_fields = ('name', 'department')
    list_filter = ('department',)

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'slot_index', 'start_time', 'end_time')
    list_filter = ('day_of_week',)
    ordering = ('day_of_week', 'slot_index')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'max_courses')
    search_fields = ('name', 'department')
    list_filter = ('department',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'semester', 'lectures_per_week')
    search_fields = ('course_code', 'title')
    list_filter = ('semester', 'lectures_per_week')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'term_id', 'department', 'room')
    search_fields = ('name', 'department')
    list_filter = ('term_id', 'department')

@admin.register(TeacherCourseQualifications)
class TeacherCourseQualificationsAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'course')
    search_fields = ('teacher__name', 'course__course_code', 'course__title')
    list_filter = ('teacher', 'course')

@admin.register(TimeTableEntry)
class TimeTableEntryAdmin(admin.ModelAdmin):
    list_display = ('section', 'course', 'teacher', 'room', 'time_slot')
    list_filter = ('room', 'teacher', 'section')
    search_fields = ('section__name', 'course__course_code', 'teacher__name', 'room__name')