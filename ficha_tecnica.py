# Importing libraries
import pandas as pd
from datetime import datetime

from pydicom import *

# Selecting DICOM Data
data = dcmread('C:\\Users\\User\\Documents\\repos\\ficha_tecnica_blumenau\\testing_files\\RP.729634.REPLAN.dcm')
##################################################################################
# Extracting Basic Infos
# Patient Name
name  = data.PatientName
# Patient ID
id    = data.PatientID
# Birth Date
datestring = data.PatientBirthDate # extracting birth date and correcting format
birth = datetime.strptime(datestring, '%Y%m%d').strftime("%d/%m/%Y")

##################################################################################
# Extracting Plan Infos
# Plan Name
plan_name = data.RTPlanName
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
      beam_presc[str(aux_beam)]    = [str(group+1) + 'a Phase']
    # Exception to lead with SETUP BEAM
    except AttributeError:
      beam_mu_data[str(aux_beam)]  = ['---']
      beam_presc[str(aux_beam)]    = [str(group+1) + 'a Phase']
      pass
    aux_beam += 1

##################################################################################
# Extracting Beam Info (gantry, collimator, ...)
for beam in range(n_beams):
  # Acessing each beam to collect infos
  beam_number = data.BeamSequence[beam].BeamNumber
  beam_number = beam # using this to avoid mistakes on numering
  key         = str(beam_number+1)
  beam_name   = data.BeamSequence[beam].BeamName

  gantry      = data.BeamSequence[beam].ControlPointSequence[0].GantryAngle
  collimator  = data.BeamSequence[beam].ControlPointSequence[0].BeamLimitingDeviceAngle
  couch       = data.BeamSequence[beam].ControlPointSequence[0].PatientSupportAngle
  try:
    ssd       = round(float(data.BeamSequence[beam].ControlPointSequence[0].SourceToSurfaceDistance) / 10,1)
  except AttributeError:
    ssd       = input(f"Input SSD for Beam Data {beam_name, gantry, collimator, couch, ssd}: ")
  beams_data[key] = [beam_name, gantry, collimator, couch, ssd]