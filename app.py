# Copyright (c) 2023, Horizon Robotics.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, request, render_template
from psutil import cpu_percent, virtual_memory, disk_usage
from os import system
import argparse

DEVICE_NAME = "rdkx3"
DEVICE_NUM = 0 # 0:rdkx3, 1:rdkultra
mode_list = ["performance", "schedutil", "powersave"]

# Flask app
app = Flask(__name__)
@app.route("/")
def index():
    return render_template(DEVICE_NAME + ".html")

@app.route("/wide")
def index_wide():
    return render_template(DEVICE_NAME + "_wide.html")

# 请求CPU, BPU, Memory, Tempture 信息（快速）
@app.route("/getState_rdkx3")
def getState_rdkx3():
    stateString = ""
    ## CPU
    # cpu0, cpu1, cpu2, cpu3,
    cpus = cpu_percent(percpu=True)
    stateString += "%.2f,%.2f,%.2f,%.2f,"%((cpus[0],cpus[1],cpus[2],cpus[3]))
    
    ## Memory
    # memory_free, memoryrate, (MiB)
    memorys = virtual_memory()
    stateString += "%012d,%012d,"%(memorys[3], memorys[1])
    
    ## BPU  ## Temp   ## CPU freq
    bpu0 = open('/sys/devices/system/bpu/bpu0/ratio', 'r', encoding='utf-8')
    bpu1 = open('/sys/devices/system/bpu/bpu1/ratio', 'r', encoding='utf-8')
    cpu_temp = open('/sys/class/hwmon/hwmon0/temp1_input', 'r',  encoding='utf-8')
    cpu_freq = open('/sys/devices/system/cpu/cpufreq/policy0/cpuinfo_cur_freq', 'r',  encoding='utf-8')
    stateString += "%03d,%03d,"%(int(bpu0.read()), int(bpu1.read()))
    stateString += "%s,"%cpu_temp.read()[0:5]
    stateString += "%s"%cpu_freq.read()[:-4]
    bpu0.close()
    bpu1.close()
    cpu_temp.close()
    cpu_freq.close()

    return stateString

# 请求磁盘占用信息（慢速）
@app.route("/getDisk_rdkx3")
def getDisk_rdkx3():
    ## 磁盘信息
    ## total, free
    disk_info = disk_usage("/")
    disk_info_string = "%014d,%014d"%(disk_info[1],disk_info[2])
    return disk_info_string

# 修改CPU性能模式
@app.route("/mode_rdkx3")
def mode_rdkx3():
    state_value = request.args.get('state')
    system("sudo bash -c \"echo " + mode_list[int(state_value)] + " > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor\"")
    return "OK"

@app.route("/test_page")
def test_page():
    return render_template("test_button.html")

if __name__ == "__main__":
    # 用户输入
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, default='-1', help='0: RDK X3 (Module), 1: RDK Ultra, 2: RDK X5\n')
    parser.add_argument('--port', type=int, default='7999', help='enter the port you like.')
    parser.add_argument('--debug', type=int, default='0', help='Flask Debug Mode, 0:false, 1:true.')
    parser.add_argument('--log', type=int, default='0', help='Flask log, 0:false, 1:true.')
    opt = parser.parse_args()
    # 设备判断(根据设备树)
    if opt.device == -1:
        # 自动判断
        tree = open('/sys/firmware/devicetree/base/model', 'r', encoding='utf-8').read()
        if "X3" in tree :
            DEVICE_NAME = "rdkx3"
            DEVICE_NUM = 0
            print("\033[31m"+"Auto Select Device: RDK X3 (Module)"+"\033[0m")
        elif "Journey 5" in tree:
            DEVICE_NAME = "rdkultra"
            DEVICE_NUM = 1
            print("\033[31m"+"Auto Select Device: RDK Ultra"+"\033[0m")
        elif "X5" in tree:
            DEVICE_NAME = "rdkx5"
            DEVICE_NUM = 2
            print("\033[31m"+"Auto Select Device: RDK X5"+"\033[0m")
        else:
            print("\033[31m"+"Your device didn't support."+"\033[0m")
            exit()
    elif opt.device == 0 :
        DEVICE_NAME = "rdkx3"
        DEVICE_NUM = 0
        print("\033[31m"+"User Select Device: RDK X3 (Module)"+"\033[0m")
    elif opt.device == 1:
        DEVICE_NAME = "rdkultra"
        DEVICE_NUM = 1
        print("\033[31m"+"User Select Device: RDK Ultra"+"\033[0m")
    elif opt.device == 2:
        DEVICE_NAME = "rdkx5"
        DEVICE_NUM = 2
        print("\033[31m"+"User Select Device: RDK X5"+"\033[0m")
    else:
        print("\033[31m"+"Wrong Device Number."+"\033[0m")
        exit()
        
    if opt.log == 0:
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    # 启动应用
    app.run(debug=bool(opt.debug), port=opt.port, host="0.0.0.0")
