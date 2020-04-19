#!/usr/bin/python3

import json
from flask import Flask, jsonify, request, Response
import MemUsageMonitor

app = Flask(__name__)

mum = MemUsageMonitor.MemUsageMonitor()

# curl -d '{"threshold":40}' -H "Content-Type: application/json" -X POST http://<IP>:5000/memusage

@app.route('/')
def index():
    helpMsg = { "/"                                      : "This help message",
                "/memusage"                              : "Memory usage",
                "/memusage POST data {'threshold' : 40}" : "Change mem usage threshold"
               }
    return jsonify(helpMsg)

@app.route('/memusage', methods=['GET'])
def memusage():
    return jsonify(mum.getMemUsage())

@app.route('/memusage', methods=['POST'])
def setMemUsageThreshold():
    request_data = request.get_json()
    if 'threshold' in request_data:
        threshold = request_data['threshold']
        mum.setMemUsageThreshold(threshold)
        return Response("", 201, mimetype='application/json')
    else:
        invalidThresholdErrMsg = {
            "error" : "Invalid mem usage threshold",
            "helpString" : "Valid data should be like {'threshold' : 40}"
        }
        return Response(json.dumps(invalidThresholdErrMsg), status=400, mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

