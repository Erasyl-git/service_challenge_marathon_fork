import subprocess
import multiprocessing

def run_gunicorn():
    subprocess.run([
        "gunicorn", 
        "service_challenge_marathon.wsgi:application", 
        "--bind", "0.0.0.0:8010", 
        "--workers", "8",
        "--access-logfile", "-",
        "--error-logfile", "-"
    ])



if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_gunicorn)

    p1.start()

    p1.join()

