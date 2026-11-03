import subprocess, time, os
os.chdir(r'C:\Users\mikel\Desktop\Pruebas\nasa')
log = open(r'C:\Users\mikel\Desktop\Pruebas\nasa\scratch\nb06.log', 'w')
proc = subprocess.Popen([r'.venv\Scripts\python.exe', '-m', 'nbconvert', '--execute', '--inplace', r'notebooks\06_evaluacion_produccion_comparativa.ipynb'], stdout=log, stderr=subprocess.STDOUT)
for i in range(72):
    time.sleep(5)
    if proc.poll() is not None:
        print('finished', proc.returncode)
        log.close()
        break
else:
    print('still running after 360s, pid', proc.pid)
