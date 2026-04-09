from pyngrok import ngrok
import time

public_url = ngrok.connect(8000).public_url
print(f"\n============================================\nSUCCESS! PUBLIC URL:\n{public_url}\n============================================\n")

while True:
    time.sleep(1)
