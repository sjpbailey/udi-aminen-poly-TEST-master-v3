

"""
Get the polyinterface objects we need. 
a different Python module which doesn't have the new LOG_HANDLER functionality
"""
import udi_interface
import sys
import time
import urllib3
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import re

"""
Some shortcuts for udi interface components

- LOGGER: to create log entries
- Custom: to access the custom data class
- ISY:    to communicate directly with the ISY (not commonly used)
"""
LOGGER = udi_interface.LOGGER
LOG_HANDLER = udi_interface.LOG_HANDLER
Custom = udi_interface.Custom
ISY = udi_interface.ISY # here it is declared atribute?

# IF you want a different log format than the current default
LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')

class AmiNemController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(AmiNemController, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = 'AMI NEM Controller'  # override what was passed in
        self.hb = 0
        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.parameterHandler)
        self.poly.subscribe(self.poly.POLL, self.poll)
        # Tell the interface we have subscribed to all the events we need.
        # Once we call ready(), the interface will start publishing data.
        self.poly.ready()
        # Tell the interface we exist.  
        self.poly.addNode(self)
        # Attributes
        self.user = None
        self.password = None
        self.isy_ip = None
        self.nem_oncor = None
        self.isy = ISY(self.poly)
        self.poly = poly

    def parameterHandler(self, params):
        self.Parameters.load(params)
        LOGGER.debug('Loading parameters now')
        self.check_params()    
    
    def start(self):
        #self.poly.updateProfile()
        self.discover()

    """class isy(udi_interface.ISY):
        def __init__(self, poly, isy):
            self.isy = ISY(self.poly)
            self.poly = poly
            isy = udi_interface.ISY()
            #pass"""

    def discover(self, *args, **kwargs):
        if self.nem_oncor is not None:
            #amiem_url = "http://" + self.isy_ip + "/rest/emeter"
            #isy = udi_interface.ISY('poly')
            amiem_resp = self.isy.cmd("/rest/emeter")
            
            #self.setDriver('GPV', 1)

            amiem_count = 0
            amiem_count1 = 0
            ustdy_count = 0
            prevs_count = 0
            sumss_count = 0

        if amiem_resp is not None:
            amiem_root = ET.fromstring(amiem_resp)

            #amiem_count = float(amiem_root('instantaneousDemand'))
            for amie in amiem_root.iter('instantaneousDemand'):
                amiem_count = float(amie.text)
                LOGGER.info("kW: " + str(amiem_count/float(self.nem_oncor)))

            #amiem_count1 = float(amiem_root.iter('instantaneousDemand'))
            for amie1 in amiem_root.iter('instantaneousDemand'):
                amiem_count1 = float(amie1.text)
                LOGGER.info("WATTS: " + str(amiem_count1))

            #ustdy_count = float(amiem_root.iter('currDayDelivered'))
            for ustd in amiem_root.iter('currDayDelivered'):
                ustdy_count = float(ustd.text)
                LOGGER.info("kWh: " + str(ustdy_count))

            #prevs_count = float(amiem_root.iter('previousDayDelivered'))
            for prev in amiem_root.iter('previousDayDelivered'):
                prevs_count = float(prev.text)
                LOGGER.info("kWh: " + str(prevs_count))

            #sumss_count = float(amiem_root.iter('currSumDelivered')#.text)
            for sums in amiem_root.iter('currSumDelivered'):
                sumss_count = float(sums.text)
                LOGGER.info("kWh: " + str(sumss_count))

    def delete(self):
        LOGGER.info('Deleting AMI NEM, Net Energy Meter')

    def stop(self):
        LOGGER.debug('AMI NEM NodeServer stopped.')

    def set_module_logs(self,level):
        LOGGER.getLogger('urllib3').setLevel(level)

    def check_params(self):
        self.Notices.clear()
        
        default_nem_oncor = "1000"
    #### All to be removed except Ip address    

        self.nem_oncor = self.Parameters.nem_oncor
        if self.nem_oncor is None:
            self.nem_oncor = default_nem_oncor
            LOGGER.error('check_params: Devisor for Oncor Meters not defined in customParams, please add it.  Using {}'.format(default_nem_oncor))
            self.nem_oncor = default_nem_oncor 
        
        # Add a notice if they need to change the user/password from the default.
        #if self.nem_oncor == default_nem_oncor:
            #self.Notices['auth'] = 'Please set your proper multiplyer currently set for Landis+Gy at 1000 set to 10000 for Oncor in configuration page'
            #pass

    def query(self, command=None):
        nodes = self.poly.getNodes()
        for node in nodes:
            nodes[node].reportDrivers()

    def poll(self, flag):
        pass
        #nodes = self.poly.getNodes()
        #for node in nodes:
        #    nodes[node].reportDrivers()
        #    self.discover()
        #if 'longPoll' in flag:
        #    LOGGER.debug('longPoll (controller)')
        #else:
        #    LOGGER.debug('shortPoll (controller)')
            

    def remove_notices_all(self,command):
        LOGGER.info('remove_notices_all: notices={}'.format(self.Notices))
        # Remove all existing notices
        self.Notices.clear()

    id = 'controller'
    
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'REMOVE_NOTICES_ALL': remove_notices_all,
    }
    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2},
        {'driver': 'GPV', 'value': 0, 'uom': 2},
        {'driver': 'CC', 'value': 0, 'uom': 30},
        {'driver': 'GV1', 'value': 0, 'uom': 73},
        {'driver': 'TPW', 'value': 0, 'uom': 33},
        {'driver': 'GV2', 'value': 0, 'uom': 33},
        {'driver': 'GV3', 'value': 0, 'uom': 33},
    ]

if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([AmiNemController])
        polyglot.start()
        control = AmiNemController(polyglot, 'controller', 'controller', 'AmiNemContoller') # 'poly', 'isy', 
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Received interrupt or exit...")
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
        polyglot.stop()
    except Exception as err:
        LOGGER.error('Excption: {0}'.format(err), exc_info=True)
    sys.exit(0)