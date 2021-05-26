import os
import numpy as np
import matplotlib.pyplot as plt
from igor import packed 

class Read_Experiment(object):
    # Class for holding sutterpatch experiment data
    
    def __init__(self, pxp_file_path):
        if os.path.exists(pxp_file_path):  # Check if file paths and filenames exists
            self.pxp_file_path = pxp_file_path
        elif os.path.exists(pxp_file_path + '.pxp'):  # see if .ibt extension was left off
            self.pxp_file_path = pxp_file_path + '.pxp'
        else:
            raise ValueError("PXP file does not exist: %s" % pxp_file_path)

        self.name = os.path.splitext(os.path.basename(self.pxp_file_path))[0]
        
        pxp_file = packed.load(pxp_file_path)
        
        self.routines = self.extract_routines(pxp_file)
        
        # add code to check if valid sutterpatch pxp file 
    
    def extract_routines(self, pxp_file):
        routines = []
        routine_dict = pxp_file[1]['root'][b'SutterPatch'][b'Data']
        # remove non-routine waves
        routine_dict.pop(b'Analysis')
        routine_dict.pop(b'Meta')
        routine_dict.pop(b'Routines')
        routine_dict.pop(b'Images')
        routine_dict.pop(b'ExperimentStructure')
        
        # Get Routine Numbers
        routine_nums = []
        for k in routine_dict.keys():
            key = k.decode()
            try:
                routine_nums.append(int(key.split('_', 1)[0].split('R')[1]))   
            except:
                pass
        routine_nums = np.unique(routine_nums)

        # extract waves for each routine
        
        for routine_num in routine_nums:
            waves = [v for k, v in routine_dict.items() if 'R' + str(routine_num) + '_' in k.decode()]
            routines.append(Routine(waves, self))
            
        return routines
        
    
    def parse_metadata(pxp_file):
        pass # Under construction

class Routine(object):
    # Class for storing sutterpatch routines
    
    def __init__(self, waveRecords, experiment):
        self.experiment = experiment.name # Experiment routine was a part of
        self.routine_num = int(waveRecords[0].wave['wave']['wave_header']['bname'].decode().split('_', 1)[0].split('R')[1])
        self.routine_name = waveRecords[0].wave['wave']['wave_header']['bname'].decode().split('_', 2)[-1]
                            
        self.mode = [] # current clamp or voltage clamp
        self.meta_data = [] # experiment meta_data
        self.dx = waveRecords[0].wave['wave']['wave_header']['sfA'][0]
        self.sweep_len = waveRecords[0].wave['wave']['wave_header']['nDim'][0]
        self.num_sweeps = waveRecords[0].wave['wave']['wave_header']['nDim'][1]        
        self.sweeps = []
        for i in range(self.num_sweeps):
            sweep_dict = {}

            for waveRecord in waveRecords:
                unit = waveRecord.wave['wave']['wave_header']['dataUnits'][0].decode()
                sweep_dict[unit] = waveRecord.wave['wave']['wData'].T[i]
            self.sweeps.append(Sweep(sweep_dict, self, i))

class Sweep(object):
    
    def __init__(self, sweep_dict, routine, sweep_num):
        self.experiment = routine.experiment
        self.routine_num = int(routine.routine_num)
        self.routine_name = routine.routine_name
        self.sweep_num = int(sweep_num)
        self.dx = routine.dx
        self.num_points = routine.sweep_len
        self.time = np.arange(0, self.num_points) * self.dx
        
        self.data = {}
        for k, v in sweep_dict.items():
            self.data[k] = v