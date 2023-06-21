import os
def get_dependecies():
    blob = "git+https://github.com"
    requirements_path = os.path.join(
        os.path.abspath(os.getcwd()),
        "requirements.txt"
    )
    if os.path.isfile(requirements_path):
        with open(requirements_path) as f:
            dependencies = [
                ">=".join(x.split("==")) for x in f.read().splitlines()
            ]
            for x in dependencies:
                if x.startswith(blob):
                    # split the text and join them with the @ command
                    # index 3 holds the name of the module
                    chunks = x.split("/")
                    dependencies[dependencies.index(x)] = x.replace(
                        blob, chunks[3] + " @ " + blob
                    )
                    break
        return dependencies