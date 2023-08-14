import os

workers = int(os.environ.get("WORKER_COUNT", "5"))
threads = int(os.environ.get("THREAD_COUNT", "2"))
timeout = int(os.environ.get("TIMEOUT", "600"))