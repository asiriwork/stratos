# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging

import paho.mqtt.publish as publish

from .. event.instance.status.events import *
from .. config.cartridgeagentconfiguration import CartridgeAgentConfiguration
from .. util import cartridgeagentconstants
from .. healthstatspublisher.healthstats import *
from .. healthstatspublisher.abstracthealthstatisticspublisher import *


log = LogFactory().get_log(__name__)

started = False
activated = False
ready_to_shutdown = False
maintenance = False

publishers = {}
""" :type : dict[str, EventPublisher] """


def publish_instance_started_event():
    global started, log
    if not started:
        log.info("Publishing instance started event")
        service_name = CartridgeAgentConfiguration().service_name
        cluster_id = CartridgeAgentConfiguration().cluster_id
        network_partition_id = CartridgeAgentConfiguration().network_partition_id
        parition_id = CartridgeAgentConfiguration().partition_id
        member_id = CartridgeAgentConfiguration().member_id

        instance_started_event = InstanceStartedEvent(service_name, cluster_id, network_partition_id, parition_id,
                                                      member_id)
        publisher = get_publisher(cartridgeagentconstants.INSTANCE_STATUS_TOPIC + cartridgeagentconstants.INSTANCE_STARTED_EVENT)
        publisher.publish(instance_started_event)
        started = True
        log.info("Instance started event published")
    else:
        log.warn("Instance already started")


def publish_instance_activated_event():
    global activated, log
    if not activated:
        log.info("Publishing instance activated event")
        service_name = CartridgeAgentConfiguration().service_name
        cluster_id = CartridgeAgentConfiguration().cluster_id
        network_partition_id = CartridgeAgentConfiguration().network_partition_id
        parition_id = CartridgeAgentConfiguration().partition_id
        member_id = CartridgeAgentConfiguration().member_id

        instance_activated_event = InstanceActivatedEvent(service_name, cluster_id, network_partition_id, parition_id,
                                                          member_id)
        publisher = get_publisher(cartridgeagentconstants.INSTANCE_STATUS_TOPIC + cartridgeagentconstants.INSTANCE_ACTIVATED_EVENT)
        publisher.publish(instance_activated_event)

        log.info("Instance activated event published")
        log.info("Starting health statistics notifier")

        if CEPPublisherConfiguration.get_instance().enabled:
            interval_default = 15  # seconds
            interval = CartridgeAgentConfiguration().read_property("stats.notifier.interval", False)
            if interval is not None and len(interval) > 0:
                try:
                    interval = int(interval)
                except ValueError:
                    interval = interval_default
            else:
                interval = interval_default

            health_stats_publisher = HealthStatisticsPublisherManager(interval)
            log.info("Starting Health statistics publisher with interval %r" % interval_default)
            health_stats_publisher.start()
        else:
            log.warn("Statistics publisher is disabled")

        activated = True
        log.info("Health statistics notifier started")
    else:
        log.warn("Instance already activated")


def publish_maintenance_mode_event():
    global maintenance, log
    if not maintenance:
        log.info("Publishing instance maintenance mode event")

        service_name = CartridgeAgentConfiguration().service_name
        cluster_id = CartridgeAgentConfiguration().cluster_id
        network_partition_id = CartridgeAgentConfiguration().network_partition_id
        parition_id = CartridgeAgentConfiguration().partition_id
        member_id = CartridgeAgentConfiguration().member_id

        instance_maintenance_mode_event = InstanceMaintenanceModeEvent(service_name, cluster_id, network_partition_id, parition_id,
                                                          member_id)

        publisher = get_publisher(cartridgeagentconstants.INSTANCE_STATUS_TOPIC + cartridgeagentconstants.INSTANCE_MAINTENANCE_MODE_EVENT)
        publisher.publish(instance_maintenance_mode_event)

        maintenance = True
        log.info("Instance Maintenance mode event published")
    else:
        log.warn("Instance already in a Maintenance mode....")


def publish_instance_ready_to_shutdown_event():
    global ready_to_shutdown, log
    if not ready_to_shutdown:
        log.info("Publishing instance activated event")

        service_name = CartridgeAgentConfiguration().service_name
        cluster_id = CartridgeAgentConfiguration().cluster_id
        network_partition_id = CartridgeAgentConfiguration().network_partition_id
        parition_id = CartridgeAgentConfiguration().partition_id
        member_id = CartridgeAgentConfiguration().member_id

        instance_shutdown_event = InstanceReadyToShutdownEvent(service_name, cluster_id, network_partition_id, parition_id,
                                                          member_id)

        publisher = get_publisher(cartridgeagentconstants.INSTANCE_STATUS_TOPIC + cartridgeagentconstants.INSTANCE_READY_TO_SHUTDOWN_EVENT)
        publisher.publish(instance_shutdown_event)

        ready_to_shutdown = True
        log.info("Instance ReadyToShutDown event published")
    else:
        log.warn("Instance already in a ReadyToShutDown event....")


def get_publisher(topic):
    if topic not in publishers:
        publishers[topic] = EventPublisher(topic)

    return publishers[topic]


class EventPublisher:
    """
    Handles publishing events to topics to the provided message broker
    """
    def __init__(self, topic):
        self.__topic = topic

    def publish(self, event):
        mb_ip = CartridgeAgentConfiguration().read_property(cartridgeagentconstants.MB_IP)
        mb_port = CartridgeAgentConfiguration().read_property(cartridgeagentconstants.MB_PORT)
        payload = event.to_json()
        publish.single(self.__topic, payload, hostname=mb_ip, port=mb_port)