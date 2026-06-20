from ortools.sat.python import cp_model
import time

def run_phase_1(input_data):
    print("Initializing Phase 1: Home Room & Canvas Generator...")
    start_time = time.time()
    
    config = input_data["config"]
    days = config["days"]
    slots_per_day = config["slots_per_day"]
    lunch_slot = config.get("lunch_slot", None)
    
    sections = input_data["sections"]
    rooms = input_data["rooms"] 
    
    model = cp_model.CpModel()
    
    # --- VARIABLES ---
    is_active = {}
    day_active = {}
    section_room = {}           # Tracks which room is the Home Room for a section
    active_in_room = {}         # Tracks activity in a specific room
    
    variance_penalties = []
    footprint_penalties = []
    
    # 1. Assign Home Rooms
    for sec in sections:
        s_id = sec["section_id"]
        for r in rooms:
            r_id = r["room_id"]
            section_room[s_id, r_id] = model.NewBoolVar(f'sec_room_{s_id}_{r_id}')
        
        # HARD CONSTRAINT: Each section gets exactly ONE home room
        model.AddExactlyOne(section_room[s_id, r["room_id"]] for r in rooms)

    # 2. Section Variables & Constraints
    for sec in sections:
        s_id = sec["section_id"]
        target_slots = sec["total_slots_needed"]
        
        for d in days:
            day_active[s_id, d] = model.NewBoolVar(f'day_active_{s_id}_{d}')
            
            for slot in range(slots_per_day):
                is_active[s_id, d, slot] = model.NewBoolVar(f'active_{s_id}_{d}_{slot}')
                
                # Link general activity to room-specific activity
                for r in rooms:
                    r_id = r["room_id"]
                    active_in_room[s_id, r_id, d, slot] = model.NewBoolVar(f'act_rm_{s_id}_{r_id}_{d}_{slot}')
                    
                    # If section is NOT in this home room, they cannot be active in it
                    model.Add(active_in_room[s_id, r_id, d, slot] == 0).OnlyEnforceIf(section_room[s_id, r_id].Not())
                    
                    # If they ARE in this home room, active_in_room mirrors is_active
                    model.Add(active_in_room[s_id, r_id, d, slot] == is_active[s_id, d, slot]).OnlyEnforceIf(section_room[s_id, r_id])

                # Lunch constraint
                if slot == lunch_slot:
                    model.Add(is_active[s_id, d, slot] == 0)

        # HARD CONSTRAINT: Target Quota
        model.Add(sum(is_active[s_id, d, slot] for d in days for slot in range(slots_per_day)) == target_slots)
        
        # HARD CONSTRAINT: 3 to 5 Active Days
        model.Add(sum(day_active[s_id, d] for d in days) >= 3)
        model.Add(sum(day_active[s_id, d] for d in days) <= 5)
        
        # Daily Logic (Consecutive classes)
        for d in days:
            lec_per_day = sum(is_active[s_id, d, slot] for slot in range(slots_per_day))
            model.Add(lec_per_day >= 1).OnlyEnforceIf(day_active[s_id, d])
            model.Add(lec_per_day == 0).OnlyEnforceIf(day_active[s_id, d].Not())
            
            padded_slots = [0] + [is_active[s_id, d, slot] for slot in range(slots_per_day)] + [0]
            transitions = []
            for i in range(1, len(padded_slots)):
                trans = model.NewBoolVar(f'trans_{s_id}_{d}_{i}')
                model.Add(trans >= padded_slots[i] - padded_slots[i-1])
                transitions.append(trans)
            model.Add(sum(transitions) <= 1)
            
        # SOFT CONSTRAINTS: Workload Balancing (Variance)
        max_lec = model.NewIntVar(0, slots_per_day, f'max_lec_{s_id}')
        min_lec = model.NewIntVar(0, slots_per_day, f'min_lec_{s_id}')
        
        for d in days:
            lec_per_day = sum(is_active[s_id, d, slot] for slot in range(slots_per_day))
            model.Add(max_lec >= lec_per_day)
            model.Add(min_lec <= lec_per_day).OnlyEnforceIf(day_active[s_id, d])
            
        variance = model.NewIntVar(0, slots_per_day, f'var_{s_id}')
        model.Add(variance == max_lec - min_lec)
        variance_penalties.append(variance)
        
        # SOFT CONSTRAINTS: Weekly Footprint (Consistency)
        for slot in range(slots_per_day):
            ever_used = model.NewBoolVar(f'ever_used_{s_id}_{slot}')
            model.AddMaxEquality(ever_used, [is_active[s_id, d, slot] for d in days])
            footprint_penalties.append(ever_used)

    # ==================================================
    # 3. NEW HARD CONSTRAINTS: Room Clashes & Capacity
    # ==================================================
    
    # Calculate absolute weekly capacity of any given room
    # (e.g., 5 days * 6 usable slots = 30 maximum slots per week)
    usable_daily_slots = slots_per_day - (1 if lunch_slot is not None else 0)
    weekly_room_capacity = len(days) * usable_daily_slots

    for r in rooms:
        r_id = r["room_id"]
        
        # A. THE REDUNDANT CAPACITY CONSTRAINT (Prunes search tree instantly)
        # The sum of required slots for all sections assigned to this room must not exceed capacity
        model.Add(
            sum(section_room[s["section_id"], r_id] * s["total_slots_needed"] for s in sections) 
            <= weekly_room_capacity
        )

        # B. THE EXACT OVERLAP CONSTRAINT (Ensures no double-booking at the exact same hour)
        for d in days:
            for slot in range(slots_per_day):
                model.Add(sum(active_in_room[s["section_id"], r_id, d, slot] for s in sections) <= 1)

    # 4. Master Objective Function
    model.Minimize(
        10 * sum(variance_penalties) + 
        8 * sum(footprint_penalties)
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 180 
    solver.parameters.log_search_progress = True 

    # 1. Turn off the mathematical symmetry trap that ate 111 seconds
    solver.parameters.symmetry_level = 0 
    
    # 2. Limit CPU workers so your operating system doesn't kill the process
    solver.parameters.num_search_workers = 4 
    
    status = solver.Solve(model)
    
    status = solver.Solve(model)
    
    print(f"\nSolver finished with status: {solver.StatusName(status)}")
    
    output_schedule = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for sec in sections:
            s_id = sec["section_id"]
            
            assigned_room = None
            for r in rooms:
                if solver.Value(section_room[s_id, r["room_id"]]) == 1:
                    assigned_room = r["room_id"]
                    break
                    
            for d in days:
                for slot in range(slots_per_day):
                    if solver.Value(is_active[s_id, d, slot]) == 1:
                        output_schedule.append({
                            "section_id": s_id,
                            "room_id": assigned_room, 
                            "day": d,
                            "slot_index": slot
                        })
        print(f"Phase 1 Solved Successfully in {time.time() - start_time:.2f} seconds!")
        return output_schedule
    else:
        print("Phase 1 Failed: Infeasible layout.")
        return []

if __name__ == "__main__":
    departments = ["Software Eng", "Computer Science", "Data Science", "Artificial Intel"]
    generated_sections = []
    
    for i in range(1, 50):
        dept = departments[i % 4]
        semester = ((i % 8) // 2) + 1  
        slots_needed = [12, 14, 15][i % 3]
        
        generated_sections.append({
            "section_id": i,
            "name": f"{dept} - Sem {semester} (Sec {i})",
            "total_slots_needed": slots_needed
        })

    generated_rooms = [
        {"room_id": r, "name": f"Room 1.0{r}" if r < 10 else f"Room 1.{r}"} 
        for r in range(1, 30)
    ]

    dummy_input = {
        "config": {
            "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "slots_per_day": 7,
            "lunch_slot": 3 
        },
        "sections": generated_sections,
        "rooms": generated_rooms
    }
    
    print(f"Starting solver for {len(generated_sections)} sections and {len(generated_rooms)} rooms...")
    result = run_phase_1(dummy_input)
    
    if result:
        print("\n--- FINAL PHASE 1 TIMETABLE ---")
        for sec in dummy_input["sections"]:
            s_id = sec["section_id"]
            assigned_room = next((r["room_id"] for r in result if r["section_id"] == s_id), None)
            room_name = next((r["name"] for r in dummy_input["rooms"] if r["room_id"] == assigned_room), "Unknown")
            
            print(f"\n[ {sec['name']} ] -> Home Room: {room_name}")
            
            for d in dummy_input["config"]["days"]:
                slots = [r["slot_index"] for r in result if r["section_id"] == s_id and r["day"] == d]
                
                if slots:
                    print(f"  {d}: Slots {sorted(slots)}")
                else:
                    print(f"  {d}: Off Day")