#!/usr/bin/env python
import rospy
import numpy as np
from sensor_msgs.msg import Joy
from duckietown_msg_jenshen.msg import Flip
import time

class VirtualMirror(object):
    def __init__(self):
        self.node_name = rospy.get_name()
        rospy.loginfo("[%s] Initializing " %(self.node_name))
        
        self.virt_mirror = None
        self.image_sub = rospy.Subscriber("image_sub",CompressedImage,self.callback)
        self.image_pub = rospy.Publisher("image_pub/compressed",CompressedImage, queue_size=1)
        
        self.last_pub_msg = None
        self.last_pub_time = rospy.Time.now()
        
        self.flip = Flip()

        # Setup Parameters
        self.speed_gain = self.setupParam("~speed_gain", 1.0)
        self.steer_gain = self.setupParam("~steer_gain", 1.0)

        # Publications
        self.pub_wheels = rospy.Publisher("~wheels_cmd", WheelsCmdStamped, queue_size=1)

        # Subscriptions
        self.sub_joy_ = rospy.Subscriber("joy", Joy, self.cbJoy, queue_size=1)
        
        # timer
        # self.pub_timer = rospy.Timer(rospy.Duration.from_sec(self.pub_timestep),self.publishControl)
        self.param_timer = rospy.Timer(rospy.Duration.from_sec(1.0),self.cbParamTimer)
        self.has_complained = False

    def cbParamTimer(self,event):
        self.speed_gain = rospy.get_param("~speed_gain", 1.0)
        self.steer_gain = rospy.get_param("~steer_gain", 1.0)

    def setupParam(self,param_name,default_value):
        value = rospy.get_param(param_name,default_value)
        rospy.set_param(param_name,value) #Write to parameter server for transparancy
        rospy.loginfo("[%s] %s = %s " %(self.node_name,param_name,value))
        return value

    def cbJoy(self, joy_msg):
        self.joy = joy_msg
        self.publishControl()

    def publishControl(self):
        speed = self.joy.axes[1] * self.speed_gain #Left stick V-axis. Up is positive
        steering = self.joy.axes[3] * self.steer_gain
        wheels_cmd_msg = WheelsCmdStamped()

        # Car Steering Mode
        vel_left = (speed - steering)
        vel_right = (speed + steering)
        wheels_cmd_msg.header.stamp = self.joy.header.stamp
        wheels_cmd_msg.vel_left = np.clip(vel_left,-1.0,1.0)
        wheels_cmd_msg.vel_right = np.clip(vel_right,-1.0,1.0)
        rospy.loginfo("[%s] left %f, right %f" % (self.node_name,wheels_cmd_msg.vel_left,wheels_cmd_msg.vel_right))
        self.pub_wheels.publish(wheels_cmd_msg)

if __name__ == "__main__":
    rospy.init_node("joy_mapper",anonymous=False)
    joy_mapper = JoyMapper()
    rospy.spin()
