#!/usr/bin/python3
"""
Builds the ini file for the Experiment Program

usage: Builder.py

Copyright: NeuRA
Author: James Cheetham
Date: 20180124
Last Modified: 20181024
"""

import os, sys
from configparser import ConfigParser

def input_prompt(prompt, valid_options=None):
  """
  :param prompt: The prompt to display
  :param valid_options: array: Possible values that can be entered
  :return: Entered Data or valid option selected
  """
  while True:
    if valid_options is None:
      user_input = input('%s: ' % prompt)
    else:
      user_input = input('%s [%s]: ' % (prompt, '/'.join(valid_options)))
    if user_input.lower() == 'q':
      sys.exit()
    if valid_options is not None:
      for o in valid_options:
        if o.lower() == user_input.lower():
          return o
      print('Please enter a valid option')
    else:
      return user_input

def main():
  """
  :return: None
  Uses Config Parser to create an ini file based on user input
  """
  config = ConfigParser()
  print('Staircase Experiment Setup')
  experiment_name = input_prompt('Experiment Name')
  config.add_section('Experiment')
  config.add_section('Staircase Default')
  config.set('Experiment', 'Name', experiment_name)
  while True:
    save_path = input_prompt('Save Data Directory')
    if os.path.isfile(save_path):
      print('The selected path (%s) is a file. Please enter a path that does not exist, or is a directory' % save_path)
    elif not os.path.exists(save_path):
      try:
        os.makedirs(save_path)
        break
      except PermissionError:
        print('Unable to create the directory %s. Please try again' % save_path)
    else:
      break
  ini_file = experiment_name.lower().replace(' ', '_')
  if save_path[-1] == '/':
    ini_filename = '%s/%s.ini' % (os.path.dirname(save_path[:-1]), ini_file)
  else:
    ini_filename = '%s/%s.ini' % (os.path.dirname(save_path), ini_file)
  config.set('Experiment', 'Path', save_path)
  while True:
    tmp_input = input_prompt('Number of Staircases')
    try:
      staircase_count = int(tmp_input)
      if staircase_count < 1:
        print('Please enter a valid number of Staircases (greater than 0)')
      else:
        break
    except ValueError:
      print('Please enter a numeric value')
  config.set('Experiment', 'Staircase Count', str(staircase_count))
  unit_descriptor = input_prompt('Unit Descriptor (e.g. gram, millimetre)')
  config.set('Staircase Default', 'Units', unit_descriptor)
  # unit_type = input_prompt('Please enter the Unit Type', ['Linear', 'Logarithmic'])
  unit_type = 'Linear'
  config.set('Staircase Default', 'Unit Type', unit_type)
  comparison_descriptor = input_prompt('Greater Value in Unit Descriptor (e.g. Heavier, Thicker)')
  config.set('Staircase Default', 'Comparison Descriptor', comparison_descriptor)
  while True:
    tmp_input = input_prompt('Number of Correct Trials to Increase Difficulty')
    try:
      reversal_correct_count = int(tmp_input)
      break
    except ValueError:
      print('Please enter a numeric value')
  config.set('Staircase Default', 'Reversal Correct Count', str(reversal_correct_count))
  while True:
    tmp_input = input_prompt('Difficulty Increase Step Size (%s)' % unit_descriptor)
    try:
      harder_step = float(tmp_input)
      break
    except ValueError:
      print('Please enter a numeric value')
  config.set('Staircase Default', 'Harder Step', str(harder_step))
  while True:
    tmp_input = input_prompt('Difficulty Decrease Step Size (%s)' % unit_descriptor)
    try:
      easier_step = float(tmp_input)
      break
    except ValueError:
      print('Please enter a numeric value')
  config.set('Staircase Default', 'Easier Step', str(easier_step))
  while True:
    tmp_input = input_prompt('Reference Value')
    try:
      reference = float(tmp_input)
      break
    except ValueError:
      print('Please enter a numeric value')
  config.set('Staircase Default', 'Reference', str(reference))
  if staircase_count > 1:
    swap_option = input_prompt('Staircase Swap Criteria', ['Alternate', 'Random', 'Serial'])
    config.set('Experiment', 'Staircase Swap Criteria', swap_option)
  # floor_rule = input_prompt('Please select the Floor Rule', ['Carry On', 'Truncation'])
  floor_rule = 'Carry On'
  config.set('Staircase Default', 'Floor Rule', floor_rule)
  # end_criteria = input_prompt('Please select the End Criteria', ['Reversals', 'Other'])
  end_criteria = 'Reversals'
  config.set('Staircase Default', 'End Criteria', end_criteria)
  if end_criteria == 'Reversals':
    while True:
      tmp_input = input_prompt('Reversals Count to end the Staircase')
      try:
        reversal_experiment_end = int(tmp_input)
        break
      except ValueError:
        print('PLease enter a numeric value')
    config.set('Staircase Default', 'end criteria reversals', str(reversal_experiment_end))
  initial_setup = input_prompt('Only Start Staircase rule after first error?', ['Y', 'N'])
  config.set('Staircase Default', 'Initial Setup', initial_setup)

  for i in range(staircase_count):
    section_name = 'Staircase %d' % (i+1)
    config.add_section(section_name)
    while True:
      tmp_input = input_prompt('Please enter the Initial Test Value for Staircase %d' % (i+1))
      try:
        initial_value = float(tmp_input)
        break
      except ValueError:
        print('Please enter a numeric value')
    config.set(section_name, 'Start Value', str(initial_value))

  with open(ini_filename, 'w') as f:
    config.write(f)

  
if __name__ == '__main__':
  main()