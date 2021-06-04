from core import GracefulKiller

killer = GracefulKiller()

while not killer.kill_now:
    pass

print("Finished gracefully")