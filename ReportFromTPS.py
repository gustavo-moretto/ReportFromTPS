from tkinter import *
from tkinter import filedialog

root = Tk()

def fichatecnica(data):
    
    # Importing libraries
    import pandas as pd
    from datetime import datetime 
    import os       

    from pydicom import dcmread
    # Selecting DICOM Data
    data = dcmread(data, force=True)

    ##################################################################################
    # Extracting Basic Infos
    # Patient Name
    name  = data.PatientName
    # Patient ID
    id    = data.PatientID
    # Birth Date
    if data.PatientBirthDate != '':
      datestring = data.PatientBirthDate # extracting birth date and correcting format
      birth = datetime.strptime(datestring, '%Y%m%d').strftime("%d/%m/%Y")
    else:
      birth = '--/--/----'

    ##################################################################################
    # Extracting Plan Infos
    # Plan Name
    try:
       plan_name = data.RTPlanName
    except AttributeError:
       plan_name = 'Planejamento'
    # Description, Dose, Number of Fractions and Treatment Machine
    description = data.DoseReferenceSequence[0].DoseReferenceDescription
    target_dose = float(data.DoseReferenceSequence[0].TargetPrescriptionDose) * 100
    fractions   = int(data.FractionGroupSequence[0].NumberOfFractionsPlanned)
    machine     = data.BeamSequence[0].TreatmentMachineName

    ##################################################################################
    # Extracting Beam Infos
    # Creating some dicts to help us
    beams_data   = {}
    beam_mu_data = {}
    beam_presc   = {}
    # Extracting the numbers of Fraction Group Sequence, i.e. the number of treatment phases
    n_fractions_group = len(data.FractionGroupSequence)
    n_beams           = 0
    # Help to numbering beams
    aux_beam = 1
    # Summing n_beams to evaluate all beams
    for group in range(n_fractions_group):
      # This determines the number of beams to evaluate
      n_beams += int(data.FractionGroupSequence[group].NumberOfBeams)
      # Each Referenced Beam Sequence has info about one beam
      n_beam_sequence = int(len(data.FractionGroupSequence[group].ReferencedBeamSequence))
      # Extracting info for each beam
      for beam_sequence in range(n_beam_sequence):
        try:
          # Extracting and rounding Monitor Units
          beam_mu                      = data.FractionGroupSequence[group].ReferencedBeamSequence[beam_sequence].BeamMeterset
          beam_mu_data[str(aux_beam)]  = [round(float(beam_mu),1)]
          # Extracting treatment phase
          beam_presc[str(aux_beam)]    = [str(group+1) + 'a Fase']
        # Exception to lead with SETUP BEAM
        except AttributeError:
          beam_mu_data[str(aux_beam)]  = ['---']
          beam_presc[str(aux_beam)]    = [str(group+1) + 'a Fase']
          pass
        aux_beam += 1

    ##################################################################################
    # Extracting Beam Info (gantry, collimator, ...)
    for beam in range(n_beams):
      # Selecting just treatments beams
      # Some beams used to portal imaging are adding in this step, but remove forward
      if data.BeamSequence[beam].TreatmentDeliveryType == 'TREATMENT':
        beam_number = data.BeamSequence[beam].BeamNumber
        beam_number = beam  # using this to avoid mistakes on numering
        key         = str(beam_number + 1)
        beam_name   = data.BeamSequence[beam].BeamName
        # Checking if phase is correct for each beam
        # check_phase = input(f'{beam_name} - {beam_presc[str(beam+1)][0]} is it correct? [yes/no]: ')
        #if check_phase == 'yes':
          #pass
        #else:
          #beam_presc[str(beam+1)] = input('Please, write the correct phase: ')
        machine     = machine
        energy      = data.BeamSequence[beam].ControlPointSequence[0].NominalBeamEnergy
        # Treatment technique
        # We will extract gantry, collimator, etc, inside the beam technique, to lead with differences when we have modulated techniques
        if data.BeamSequence[beam].BeamType == 'STATIC':
          x1          = abs(float(data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDevicePositionSequence[0].LeafJawPositions[0]) / 10)
          x2          = float(data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDevicePositionSequence[0].LeafJawPositions[1]) / 10
          y1          = abs(float(data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDevicePositionSequence[1].LeafJawPositions[0]) / 10)
          y2          = float(data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDevicePositionSequence[1].LeafJawPositions[1]) / 10
          gantry      = data.BeamSequence[beam].ControlPointSequence[0].GantryAngle
          collimator  = data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDeviceAngle
          couch       = data.BeamSequence[beam].ControlPointSequence[0].PatientSupportAngle
          technique   = '3D'
          block       = '---'
        elif data.BeamSequence[beam].BeamType == 'DYNAMIC':
          x1          = '---'
          x2          = '---'
          y1          = '---'
          y2          = '---'
          if data.BeamSequence[beam].ControlPointSequence[0].GantryRotationDirection == 'NONE':
            gantry      = str(data.BeamSequence[beam].ControlPointSequence[0].GantryAngle)
            collimator  = data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDeviceAngle
            couch       = data.BeamSequence[beam].ControlPointSequence[0].PatientSupportAngle
            technique   = 'IMRT'
            block       = '---'
          else:
            gantry      = str(data.BeamSequence[beam].ControlPointSequence[0].GantryAngle) + f'({str(data.BeamSequence[beam].ControlPointSequence[0].GantryRotationDirection)})'
            collimator  = data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDeviceAngle
            couch       = data.BeamSequence[beam].ControlPointSequence[0].PatientSupportAngle
            technique   = 'VMAT'
            block       = '---'
        else:
          technique = '---'
        # Wedges
        if data.BeamSequence[beam].NumberOfWedges == '1':
          # Extracting wedge angle, type and orientation
          wedge    = str(data.BeamSequence[beam].WedgeSequence[0].WedgeAngle) + str(data.BeamSequence[beam].WedgeSequence[0].WedgeType) + str(data.BeamSequence[beam].WedgeSequence[0].WedgeOrientation)
          # Some cases we have a percentage of the field with wedge and other without (Elekta Motorized Wedge)
          # So, we will use a condition to extract correct MU values in this cases
          if data.BeamSequence[beam].WedgeSequence[0].WedgeType == 'MOTORIZED':
            wedge_mu = round(float(data.BeamSequence[beam].ControlPointSequence[1].CumulativeMetersetWeight) * beam_mu_data[str(beam+1)][0],1)
            beam_mu_data[str(beam+1)] = str(wedge_mu) + '/' + str(beam_mu_data[str(beam+1)][0])
        else:
          wedge = '---'
        # Bolus
        if data.BeamSequence[beam].NumberOfBoli == '1':
          bolus = data.BeamSequence[beam].ReferencedBolusSequence[0].BolusDescription
        else:
          bolus = '---'
        # Some cases the Source to Surface Distance needs to add manually
        ssd = ''
        try:
          ssd = round(float(data.BeamSequence[beam].ControlPointSequence[0].SourceToSurfaceDistance) / 10, 1)
          ssd = str(f'100/{ssd}')
        except AttributeError:
          ssd = "NA"      
        beams_data[key] = [machine, energy, beam_name,
                            x1, x2, y1, y2,
                            gantry, collimator, couch, wedge, bolus,
                            block, technique, ssd]
      elif data.BeamSequence[beam].TreatmentDeliveryType == 'SETUP':
        beam_number = data.BeamSequence[beam].BeamNumber
        beam_number = beam  # using this to avoid mistakes on numering
        key         = str(beam_number + 1)
        beam_name   = data.BeamSequence[beam].BeamName
        # Checking if phase is correct for each beam
        # check_phase = input(f'{beam_name} - {beam_presc[str(beam+1)][0]} is it correct? [yes/no]: ')
        #if check_phase == 'yes':
          #pass
        #else:
          #beam_presc[str(beam+1)] = input('Please, write the correct phase: ')
        machine     = machine
        energy      = data.BeamSequence[beam].ControlPointSequence[0].NominalBeamEnergy
        x1          = '---'
        x2          = '---'
        y1          = '---'
        y2          = '---'
        gantry      = data.BeamSequence[beam].ControlPointSequence[0].GantryAngle
        collimator  = data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDeviceAngle
        couch       = data.BeamSequence[beam].ControlPointSequence[0].PatientSupportAngle
        technique   = 'SETUP'
        wedge       = '---'
        bolus       = '---'
        block       = '---'
        # Some cases the Source to Surface Distance needs to add manually
        ssd = ''
        try:
          ssd = round(float(data.BeamSequence[beam].ControlPointSequence[0].SourceToSurfaceDistance) / 10, 1)
          ssd = str(f'100/{ssd}')
        except AttributeError:
          ssd = "NA"
        beams_data[key] = [machine, energy, beam_name,
                            x1, x2, y1, y2,
                            gantry, collimator, couch, wedge, bolus,
                            block, technique, ssd]
      else:
        pass

    beams_data     = pd.DataFrame.from_dict(beams_data)
    beam_mu_data   = pd.DataFrame.from_dict(beam_mu_data)
    beam_presc     = pd.DataFrame.from_dict(beam_presc)
    plan_data      = pd.concat([beams_data, beam_mu_data])
    plan_data      = pd.concat([plan_data, beam_presc]).set_index([['Equipamento', 'Energia', 'Local',
                                                                  'X1', 'X2', 'Y1', 'Y2',
                                                                  'Ang. Gantry', 'Ang. Colimador', 'Ang. Mesa', 'Filtro', 'Bólus',
                                                                  'Bloco', 'Técnica', 'DFTu/DFPe', 'MU', 'Fase']])
    final_data     = plan_data.reindex(['Técnica', 'Equipamento', 'Energia', 'Local',
                                      'X1', 'X2', 'Y1', 'Y2', 'DFTu/DFPe',
                                      'Ang. Gantry', 'Ang. Colimador', 'Ang. Mesa', 'Filtro', 'Bólus', 'Bloco', 
                                      'MU', 'Fase']).T.dropna()    
    # Select a sheet to save file
    final_data = final_data.T
    birth_save = birth.replace('/','')
    file_name = f'{plan_name}_{name}_{birth_save}_{id}'
    file_name = filedialog.asksaveasfilename(filetypes=[('excel file', '*.xlsx')], defaultextension='.xlsx', title = "Salvar dados extraídos", initialfile=file_name)
    final_data.to_excel(f'{file_name}.xlsx')   

    #####################################################################
    # Opening save sheet
    # os.path.realpath(f'{file_name}.xlsx', 'r')

# Function to select a DICOMRT file
def openFile():
        filepath = filedialog.askopenfilename()
        # data = path of selected file
        data = filepath
        fichatecnica(data)  

# Creating an widget to the app
class Application():
    def __init__(self):
        self.root = root
        self.screen()
        self.buttons()
        root.mainloop()
    
    def screen(self):
        self.root.title("DicomRT Extractor")        
        self.root.geometry("300x150")
        self.root.resizable(False, False)
        
    def buttons(self):
        self.button = Button(text="Selecione o arquivo DICOMRT",
                             command = openFile)
        self.button.place(relx=0.15, rely=0.25, relwidth=0.75, relheight=0.25)

Application()