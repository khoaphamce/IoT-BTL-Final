from apscheduler.schedulers.background import BackgroundScheduler
import time
import uuid
from datetime import datetime, timedelta
import json
from  adafruit import create_client
from rs485 import setDeviceON,setDeviceOFF,readMoisture,readTemperature
import serial

ADAFRUIT_IO_USERNAME = "khoaphamce"
ADAFRUIT_IO_KEY = "aio_hHVv98lytxxgrfjwyQrYJwXM87oR"
    
# Global scheduler and schedules
scheduler = BackgroundScheduler()
schedules = []

new_schedules = [ 
    {'cycle': 3, 'flow 1': 20, 'flow 2': 10, 'flow 3': 20, 'isActive': True, 'schedulerName': 'New Lich Tuoi', 'startTime': '21:48', 'stopTime': '21:49'},
    {'cycle': 5, 'flow 1': 20, 'flow 2': 10, 'flow 3': 20, 'isActive': True, 'schedulerName': 'New Lich Tuoi 1', 'startTime': '17:01', 'stopTime': '17:10'},
    {'cycle': 1, 'flow 1': 20, 'flow 2': 10, 'flow 3': 20, 'isActive': False, 'schedulerName': 'New Lich Tuoi 2', 'startTime': '14:57', 'stopTime': '15:00'},
    {'cycle': 3, 'flow 1': 20, 'flow 2': 10, 'flow 3': 20, 'isActive': True, 'schedulerName': 'New Lich Tuoi 3', 'startTime': '17:12', 'stopTime': '17:15'}
]


'''

remove_all job 

'''
def message(client , feed_id , payload):
    print("Nhan du lieu: " + payload + f'  feed id : {feed_id}')
    
    if(feed_id=='schedules'):
        global new_schedules, scheduler
        new_schedules = json.loads(payload)
        print("==== UPDATING SCHEDULER ... ====")
        print()
        scheduler = reset_scheduler()
        print("==== START NEW SCHEDULER ====")
        print()
        scheduler.start()

        initial_base_behavior(scheduler,client)
        update_schedules(new_schedules,scheduler) 

client = create_client(ADAFRUIT_IO_USERNAME,ADAFRUIT_IO_KEY, message)

def activate_relay(relay_id, duration):
    """Activate a relay for a specified duration."""
    setDeviceON(relay_id)
    time.sleep(duration)
    setDeviceOFF(relay_id)


def update_schedules(new_schedules,scheduler): #use when use input new scheduler
    """Remove all current jobs, clear schedules, and update with new schedules."""
    global schedules
    # Remove all existing jobs
    for sched in schedules:
        scheduler.remove_job(sched['id'])
    schedules.clear()
    # Add new schedules
    for sched in new_schedules:
        if(sched['isActive']):
            add_schedule(sched,scheduler)

def daily_job(scheduler):
    # Readd sche
    update_schedules(new_schedules,scheduler)
    
def initial_base_behavior(scheduler,client):
    # Clean and readd all schedules 
    print('==== Initial reading sensor job ====')
    scheduler.add_job(readSerial, args=[client], trigger='interval', minutes=1)
    print('==== All schedules are updated at every 0:00 ====')
    scheduler.add_job(daily_job,args=[scheduler],trigger='cron', hour=0, minute=0)
    

def reset_scheduler():
    print("==== RESET SCHEDULER ====")
    print()
    scheduler.shutdown(wait=False)
    scheduler.remove_all_jobs()
    return BackgroundScheduler()

# Can seperate activate relay , mixer , pump- in , pump-out (instead of time.spleep duraion can for loop to sleep (1))

def process_fsm(schedule):
    """Process a single irrigation cycle based on the schedule."""
    
    print('==== Start Process ====')
    
    for i in range(1, 4):  # Fertilizer tanks 1 to 3
        relay_id = i
        flow_amount = schedule[f'flow {i}']
        print(f"Activating relay {relay_id} for {flow_amount}ml")
        # Can adding keep track the water level by activate one more sensor to read data
        activate_relay(relay_id, 10)  # Assuming 10s for simplicity, replace with actual flow sensor logic

    # # Water pump-in process
    print("Activating water pump-in")
    activate_relay(7, 10)  # 20s or until water is detected
    
    print("Chosse Selector Area and pump-out")
    activate_relay(8, 10)
    print('Stop Process')
    
