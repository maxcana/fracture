# fracture 1.0
# simulates rng from seed
import json
import pyperclip

class eD:
    def __init__(self, t):
        self.state = int(t) & 0xFFFFFFFFFFFFFFFF

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        t = self.state
        t = (t ^ (t >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
        t = (t ^ (t >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
        t = t ^ (t >> 31)
        return t & 0xFFFFFFFFFFFFFFFF

    def nextFloat(self):
        return self.next() / 0x10000000000000000

    def nextInt(self, t, n):
        return int(self.next_float() * (n - t)) + t

# get actions.json data for usage in get_db_action
with open("data/actions.json", "r") as file:
    tD = json.load(file)

def get_db_action(skill_id, action_id):
    skill_id = str(skill_id)
    action_id = str(action_id)
    
    # Retrieve the skill by ID
    skill = tD.get(skill_id)
    if not skill:
        print(f"Skill ID {skill_id} not found.")
        return None
    
    # Retrieve the action by ID
    action = skill["actions"].get(action_id)
    if not action:
        print(f"Action ID {action_id} not found in skill {skill_id}.")
        return None
    
    # Sort rewards by drop_rate
    action["rewards"] = sorted(action["rewards"], key=lambda r: r["drop_rate"])
    
    return action

input("copy the request start-action/\npress enter...")

def get_active_action_from_clipboard():
    unprocessed = pyperclip.paste()
    return json.loads(unprocessed).get("action", {"failure": "yes"})

active_action = get_active_action_from_clipboard()
print(active_action)
rng = eD(active_action.get("seed"))

def update_progress(cycles):
    cycles = int(cycles)
    
    # Unpack state
    i = active_action #state.get("active_action")
    
    s = get_db_action(i.get("skill_id"), i.get("action_id")) #state.get("db_action")
    o = rng # state.get("rng")
    u = 0 # state.get("last_completed_cycle", 0)
    # f = state.get("start_time", 0)
    m = {} # state.get("loot", {})
    
    if not i or not o or not s:
        return
    
    # Extract action details
    # h = s.get("duration")
    g = s.get("rewards", [])
    #v = s.get("requirements", []) # ingredients for crafting recipe
    # x = h * (1 - i.get("speed_bonus", 0) / 100)
    # w = state.get("server_time") - f
    # if w <= 0:
    #     return
    
    # Calculate time metrics
    # S = w / 1000  # Elapsed time in seconds
    # C = x / 1000  # Cycle duration in seconds
    # j = (S % C) / C  # Progress within the current cycle (0-1, displayed as %)
    N = m.copy()  # Copy current loot
    #R = 100 # int(S // C)  # Number of completed cycles to be calculated
    O = 0 + cycles #i.get("action_count", 0) + R  # Total completed cycles (after counting old cycles "action_count")
    
    
    drops = []
    
    # Process completed cycles
    if O > u:
        # Handle crafting requirements
        #if v:
            #calculate_used_in_crafting_items(O, state)
        
        #k = state.get("inventory")
        G = s.get("single_reward", False)
        
        for U in range(u, O):
            # Check requirements for each cycle
            #if v and not all(requirements_met(P, i, k) for P in v):
                #break
            
            # Distribute rewards
            for reward in g:
                drop_rate = reward["drop_rate"] * (1 + i.get("quality_bonus", 0))
                if o.nextFloat() <= drop_rate:  # Use RNG for drop chance
                    quantity = (
                        reward["quantity"]
                        if reward["quantity"] == reward["max_quantity"]
                        else o.nextInt(reward["quantity"], reward["max_quantity"] + 1)
                    )
                    item_id = reward["item_id"]
                    N[item_id] = N.get(item_id, 0) + quantity
                    if G:
                        break
            drops.append((U, quantity, item_id))
        
        # Update skill experience
        

        # O is the ending action #, u is the starting action number, always 0. (index doesnt matter as seen in the loop above U is not used)
        # j = 0  # Reset progress within the current cycle
    
    # Update final state
    # final_state = {
    #     "calculated_experience": O * s.get("experience", 0),
    #     # "progress": j * 100,
    #     "last_completed_cycle": O,
    #     "completed_cycles": R,
    #     "total_completed_cycles": O,
    #     "loot": N,
    # }

    # print("skill " + i.get("skill_id") + " xp increased by " + O * s.get("experience", 0))
    
    return drops


# load items database
with open("data/items.json", "r") as file: items_db = json.load(file)

def run():
    # calculate drops from seed
    drops = update_progress(1000)

    # config
    interesting_qualities = ["RARE", "EPIC"]
    show_first_n_of_each_quality = 3
    print_each_drop = False

    qualities = {}
    for drop in drops:
        drop_number = drop[0]+1
        item_quantity = drop[1]
        item_id = str(drop[2])
        q = items_db[item_id]["quality"].upper()
        
        if(q in interesting_qualities):
            if q in qualities:
                qualities[q].append((drop_number, item_quantity, item_id))
            else:
                qualities[q] = [(drop_number, item_quantity, item_id)]
        if(print_each_drop): 
            print(f"drop #{drop_number}: {item_quantity}x item {item_id}")
        
    # print basic info
    for key, value in qualities.items():
        
        print(f"{key}:")
        for i in range(0, len(value)):
            if(i < show_first_n_of_each_quality): print(f"#{value[i][0]}: {value[i][1]}x {items_db[value[i][2]]["name"]["en"].lower()}")
            elif (i == len(value) - 1): print(f"({len(value) - show_first_n_of_each_quality} more)")
            
    input("run again?")
    run()
run()