#!/usr/bin/env python3
"""Probe one application publisher after successful construction of the listener node."""
import json
import sys
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

rclpy.init(args=sys.argv[1:])
node=Node('listener',enable_rosout=False,start_parameter_services=False)
print('NODE_READY',flush=True)
try:
    node.create_publisher(String,'/chatter',10)
except Exception as error:
    print(json.dumps({'phase':'create_publisher','publisher_created':False,'error':str(error)}),flush=True)
    node.destroy_node();rclpy.shutdown();raise SystemExit(2)
else:
    print(json.dumps({'phase':'create_publisher','publisher_created':True}),flush=True)
    node.destroy_node();rclpy.shutdown()
