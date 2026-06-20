from ortools.sat.python import cp_model
import time

def run_phase_2(input_data):
    print("Initializing Phase 2: Teacher & Course Matching...")
    start_time = time.time()
    
    phase1_slots = input_data["phase1_slots"]
    curriculum = input_data["curriculum"]
    teachers = input_data["teachers"]
    qualifications = input_data["qualifications"]
    
    # 1. Parse Inputs & Build Active Lookup
    active_lookup = {}
    for entry in phase1_slots:
        s_id = entry["section_id"]
        active_lookup.setdefault(s_id, []).append((entry["day"], entry["slot_index"]))
        
    days = list(set(entry["day"] for entry in phase1_slots))
    slots_per_day = max(entry["slot_index"] for entry in phase1_slots) + 1
    
    model = cp_model.CpModel()
    
    teacher_assigned = {}
    course_slot = {}
    
    # 2. Variable Initialization
    for req in curriculum:
        s_id = req["section_id"]
        c_id = req["course_id"]
        
        qualified_teachers = [q["teacher_id"] for q in qualifications if q["course_id"] == c_id]
        
        # DIAGNOSTIC GUARDRAIL: Catch missing data instantly
        if not qualified_teachers:
            print(f"CRITICAL ERROR: Course ID {c_id} has NO qualified teachers in the database!")
            return []

        for t_id in qualified_teachers:
            teacher_assigned[t_id, s_id, c_id] = model.NewBoolVar(f'assign_{t_id}_{s_id}_{c_id}')
            
        for d in days:
            for slot in range(slots_per_day):
                course_slot[s_id, c_id, d, slot] = model.NewBoolVar(f'c_slot_{s_id}_{c_id}_{d}_{slot}')

    # 3. CONSTRAINTS
    for req in curriculum:
        s_id = req["section_id"]
        c_id = req["course_id"]
        qualified_teachers = [q["teacher_id"] for q in qualifications if q["course_id"] == c_id]
        
        # A. Exactly ONE teacher must be assigned to this Section-Course
        model.AddExactlyOne(teacher_assigned[t, s_id, c_id] for t in qualified_teachers)
        
        # B. The sum of slots assigned to this course must equal the lectures quota
        model.Add(
            sum(course_slot[s_id, c_id, d, slot] for d in days for slot in range(slots_per_day)) 
            == req["lectures_per_week"]
        )

    # C. Teacher Workload Limit
    for t in teachers:
        t_id = t["teacher_id"]
        possible_assignments = [
            teacher_assigned[t_id, req["section_id"], req["course_id"]] 
            for req in curriculum 
            if (t_id, req["section_id"], req["course_id"]) in teacher_assigned
        ]
        if possible_assignments:
            model.Add(sum(possible_assignments) <= t["max_courses"])

    # D. Phase 1 Boundary Enforcement
    for s_id in active_lookup.keys():
        s_reqs = [req for req in curriculum if req["section_id"] == s_id]
        
        for d in days:
            for slot in range(slots_per_day):
                if (d, slot) not in active_lookup[s_id]:
                    # If Phase 1 did NOT activate this slot, freeze it
                    for req in s_reqs:
                        model.Add(course_slot[s_id, req["course_id"], d, slot] == 0)
                else:
                    # If Phase 1 DID activate this slot, EXACTLY ONE course must be placed here
                    model.AddExactlyOne(course_slot[s_id, req["course_id"], d, slot] for req in s_reqs)

    # E. Teacher Clash Prevention (Optimized via MinEquality)
    for t in teachers:
        t_id = t["teacher_id"]
        for d in days:
            for slot in range(slots_per_day):
                active_events = []
                for req in curriculum:
                    s_id = req["section_id"]
                    c_id = req["course_id"]
                    
                    if (t_id, s_id, c_id) in teacher_assigned:
                        t_event = model.NewBoolVar(f'ev_{t_id}_{s_id}_{c_id}_{d}_{slot}')
                        
                        # C++ OPTIMIZATION: t_event is 1 ONLY IF (teacher assigned AND course is in this slot)
                        model.AddMinEquality(t_event, [teacher_assigned[t_id, s_id, c_id], course_slot[s_id, c_id, d, slot]])
                        active_events.append(t_event)
                        
                if active_events:
                    model.AddAtMostOne(active_events)

    # 4. Execute Solver
    solver = cp_model.CpSolver()
    
    # Matching the exact safety limits we applied to Phase 1
    solver.parameters.max_time_in_seconds = 180
    solver.parameters.log_search_progress = True
    solver.parameters.symmetry_level = 0 
    solver.parameters.num_search_workers = 4 
    
    print("\nFIRING PHASE 2 ENGINE...")
    status = solver.Solve(model)
    
    # 5. Extract Output
    final_timetable = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for req in curriculum:
            s_id = req["section_id"]
            c_id = req["course_id"]
            qualified_teachers = [q["teacher_id"] for q in qualifications if q["course_id"] == c_id]
            
            assigned_t_id = None
            for t_id in qualified_teachers:
                if solver.Value(teacher_assigned[t_id, s_id, c_id]) == 1:
                    assigned_t_id = t_id
                    break
            
            for d in days:
                for slot in range(slots_per_day):
                    if solver.Value(course_slot[s_id, c_id, d, slot]) == 1:
                        room_id = next(entry["room_id"] for entry in phase1_slots if entry["section_id"] == s_id and entry["day"] == d and entry["slot_index"] == slot)
                        
                        final_timetable.append({
                            "section_id": s_id,
                            "course_id": c_id,
                            "teacher_id": assigned_t_id,
                            "room_id": room_id,
                            "day": d,
                            "slot_index": slot
                        })
        print(f"Phase 2 Solved Successfully in {time.time() - start_time:.2f} seconds!")
        return final_timetable
    else:
        print("Phase 2 Failed: Infeasible. The logic matrix locked up.")
        return []