import os

def get_dependecies() -> list:
    requirements_path = os.path.join(os.path.abspath(os.getcwd()), "requirements.txt")
    if os.path.isfile(requirements_path):
        with open(requirements_path) as f:
            dependencies = [">=".join(x.split("==")) for x in f.read().splitlines()]
    return dependencies