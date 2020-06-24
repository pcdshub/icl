from hutch_python.utils import safe_load
import subprocess
import sys
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, AreaDetector
from pcdsdevices.device_types import PulsePicker

import matplotlib.pyplot as plt
from time import sleep
import statistics as stat 

from pcdsdevices.device_types import IMS
from epics import PV


with safe_load('example'):
    1/0

class Proportionair(Device):
    chA = Cpt(GX_readback, ':01')
    chB = Cpt(GX_readback, ':02')

#    def __init__(self, inPressure = 0.0, inStatus=1):
#        self.pressure_setpoint = inPressure
#        self.status = inStatus
prop_a = Proportionair('CXI:SDS:PCM:A', name='prop_a')   
prop_b = Proportionair('CXI:SDS:PCM:B', name='prop_b')


class HPLC(Device):     
    status_setpoint = Cpt(EpicsSignal, ':Run')    
    status_value = Cpt(EpicsSignalRO, ':Status')
    flowrate_setpoint = Cpt(EpicsSignal, ':SetFlowRate')
    flowrate_value = Cpt(EpicsSignalRO, ':FlowRate')
    flowrate_setpoint_value = Cpt(EpicsSignalRO, ':FlowRateSP' )    
    max_pressure_setpoint = Cpt(EpicsSignal, ':SetMaxPress')    
    max_pressure = Cpt(EpicsSignalRO, ':MaxPress')
    min_pressure_setpoint = Cpt(EpicsSignal,':SetMinPress')
    min_pressure = Cpt(EpicsSignalRO,':MinPress')
    error_state = Cpt(EpicsSignalRO,':Error')
    error_process = Cpt(EpicsSignal, ':ClearError.PROC')
    

#    def __init__(self, *args, **kwargs, inFlowrate = 0.0, inStatus=1):
#        super().__init__(*args, **kwargs)
#        self.pressure_setpoint = inPressure
#        self.status = inStatus
    
    def set_flowrate_setpoint(self, inFlowrate):
        if inFlowrate >= 0.1:
            print("The units are mL/min so verify you really want this flowrate")
        if inFlowrate < 0:
            print("Stop being stupid, flowrate shouldn't be negative.  Setting the flowrate to 0")
            inFlowrate = 0
        self.flowrate_setpoint.put(inFlowrate)
        return self.flowrate_setpoint_value.get()
        
    def set_status(self, inStatus):
        self.status_setpoint.put(inStatus)
        return self.status_value.get()
    
    def set_pressure_limit(self, inLimit):
        self.limit_setpoint.put(inLimit)        
        return self.limit_value.get()
        
    def clear_error(self):
        state=self.error_process.get()
        if state==1:
            self.error_process.put(0)
        else:
            self.error_process.put(1)
        return self.error_state.get()
        
    def hplc2_resume(self):
        self.clear_error()
        self.set_status(1)
        return self.status_value.get() 

#        state=hplc2_error.get()
#        if state==1:
#            hplc2_error.put(0)
#        else:
#            hplc2_error.put(1)
#        hplc2_status=PV('CXI:LC20:SDSB:Run')
#        hplc2_status.put(1)
    
hplc_A = HPLC('CXI:LC20:SDS',name='hplc_A')
hplc_B = HPLC('CXI:LC20:SDSB',name='hplc_B')


'''
Building the selector boxes with multiple inheritances
Building blocks will be reservoirs, valves, flow meters
'''


class SelectorBoxValve(Device):
    '''
    Selector box used to switch between different samples when running aqueous samples
    
    '''
    current_position = Cpt(EpicsSignalRO,':CURR_POS')
    required_position = Cpt(EpicsSignal, ':REQ_POS')
    required_reservoir = Cpt(EpicsSignalRO, ':RES:REQ')
    
class SelectorBoxValvePair(SelectorBoxValve):
    valve01 = Cpt(SelectorBoxValve,':VLV:01')
    valve02 = Cpt(SelectorBoxValve,':VLV:02')
    
    
class SelectorBoxReservoirStates(Device):
    unit_converter = Cpt(EpicsSignalRO,':PumpUnitConverter')
    integrator_sub = Cpt(EpicsSignalRO, ':IntegratorSub')
    integrator_source_select = Cpt(EpicsSignal, ':IntegratorSrcSel')
    flow_source_select = Cpt(EpicsSignal, ':FlowSrcSelection')
    integrated_flow = Cpt(EpicsSignalRO, ':IntgFlow')
    starting_volume = Cpt(EpicsSignal, ':StartingVol')
    clear_integrated_flow = Cpt(EpicsSignal, ':ClearIntgFlow')
    clear_integrated_flow_calc = Cpt(EpicsSignal, ':ClearIntgFlowCalc')
    estimated_depletion_time = Cpt(EpicsSignal,':EstDepletionTime')

class SelectorBoxReservoir(SelectorBoxReservoirStates):
    res = Cpt(SelectorBoxReservoirStates, ':RES')    
    res1 = Cpt(SelectorBoxReservoirStates, ':RES:1')
    res2 = Cpt(SelectorBoxReservoirStates, ':RES:2')
    res3 = Cpt(SelectorBoxReservoirStates, ':RES:3')
    res4 = Cpt(SelectorBoxReservoirStates, ':RES:4')
    res5 = Cpt(SelectorBoxReservoirStates, ':RES:5')
    res6 = Cpt(SelectorBoxReservoirStates, ':RES:6')
    res7 = Cpt(SelectorBoxReservoirStates, ':RES:7')
    res8 = Cpt(SelectorBoxReservoirStates, ':RES:8')
    res9 = Cpt(SelectorBoxReservoirStates, ':RES:9')
    res10 = Cpt(SelectorBoxReservoirStates, ':RES:10')
    
class FlowMeter(Device):
    '''
    Capturing the flow meter components of the selector box
    '''
    flow_meter_mode = Cpt(EpicsSignalRO, ':FMMode')
    flow_meter_mode_readback = Cpt(EpicsSignalRO,':FMModeRb')
    flow_meter_reset = Cpt(EpicsSignal, ':FMReset')
    valid_flow = Cpt(EpicsSignalRO, ':FlowValid')
    flow_out_of_range = Cpt(EpicsSignalRO, ':FlowOor')
    measured_flow = Cpt(EpicsSignal, ':Flow')
    
    


class SelectorBox(SelectorBoxValvePair, SelectorBoxReservoir, FlowMeter):
    '''
    Making the larger Selector Box that has the reservoirs, flow meter, etc.)
    '''    
    lock = Cpt(EpicsSignal,':Lock')    
    def coupled_reservoir_switch(self,port=11):
        '''
        option is port.  Default is port 11 (water)
        '''
        if port == "Water":
            port = 11
        elif port =="water":
            port = 11
            
        self.valve01.required_position.put(port)
        self.valve02.required_position.put(port)
        time.sleep(1)
        return self.valve01.current_position.get()
        return self.valve02.current_position.get()
        
    def reservoir_prepressurize(self,port=11):
        '''
        Option is port.  Default is port 11 (water)
        '''
        curr_port = self.valve01.current_position.get()        
        for i in range(10):
            self.valve01.required_position.put(port, wait=True)
            time.sleep(2)
            self.valve01.required_position.put(curr_port, wait=True)
            time.sleep(2)
        self.valve01.required_position.put(port,wait=True)
        time.sleep(1)
        return self.valve01.current_position.get()


'''instantiate the selector box already!'''

selectorbox2 = SelectorBox('CXI:SDS:SEL2', name = 'selectorbox2')
selectorbox1 = SelectorBox('CXI:SDS:SEL1', name = 'selectorbox1')

