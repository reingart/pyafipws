import subprocess

def get_dependecies() -> list:
    # The subprocess.Popen is used for backward compatibility with python 2.7
    freeze = subprocess.Popen("pip freeze", shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    g = freeze[0].decode("utf-8").split("\r\n")
    dependencies = [">=".join(x.split("==")) for x in g]
    return dependencies