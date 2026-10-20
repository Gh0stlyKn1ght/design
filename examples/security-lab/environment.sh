# Source in each lab terminal after sourcing ROS 2 Jazzy.
# Set ROS_SECURITY_KEYSTORE to the absolute lab keystore path separately.
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=42
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
unset ROS_SECURITY_ENCLAVE_OVERRIDE
