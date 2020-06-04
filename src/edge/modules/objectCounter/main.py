# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import asyncio
import json
from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

class ModuleObjectCounter:

    def __init__(self):
        self.object_tag = ''
        self.object_confidence = 0


    async def main(self):
        try:
            if not sys.version >= "3.5.3":
                raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
            print ( "IoT Hub Client for Python" )

            # The client object is used to interact with your Azure IoT hub.
            module_client = IoTHubModuleClient.create_from_edge_environment()

            # connect the client.
            await module_client.connect()

            # define behavior for receiving an input message on input1
            async def count_objects_listener(module_client):
                while True:
                    input_message = await module_client.receive_message_on_input("detectedObjects")  # blocking call
                    
                    count = 0
                    detected_objects = input_message.custom_properties['inferences']

                    if detected_objects is not None:
                        for inference in detected_objects:
                            entity = inference['entity']
                            tag = entity['tag']

                            if (tag["value"] == self.object_tag) and (tag["confidence"] > self.object_confidence):
                                count += 1
                    
                    if count > 0:
                        output_message_string = json.dumps(dict({'count': count}))

                    output_message = Message(output_message_string)
                    
                    subject = input_message.custom_properties['subject']
                    graph_instance_signature = '/graphInstances/'

                    if graph_instance_signature in subject:
                        # CSharp sample version is doing nothing with this, so does this Python port (must it?)
                        graph_instance_name = subject.split('/')[2]
                        #
                        output_message.custom_properties['eventTime'] = input_message.custom_properties['eventTime']
                        await module_client.send_message_to_output(output_message, "objectCountTrigger")

            
            # define behavior for halting the application
            def stdin_listener(self):
                while True:
                    try:
                        selection = input("Press Q to quit\n")
                        if selection == "Q" or selection == "q":
                            print("Quitting...")
                            break
                    except:
                        time.sleep(10)


            # Schedule task for C2D Listener
            listeners = asyncio.gather(count_objects_listener(module_client))

            print ( "The sample is now waiting for messages. ")

            # Run the stdin listener in the event loop
            loop = asyncio.get_event_loop()
            user_finished = loop.run_in_executor(None, stdin_listener)

            # Wait for user to indicate they are done listening for messages
            await user_finished

            # Cancel listening
            listeners.cancel()

            # Finally, disconnect
            await module_client.disconnect()

        except Exception as e:
            print ( "Unexpected error %s " % e )
            raise

if __name__ == "__main__":
    module = ModuleObjectCounter()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(module.main())
    loop.close()

    # If using Python 3.7 or above, you can use following code instead:
    # asyncio.run(main())