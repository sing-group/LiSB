import threading
import time

import schedule


def say_hello(name, greeting):
    print(f"Hello {name}! {greeting}")


def job():
    while True:
        schedule.run_pending()
        time.sleep(1)


schedule.every(5).seconds.do(say_hello, "César", "How are you?")
threading.Thread(target=job).start()

while True:
    print("Main thread here")
    time.sleep(1)
