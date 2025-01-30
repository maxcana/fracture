# fracture 1.0
# simulates rng from seed
from functools import reduce
import json
import pyperclip

# load items database
with open("data/items.json", "r") as file: items_db = json.load(file)

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
        return int(self.nextFloat() * (n - t)) + t

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
    
    return action.copy()

def get_adjusted_rates_action(action):
    # Get the action details
    db_action = get_db_action(action["skill_id"], action["action_id"])
    if not db_action:
        return None

    # Extract slot choices
    selected_slots = list(action.get("slot_choices", {}).values())

    # Filter requirements that match the selected slot items
    matching_requirements = [
        req for req in db_action["requirements"] if req["item_id"] in selected_slots
    ]
    print(f"matching_requirements {matching_requirements}")

    # Adjust drop rates for rewards based on matching requirements
    adjusted_rewards = []
    for reward in db_action["rewards"]:
        drop_rate = reward["drop_rate"]

        # Apply quality bonuses from matching requirements
        for req in matching_requirements:
            if req["quality_bonus_target"] == reward["quality"] and req["quality_bonus"] > 0:
                print(f"Changed drop rate of Q{reward["quality"]} {items_db[str(reward["item_id"])]['name']['en']} from {drop_rate} to {drop_rate + req["quality_bonus"]} due to ingredient quality")
                drop_rate += req["quality_bonus"]

        # Store adjusted reward
        adjusted_rewards.append({**reward, "drop_rate": drop_rate})

    # Sort rewards by adjusted drop rate (ascending order) to match with the js logic to not ensure desync and also maybe if it's not sorted a rare could become a common etc
    adjusted_rewards.sort(key=lambda r: r["drop_rate"])
    
    #print(f"original rewards: {db_action["rewards"]}")
    #print(f"adjusted rewards: {adjusted_rewards}")
    
    db_action["rewards"] = adjusted_rewards
    
    return db_action

def coalesce(*arg):
  return reduce(lambda x, y: x if x is not None else y, arg)

def update_progress(cycles, active_action, rng):
    cycles = int(cycles)
    
    # Unpack state
    i = active_action  # state.get("active_action")
    s = coalesce(get_adjusted_rates_action(active_action), get_db_action(i["skill_id"], i["action_id"])) # state.get("db_action")
    o = rng  # state.get("rng")
    u = 0  # state.get("last_completed_cycle", 0)
    m = {}  # state.get("loot", {})

    if not i or not o or not s:
        return
    
    # Extract action details
    rewards = s.get("rewards")

    O = u + cycles  # Total completed cycles
    drops = []

    # Process completed cycles
    if O > u:
        G = s.get("single_reward", False)  # Flag for a single reward drop per cycle

        for U in range(u, O):
            for reward in rewards:
                # Step 1: Start with the base drop rate
                drop_rate = reward["drop_rate"]

                # Step 3: Apply the global quality bonus (EVEN TO THE ADJUSTED RATES LMAO)
                
                drop_rate *= (1 + i.get("quality_bonus", 0))
                #print(f"Q{reward["quality"]} {items_db[str(reward["item_id"])]['name']['en']} final drop rate: {drop_rate} (+{i.get("quality_bonus", 0) * 100}%)")

                # Step 4: Perform RNG check for drop chance
                nextFloat = o.nextFloat()

                if nextFloat <= drop_rate:
                    quantity = (
                        reward["quantity"]
                        if reward["quantity"] == reward["max_quantity"]
                        else o.nextInt(reward["quantity"], reward["max_quantity"] + 1)
                    )
                    item_id = reward["item_id"]
                    m[item_id] = m.get(item_id, 0) + quantity
                    drops.append((U, quantity, item_id))
                    
                    # If only one reward should drop, break after the first successful drop
                    if G:
                        break

    return drops



def run():
    input("copy the request start-action/\npress enter...")

    def get_active_action_from_clipboard():
        unprocessed = pyperclip.paste()
        return json.loads(unprocessed).get("action", {"failure": "yes"})

    active_action = get_active_action_from_clipboard()
    print(active_action)
    rng = eD(active_action.get("seed"))

    
    # calculate drops from seed
    drops = update_progress(100000, active_action, rng)

    # config
    interesting_qualities = [3, 4, 5]
    quality_to_name = {0: "poor", 1: "common", 2: "uncommon", 3: "rare", 4: "epic", 5: "legendary", 6: "rarity-6"}
    show_first_n_of_each_quality = 5
    #end config

    qualities = {quality_to_name[key]: [] for key in interesting_qualities}
    for drop in drops:
        drop_number = drop[0]+1
        item_quantity = drop[1]
        item_id = str(drop[2])
        q = items_db[item_id]["quality"]
        
        if(q in interesting_qualities):
            qualities[quality_to_name[q]].append((drop_number, item_quantity, item_id))
        
    # print basic info
    for key, value in qualities.items():
        
        print(f"{key}:")
        for i in range(0, len(value)):
            if(i < show_first_n_of_each_quality): print(f"#{value[i][0]}: {value[i][1]}x {items_db[value[i][2]]["name"]["en"].lower()}")
            elif (i == len(value) - 1): print(f"({len(value) - show_first_n_of_each_quality} more)")
            
    input("run again?")
    run()
run()