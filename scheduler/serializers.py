from rest_framework import serializers
from .models import (
    AcademicTerm, Room, TimeSlot, Teacher, Course, 
    Section, TeacherCourseQualifications, TimeTableEntry
)

class AcademicTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicTerm
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class SectionSerializer(serializers.ModelSerializer):
    # We can nest the Room data so the engine easily sees the Phase 1 Home Room
    room_details = RoomSerializer(source='room', read_only=True)
    
    class Meta:
        model = Section
        fields = '__all__'

class TeacherQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherCourseQualifications
        fields = '__all__'

class TimeTableEntrySerializer(serializers.ModelSerializer):
    # This will be used to send the final, beautiful schedule to the frontend
    section_name = serializers.CharField(source='section.name', read_only=True)
    course_name = serializers.CharField(source='course.course_code', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    day = serializers.CharField(source='time_slot.day_of_week', read_only=True)
    start_time = serializers.TimeField(source='time_slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='time_slot.end_time', read_only=True)

    class Meta:
        model = TimeTableEntry
        fields = [
            'id', 'section_name', 'course_name', 'teacher_name', 
            'room_name', 'day', 'start_time', 'end_time'
        ]