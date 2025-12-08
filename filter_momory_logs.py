import os
import gzip

keywords = ["137", "killed", "oom", "out of memory", "memory limit", "no memory"]

memory_logs = []

# Only search in failed logs directory
for root, dirs, files in os.walk("logs_failure"):
    for file in files:
        if file.endswith(".txt") or file.endswith(".log"):

            path = os.path.join(root, file)
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read().lower()

                if any(k in content for k in keywords):
                    memory_logs.append(path)
            except:
                pass

with open("memory_logs.txt", "w") as f:
    for log in memory_logs:
        f.write(log + "\n")

print(f"Found {len(memory_logs)} logs with memory issues")
print("Saved memory_logs.txt")
