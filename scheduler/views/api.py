from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from scheduler.models import (
    AcademicTerm, Room, TimeSlot, Teacher, Course, 
    Section, TeacherCourseQualifications, TimeTableEntry
)

# Import your actual OR-Tools engine scripts here
# Assuming your functions are named run_phase_1 and run_phase_2
from scheduler.engine.scheduler_phase1 import run_phase_1
from scheduler.engine.scheduler_phase2 import run_phase_2

class GenerateScheduleView(APIView):
    """
    The Master Orchestrator API Endpoint.
    Extracts DB data -> Formats for OR-Tools -> Runs Solvers -> Saves Results.
    """
    
    @transaction.atomic
    def post(self, request):
        try:
            # ==========================================
            # PHASE 0: WIPE THE OLD SCHEDULE
            # ==========================================
            # Clear existing timetable entries to avoid unique constraint crashes
            TimeTableEntry.objects.all().delete()

            # ==========================================
            # PHASE 1: EXTRACT & TRANSLATE DATABASE DATA
            # ==========================================
            
            # 1. Rooms
            rooms = [{"room_id": r.id, "name": r.name} for r in Room.objects.all()]
            
            # 2. Sections
            sections = [{"section_id": s.id, "name": s.name, "term_id": s.term_id_id} for s in Section.objects.all()]
            
            # 3. Teachers
            teachers = [{"teacher_id": t.id, "max_courses": t.max_courses} for t in Teacher.objects.all()]
            
            # 4. Qualifications
            qualifications = []
            for qual in TeacherCourseQualifications.objects.all():
                qualifications.append({
                    "teacher_id": qual.teacher_id,
                    "course_id": qual.course_id
                })

            # 5. Dynamic Curriculum Mapping
            # We map courses to sections based on the section's current term
          # 5. Dynamic Curriculum Mapping
            # We map courses to sections based on the section's current term integer
            curriculum = []
            for sec in Section.objects.all():
                # Extract the integer (1-8) from the cohort's current term
                current_sem_integer = sec.term_id.current_semester 
                
                # Fetch courses matching that integer
                term_courses = Course.objects.filter(semester=current_sem_integer) 
                
                for course in term_courses:
                    curriculum.append({
                        "section_id": sec.id,
                        "course_id": course.id,
                        "lectures_per_week": course.lectures_per_week
                    })

            # Calculate required slots per section for Phase 1
            section_slot_requirements = {}
            for req in curriculum:
                sec_id = req["section_id"]
                section_slot_requirements[sec_id] = section_slot_requirements.get(sec_id, 0) + req["lectures_per_week"]

            phase1_input_sections = [
                {"section_id": s_id, "total_slots_needed": req_slots} 
                for s_id, req_slots in section_slot_requirements.items()
            ]

           # ==========================================
            # PHASE 2: FIRE THE ENGINES
            # ==========================================
            
            # 1. Construct the master payload for Phase 1
            phase1_input_data = {
                "config": {
                    "days": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                    "slots_per_day": 7,
                },
                "sections": phase1_input_sections,
                "rooms": rooms
            }


            #print statements for deubugging
            print("--- ORCHESTRATOR CHECK ---")
            print(f"Sections Count: {len(phase1_input_data['sections'])}")
            print(f"Rooms Count: {len(phase1_input_data['rooms'])}")
            print("FIRING PHASE 1 ENGINE NOW...")
            
            # Run Phase 1 (Boundary Optimization & Home Rooms)
            phase1_output = run_phase_1(phase1_input_data)
            
            if not phase1_output:
                return Response({"error": "Phase 1 Failed: Infeasible Layout"}, status=status.HTTP_400_BAD_REQUEST)

            # Run Phase 2 (Teacher & Course Matching)
            phase2_input = {
                "phase1_slots": phase1_output,
                "curriculum": curriculum,
                "teachers": teachers,
                "qualifications": qualifications
            }
            
            final_timetable = run_phase_2(phase2_input)
            
            if not final_timetable:
                return Response({"error": "Phase 2 Failed: Could not match teachers without clashes"}, status=status.HTTP_400_BAD_REQUEST)
            # ==========================================
            # PHASE 3: SAVE TO DATABASE
            # ==========================================
            
            # Pre-fetch TimeSlots to avoid hitting the DB hundreds of times in the loop
            timeslot_map = { 
                (ts.day_of_week, ts.slot_index): ts 
                for ts in TimeSlot.objects.all() 
            }

            entries_to_create = []
            for entry in final_timetable:
                ts_obj = timeslot_map.get((entry['day'], entry['slot_index']))
                
                if ts_obj:
                    entries_to_create.append(
                        TimeTableEntry(
                            section_id=entry['section_id'],
                            course_id=entry['course_id'],
                            teacher_id=entry['teacher_id'],
                            room_id=entry['room_id'],
                            time_slot=ts_obj
                        )
                    )

            # Bulk create is massively faster than saving one by one
            TimeTableEntry.objects.bulk_create(entries_to_create)

            return Response({
                "message": "University Schedule Generated Successfully!",
                "total_entries_created": len(entries_to_create)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



        