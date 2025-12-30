import subprocess

with open("build_final.log", "w") as f:
    subprocess.run(["dotnet", "build"], stdout=f, stderr=f, cwd="D:\\Project 3\\picogk_runner")
