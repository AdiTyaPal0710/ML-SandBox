import docker 
import tempfile 
import os
import uuid


def build_sandbox_image(requirements: str = "") -> str:
    """
    Builds a Docker image with the given requirements pre-installed.
    Returns the image tag to reuse across iterations.
    If no requirements, returns the base image name.
    """
    base_image = "python:3.10-slim"

    if not requirements.strip():
        return base_image

    client = docker.from_env()
    tag = f"sandbox-session-{uuid.uuid4().hex[:8]}"

    with tempfile.TemporaryDirectory() as build_dir:
        # Write requirements file
        req_path = os.path.join(build_dir, "requirements.txt")
        with open(req_path, "w") as f:
            f.write(requirements)

        # Write Dockerfile
        dockerfile_path = os.path.join(build_dir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write(f"FROM {base_image}\n")
            f.write("COPY requirements.txt /tmp/requirements.txt\n")
            f.write("RUN pip install --no-cache-dir -r /tmp/requirements.txt\n")

        print(f"   [Docker] Building image '{tag}' with requirements...")
        client.images.build(path=build_dir, tag=tag, rm=True)
        print(f"   [Docker] Image '{tag}' ready.")

    return tag


def cleanup_sandbox_image(image_tag: str):
    """Removes the custom sandbox image if it's not the base image."""
    if image_tag and not image_tag.startswith("python:"):
        try:
            client = docker.from_env()
            client.images.remove(image_tag, force=True)
            print(f"   [Docker] Cleaned up image '{image_tag}'.")
        except Exception:
            pass


def run_Sandbox(script_string: str, image: str = "python:3.10-slim")->dict: 
    
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        return {"error":str(e)}

    with tempfile.TemporaryDirectory() as temp_dir:

        script_path = os.path.join(temp_dir,"train.py")
        with open(script_path,"w") as f:
            f.write(script_string)

        try:
            data_dir = os.path.abspath("./data")
            os.makedirs(data_dir, exist_ok=True)

            container = client.containers.run(
                image=image,
                command="python /workspace/train.py",
                detach=True,
                mem_limit="512m",
                nano_cpus=1_000_000_000,
                volumes={
                    temp_dir: {"bind": "/workspace", "mode": "rw"},
                    data_dir: {"bind": "/data", "mode": "ro"},
                }
            )

            try:
                result = container.wait(timeout=120)
            except Exception:
                container.kill()
                result = {"StatusCode":-1}

            exit_code = result.get("StatusCode")
            stdout = container.logs().decode('utf-8')

            container.remove()

            return {
                "exit_code": exit_code,
                "logs": stdout,
                "status": "SUCCESS" if exit_code == 0 else "FAILED"
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "logs": str(e),
                "status": "SYSTEM_ERROR"
            }
            
if __name__ == "__main__":

    print("Testing Docker Sandbox...\n")
    
    good_code = """
print("Hello from inside the Docker container!")
x = 10
y = 20
print(f"The AI calculated: {x} + {y} = {x+y}")
    """
    
    print("--- Test 1: Good Code ---")
    result1 = run_Sandbox(good_code)
    print(f"Status: {result1['status']}")
    print(f"Exit Code: {result1['exit_code']}")
    print("Logs from Docker:\n" + result1['logs'])
    
    bad_code = """
print("I am about to do something illegal...")
1 / 0 
    """
    
    print("\n--- Test 2: Bad Code ---")
    result2 = run_Sandbox(bad_code)
    print(f"Status: {result2['status']}")
    print(f"Exit Code: {result2['exit_code']}")
    print("Logs from Docker:\n" + result2['logs'])