def add_schedule(schedule,scheduler):
    """Add a new schedule and schedule the corresponding jobs."""
    schedule['id'] = str(uuid.uuid4())  # Assign a unique ID to the schedule
    # schedules.append(schedule)
    schedule_jobs(schedule,scheduler)

def remove_schedule(schedule_id):
    """Remove a schedule and its jobs from the scheduler."""
    global schedules
    schedules = [s for s in schedules if s['id'] != schedule_id]
    scheduler.remove_job(schedule_id)

def print_job_count(scheduler):
    """Print the number of currently scheduled jobs."""
    jobs = scheduler.get_jobs()
    job_count = len(jobs)
    print(f"Current number of jobs scheduled: {job_count}")
    return job_count

def process_cycle(schedule, scheduler):
    """Process a single cycle and schedule the next cycle if conditions are met."""
    print(f"Processing cycle for {schedule['schedulerName']} ID: {schedule['id']} - Cycle count: {schedule['cycle_count']}")

    start_time = time.time()
    # Simulate variable processing time
    process_fsm(schedule)
    end_time = time.time()
    print(f'Cycle took {end_time-start_time}')

    # Update the number of cycles completed
    schedule['cycle_count'] += 1

    next_run_time = datetime.now() + timedelta(seconds=45)

    if next_run_time < schedule['stop_dt'] and schedule['cycle_count'] < schedule['max_cycles']:
        scheduler.add_job(process_cycle, args=[schedule, scheduler],id=schedule['id'], next_run_time=next_run_time)
    else : 
        print(f"Finish Processing Job for {schedule['schedulerName']} ID: {schedule['id']}")


def schedule_jobs(schedule, scheduler):
    """Schedule the initial job at startTime."""
    schedule['start_dt'] = datetime.now().replace(hour=int(schedule['startTime'].split(':')[0]),
                                                  minute=int(schedule['startTime'].split(':')[1]),
                                                  second=0, microsecond=0)
    schedule['stop_dt'] = schedule['start_dt'].replace(hour=int(schedule['stopTime'].split(':')[0]),
                                                       minute=int(schedule['stopTime'].split(':')[1]))

    if datetime.now() > schedule['start_dt']:
        print(f"It is over start time {datetime.now()} start_time{schedule['start_dt']} -> Skip {schedule['schedulerName']}")
        pass
    else:
        # Initialize cycle count
        schedule['cycle_count'] = 0
        schedule['max_cycles'] = schedule['cycle']  # Maximum number of cycles
        scheduler.add_job(process_cycle, args=[schedule, scheduler], next_run_time=schedule['start_dt'],id=schedule['id'])
        
        print(f"Initial job scheduled: {schedule['schedulerName']} with ID {schedule['id']} from {schedule['startTime']} to {schedule['stopTime']}")


def calculate_time_window(start_time, stop_time, cycle_count):
    fmt = '%H:%M'
    delta = datetime.strptime(stop_time, fmt) - datetime.strptime(start_time, fmt)
    total_minutes = delta.total_seconds() / 60
    return total_minutes / cycle_count

def readSerial(client):
    value_temperature = readTemperature()/100
    print(f'Publish temperature value {value_temperature}')
    client.publish("temperature", value_temperature)
    value_moisture = readMoisture()/100
    print(f'Publish moisture value {value_moisture}')
    client.publish("humidity", value_moisture)


def main():
    # initial connection 
    scheduler.start()
    
    # initial_base_behavior(scheduler)
    print("==== INITIAL SYSTEM ====")
    
    initial_base_behavior(scheduler,client)    
    # Update schedules with a fresh set
    update_schedules(new_schedules,scheduler)

    try:
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shutdown cleanly.")

if __name__ == "__main__":
    main()