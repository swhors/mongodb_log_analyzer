import os


def write_pid(file_path: str):
    with open(file_path, "wt") as fd:
        fd.write(f"{os.getpid()}")
        fd.close()
