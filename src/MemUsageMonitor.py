import psutil
import asyncio
import os
import subprocess
import re
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

def shell(cmd):
    result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = result.communicate()
    if stderr:
        Exception(stderr.decode("utf-8"))

    return stdout.decode('utf8').strip().split('\n')

#
# Inside container:
#     default via 172.17.0.1 dev eth0
# Outside container:
#    default via <ip1> dev ens3 proto dhcp src <ip2> metric 100
#
def get_host_ip():
    cmd = ['ip', 'route']
    output = shell(cmd)
    regex = r"default via ((?:[0-9]{1,3}\.){3}[0-9]{1,3}) dev eth0"
    for line in output:
        result = re.findall(regex, line)
        if result:
            return result[0]
    return '0.0.0.0'

subject_mem = "mem_usage_fault"

async def publishNATS(loop, msg):
    nats_server = os.getenv('NATS_SERVER')
    # If no environment variable NATS_SERVER, assume NATS server runs on host machine
    if nats_server == None:
        nats_server = get_host_ip()
    print("NATS server: {}".format(nats_server))

    nats_conn = NATS()

    async def error_cb(e):
        print("Error:", e)

    async def closed_cb():
        print("Connection to NATS is closed.")

    async def reconnected_cb():
        print("Reconnected to NATS at {} ...".format(nats_conn.connected_url.netloc))

    options = {
        "loop": loop,
        "error_cb": error_cb,
        "closed_cb": closed_cb,
        "reconnected_cb": reconnected_cb,
        "servers" : ["nats://{}:4222".format(nats_server)]
    }

    try:
        await (nats_conn.connect(**options))
    except Exception as e:
        print(e)

    print("Connected to NATS at {} ...".format(nats_conn.connected_url.netloc))
    encoded_msg = msg.encode('utf-8')
    await (nats_conn.publish(subject_mem, encoded_msg))
    await nats_conn.flush()
    print("Message published with subject {}: {}".format(subject_mem, msg))
    await nats_conn.close()

def publishFault(msg):
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(publishNATS(loop, msg))
    finally:
        loop.close()

class MemUsageMonitor:
    MEM_USAGE_THRESHOLD = 80

    def __init__(self):
        self._mem_usage = psutil.virtual_memory().percent
        self._mem_usage_threshold = MemUsageMonitor.MEM_USAGE_THRESHOLD

    def getMemUsage(self):
        mem_usage = {}
        mem_usage['Mem Usage'] = psutil.virtual_memory().percent
        mem_usage['Mem Usage Threshold'] = self._mem_usage_threshold
        if psutil.virtual_memory().percent >= self._mem_usage_threshold:
            mem_usage['Mem Usage Fault'] = True
            self.notifyFault();
        else:
            mem_usage['Mem Usage Fault'] = False
        return mem_usage

    def setMemUsageThreshold(self, threshold):
        self._mem_usage_threshold = threshold

    def notifyFault(self):
        msg = "Mem usage {} exceeded threshold {}!!!".format(self._mem_usage, self._mem_usage_threshold)
        publishFault(msg)

    def __str__(self):
        output = "_mem_usage : {}, _mem_usage_threshold : {}".format(self._mem_usage, self._mem_usage_threshold)
        return output

    def __repr__(self):
        return 'MemUsageMonitor'

# pip3 install psutil 
# pip3 install asyncio-nats-client[nkeys]
if __name__ == '__main__':
    mum = MemUsageMonitor()
    print(mum.getMemUsage())

