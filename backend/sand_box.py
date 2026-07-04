import docker 
import tempfile 
import os

def run_Sandbox(script_string: str)->dict: 

    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        return {"error":str(e)}

    with tempfile.TemporaryDirectory() as temp_dir:

        script_path = os.path.join(temp_dir,"train.py")
        with open(script_path,"w") as f:
            f.write(script_string)
        
        try:
            container = client.containers.run(
                image="python:3.10-slim",
                command="python /workspace/train.py",
                detach=True,
                volumes = {
                    temp_dir: {"bind": "/workspace", "mode": "rw"} 
                }
            )
            result = container.wait(timeout=120)

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