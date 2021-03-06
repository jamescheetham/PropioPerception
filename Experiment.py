#!/usr/bin/python3
"""
This code is designed to run a Staircase Experiment for Psychophysics. It will read the experiment setup from the
supplied ini file.

Experiment.py -c <ini_file>

Copyright: NeuRA
Author: James Cheetham
Last Modified By: James Cheetham
Last Modified On: 20180124

"""

from configparser import ConfigParser
from configparser import NoOptionError, NoSectionError
from optparse import OptionParser
import os, sys, random, csv
import matplotlib.pyplot as plt
from datetime import datetime

class Experiment:
  """
  The Experiment Class controls the entire experiment and contains the details of the individual staircases.
  After each step, it will determine the next staircase to be run
  """
  def __init__(self, config_file):
    self.config_file = config_file
    self.config = ConfigParser()
    self.config.read(self.config_file)
    self.name = ''
    self.data_path = ''
    self.swap_criteria = ''
    self.staircases = []
    self.open_staircases = []
    self.end_time = None
    self.staircase_count = 0
    self.process_config()
    self.subject = Subject(self.data_path)
    self.start_time = datetime.now()
    self.last_staircase = None

  def process_config(self):
    """
    :return: None
    Reads the ini file for the Experiment Setup as well as creates the staircases
    """
    self.name = self.config.get('Experiment', 'name')
    self.data_path = self.config.get('Experiment', 'path')
    self.swap_criteria = self.config.get('Experiment', 'staircase swap criteria')
    self.staircase_count = self.config.getint('Experiment', 'staircase count')

    for i in range(self.staircase_count):
      self.staircases.append(Staircase(self.config, i+1))
      self.open_staircases.append(self.staircases[-1])

  def run(self):
    """
    :return: Boolean: True if the experiement completed normally, False if the user terminated it early
    Runs the Experiment, it will continue until all of the supplied staircases
    """
    current_staircase = None
    while self.has_open_staircases():
      self.last_staircase = current_staircase
      current_staircase = self.next_staircase(current_staircase)
      result = current_staircase.run(self.last_staircase is not None)
      # Staircase.run returns True or False if the correct sample was chosen, 'Backtrack' to reanswer
      # the old question, or 'q' if the operator wants to stop the Experiment
      if result == True:
        if current_staircase.is_finished:
          self.open_staircases.remove(current_staircase)
      elif result == 'Backtrack':
        # Backtrack is a special option that allows the previous answer to be reselected
        self.undo_last_answer()
      else:
        for s in self.open_staircases:
          s.is_finished = True
        self.open_staircases = []
        self.end_time = datetime.now()
        return False
    self.end_time = datetime.now()
    return True

  def has_open_staircases(self):
    """
    Checks to see if there are currently open staircases
    :return: Boolean
    """
    return len(self.open_staircases) > 0

  def undo_last_answer(self):
    """
    Will undo the last answer and present a backtrack option
    :return:
    """
    if self.last_staircase.is_finished:
      self.last_staircase.is_finished = False
      self.open_staircases.append(self.last_staircase)
    self.last_staircase.backtrack()

  def finish_experiement(self):
    """
    Writes the results to disk and produces a plot of the answer
    :return:
    """
    self.write_results()
    self.produce_plot()

  def write_results(self):
    """
    :return: None
    Creates the necessary output directories and writes each Staircase to a separate file
    """
    base_dir = '%s/%s' % (self.data_path, self.subject.name.replace(' ', '_'))
    base_dir = base_dir.replace('//', '/')
    if not os.path.isdir(base_dir):
      os.makedirs(base_dir)
    for s in self.staircases:
      s.write_results(base_dir, self.subject.name, self.start_time, self.end_time, self.config)

  def produce_plot(self):
    """
    :return: None
    Produces a plot of containing the results for each staircase
    """
    fig = plt.figure(figsize=(10, 5*self.staircase_count))
    for i in range(self.staircase_count):
      s = self.staircases[i]
      subplot = fig.add_subplot(self.staircase_count, 1, i+1)
      s.produce_plot(subplot)
    fig.tight_layout()
    fig.savefig('%s/%s/%s_results.png' % (self.data_path, self.subject.name.replace(' ', '_'), self.subject.name.replace(' ', '_')))

  def next_staircase(self, current_staircase=None):
    """
    :param current_staircase:
    :return: The next Staircase
    There are three options for switching between Staircases
    Random: The next staircase is random from the available pool
    Serial: One is run to completion, before the next is started
    Alternate: The staircases is changed after every option
    """
    if current_staircase is None:
      return self.open_staircases[0]
    if self.swap_criteria == 'Serial':
      if current_staircase is None or current_staircase.is_finished:
        return self.open_staircases[0]
    elif self.swap_criteria == 'Alternate':
      # if the current staircase is complete and not in the list of open_staircases
      # The first staircase from the list will be chosen
      try:
        current_index = self.open_staircases.index(current_staircase)
      except ValueError:
        return self.open_staircases[0]
      if current_index+1 == len(self.open_staircases):
        return self.open_staircases[0]
      else:
        return self.open_staircases[current_index+1]
    elif self.swap_criteria == 'Random':
      return random.choice(self.open_staircases)


class Staircase:
  """
  This class contains the information for the Staircase Experiment. It loads it's information from the
  ini file pulling it from the Staircase Default option as well as from the specified Staircase section
  """
  def __init__(self, config, number):
    self.name = 'Staircase %d' % number
    self.units = config.get('Staircase Default', 'units')
    self.unit_type = config.get('Staircase Default', 'unit type')
    self.comparision_descriptor = config.get('Staircase Default', 'comparison descriptor')
    self.harder_step = config.getfloat('Staircase Default', 'harder step')
    self.easier_step = config.getfloat('Staircase Default', 'easier step')
    self.target = config.getfloat('Staircase Default', 'reference')
    self.floor_rule = config.get('Staircase Default', 'floor rule')
    self.end_criteria = config.get('Staircase Default', 'end criteria')
    self.start_value = config.getfloat(self.name, 'start value')
    self.run_initial_setup = config.get('Staircase Default', 'initial setup')
    self.correct_reverse_count = config.getint('Staircase Default', 'reversal correct count')
    self.end_criteria_reversals = config.getint('Staircase Default', 'end criteria reversals')
    self.initial_setup = config.get('Staircase Default', 'initial setup')
    self.is_finished = False
    self.current_sample = self.start_value
    self.correct_count = 0
    self.test_count = 0
    self.reversal_count = 0
    self.results = []
    self.current_direction = None
    self.last_sample = None

    if self.target < self.start_value:
      self.harder_step *= -1
      self.easier_step *= -1

  def write_results(self, path, subject_name, expr_start_time, expr_end_time, config):
    """
    :param path: The directory to write the file to
    :param subject_name: The name of the test subject
    :param expr_start_time: The time that the experiement was started
    :param expr_end_time: The time that the experiment was concluded
    :return: None
    Writes the restult set to the results file
    """
    file_name = '%s/%s_%s_results.csv' % (path, subject_name.replace(' ', '_'), self.name.replace(' ', '_'))
    with open(file_name, 'w') as f:
      csv_writer = csv.writer(f, delimiter=',', quotechar='"')
      csv_writer.writerow(['Reference Weight', 'Test Weight', 'Ref Presented First', 'Correct', 'Reversal'])
      for r in self.results:
        r.write_results(csv_writer)
      csv_writer.writerow([])
      csv_writer.writerow(['Start Time', expr_start_time.strftime('%H:%M:%S'), expr_start_time.strftime('%d/%m/%Y')])
      csv_writer.writerow(['End Time', expr_end_time.strftime('%H:%M:%S'), expr_end_time.strftime('%d/%m/%Y')])
      run_time = expr_end_time - expr_start_time
      csv_writer.writerow(['Experiment Time (min)', '%d:%02d' % (run_time.seconds/60, run_time.seconds%60)])
      csv_writer.writerow([])
      csv_writer.writerow(['Config'])
      for s in ['Experiment', 'Staircase Default', self.name]:
        csv_writer.writerow([s])
        for o in config.options(s):
          csv_writer.writerow([o, config.get(s, o)])
        csv_writer.writerow([])

  def produce_plot(self, subplot):
    """
    :param subplot: The subplot to populate with the results
    :return: None
    Plots the Results Set on to the supplied subplot
    """
    subplot.set_ylabel('Test Sample (%s)' % self.units)
    subplot.set_xlabel('Test Count')
    last_result = None
    for r in self.results:
      if r.correct:
        if r.reversal:
          subplot.plot(r.sample_num + 1, r.test_sample, 'ks', markersize=6)
        else:
          subplot.plot(r.sample_num + 1, r.test_sample, 'ko', markersize=6)
      else:
        if r.reversal:
          subplot.plot(r.sample_num + 1, r.test_sample, 'ks', markerfacecolor='w', markersize=6)
        else:
          subplot.plot(r.sample_num + 1, r.test_sample, 'ko', markerfacecolor='w', markersize=6)
      if last_result is not None:
        subplot.plot([r.sample_num + 1, last_result.sample_num + 1], [r.test_sample, last_result.test_sample], 'k-')
      last_result = r
    if self.start_value < self.target:
      subplot.set_ylim(self.start_value-10, self.target+10)
    else:
      subplot.set_ylim(self.target-10, self.start_value+10)
    subplot.set_xlim(1, len(self.results) + 1)
    subplot.locator_params('x', None, integer=True)

  def get_next_sample(self, last_correct):
    """
    :param last_correct: Boolean, status of the last Test
    :return: return_value: tuple of booleans [0] whether a reversal occured, [1] whether the test sample changed
    Updates the status of the staircase based on the previous result
    """
    direction = None
    return_value = [False, False]
    if last_correct:
      self.correct_count += 1
      if self.initial_setup == 'Y' and self.reversal_count == 0:
        self.calc_next_sample('closer')
        direction = 'closer'
        return_value[1] = True
      elif self.correct_count == self.correct_reverse_count:
        # Resets the Correct Count due to meeting the criteria to increase the difficulty of the test
        self.calc_next_sample('closer')
        direction = 'closer'
        return_value[1] = True
        self.correct_count = 0
    else:
      if self.test_count == 0 and self.initial_setup == 'Y':
        self.initial_setup = 'N'
      self.calc_next_sample('further')
      direction = 'further'
      return_value[1] = True
      self.correct_count = 0
    if self.last_sample is not None and self.last_sample != self.current_sample and self.current_direction is not None and self.current_direction != direction:
      self.reversal_count += 1
      return_value[0] = True
    if self.current_direction is None or (self.last_sample != self.current_sample and self.current_direction != direction):
      self.current_direction = direction
    self.last_sample = self.current_sample
    return return_value

  def calc_next_sample(self, direction):
    """
    :param direction:
    :return: None
    Calculates the next sample based on whether it should be closer or further from the sample
    """
    if direction == 'closer':
      self.current_sample += self.harder_step
    elif direction == 'further':
      self.current_sample -= self.easier_step

    # If the current_sample is beyond the initial value, or is the same as the reference sample
    # Then it will set the current_sample to those values accordingly.
    if self.start_value < self.target <= self.current_sample:
      self.current_sample = self.target - abs(self.harder_step)
    elif self.start_value > self.target >= self.current_sample:
      self.current_sample = self.target + abs(self.harder_step)
    elif (self.target > self.start_value > self.current_sample) or \
            (self.target < self.start_value < self.current_sample):
      self.current_sample = self.start_value

  def run(self, allow_backtrack=True):
    """
    :param allow_backtrack: Boolean, whether the operator can enter '<' as the result to reanswer the previous question
    :return: Mixed: True is a successful run, or the entered value (< or q)
    The first choice presented to the test subject is calculated randomly and the operator is asked to enter which
    was the higher of the two values.
    """
    choices = [self.current_sample, self.target]
    choice1 = random.choice(choices)
    choice2 = choices[0] if choices.index(choice1) == 1 else choices[1]
    self.present_choices(choice1, choice2)
    while True:
      selected_choice = self.read_choice(choice1, choice2, allow_backtrack)
      if selected_choice in choices:
        break
      else:
        if selected_choice == False:
          answer = input('Do you wish to Terminate the Experiement early and write the results to disk? [y/N] ')
          if answer.lower() == 'y':
            return selected_choice
        else:
          return selected_choice

    correct = self.check_correct(selected_choice, self.target, self.current_sample)
    self.results.append(ResultSet(self.target, self.current_sample, choice1, self.test_count, correct, self.current_direction, self.get_next_sample(correct)))
    self.test_count += 1

    self.determine_is_finished()
    return True

  def present_choices(self, choice1, choice2, backtrack=False):
    """
    :param choice1: The first choice to present to the test subject
    :param choice2:  The second choice to present to the test subject
    :param backtrack: Whether this is asking the operator to renter the value of a previous test.
    :return: None
    Displays the text to the operator telling which sample to present to the subject first. It will display
    the Test Number and whether this is a backtracked question.
    """
    if backtrack:
      print('\nBacktraced Test for %s - Test %d\n' % (self.name, self.test_count))
    else:
      print('\nTest for %s - Test %d\n' % (self.name, self.test_count + 1))
    if choice1.is_integer:
      print('Option 1: %d %s' % (choice1, self.units))
    else:
      print('Option 1: %0.2f %s' % (choice1, self.units))
    if choice2.is_integer:
      print('Option 2: %d %s' % (choice2, self.units))
    else:
      print('Option 2: %0.2f %s' % (choice2, self.units))

  def read_choice(self, choice1, choice2, allow_backtrack=False):
    """
    :param choice1: The first option
    :param choice2: The second option
    :param allow_backtrack: Whether < is an allowed option to let the operator reanswer the last question.
    :return: The choosen option
    Prompts the user to enter which of the two samples was the higher option and return that value
    """
    while True:
      greater = input('\nWhich was %s [1/2]: ' % self.comparision_descriptor)
      if greater.lower() == 'q':
        return False
      if allow_backtrack and greater.lower() == '<':
        return 'Backtrack'
      if greater in ['1', '2']:
        break
      print('Invalid Choice')
    if greater == '1':
      return choice1
    else:
      return choice2

  @staticmethod
  def check_correct(selected_choice, target, sample):
    """
    :param selected_choice: The chosen value
    :param target: The Target Value
    :param sample: The Sample Value
    :return: Boolean, whether the correct value was chosen
    Determines if the higher sample was choosen.
    """
    if selected_choice == target and target > sample:
      return True
    elif selected_choice == sample and sample > target:
      return True
    else:
      return False

  def backtrack(self):
    """
    :return: None or the entered value
    Prompts the Operator for the previous test again allowing them to change their answer.
    """
    last_result = self.results[-1]
    if last_result is None:
      return
    # Reads the Last Result setup and ensures that it's represented the same
    if last_result.presented_first == last_result.target:
      choice1 = last_result.target
      choice2 = last_result.test_sample
    else:
      choice1 = last_result.test_sample
      choice2 = last_result.target
    self.present_choices(choice1, choice2, True)
    selected_choice = self.read_choice(choice1, choice2)

    if selected_choice not in [choice1, choice2]:
      return selected_choice

    correct = self.check_correct(selected_choice, last_result.target, last_result.test_sample)

    # Remove the last result as it will need to be replaced
    self.results.pop()

    new_result = ResultSet(self.target, last_result.test_sample, choice1, last_result.sample_num, correct)
    if last_result.correct != new_result.correct:
      # If the previous answer differs from the new answer it is necessary to recalculate
      # The current position by reprocessing all of the previous answers
      correct_count = 0
      reversal_count = 0
      last_sample = 0
      for r in self.results:
        # Loop through existing results to recalculate the current position with the new answer
        last_sample = r.test_sample
        if r.reversal:
          reversal_count += 1
        if r.correct:
          correct_count += 1
          if (self.initial_setup != 'Y' or reversal_count != 0) and correct_count == self.correct_reverse_count:
            # Reset correct_count if the subject has met the criteria to increase difficulty
            correct_count = 0
        else:
          # subject answered incorrectly, reset the correct_count
          correct_count = 0
      # Reset the correct_count and reversal_count for the staircase
      self.correct_count = correct_count
      self.reversal_count = reversal_count
      self.last_sample = last_sample
    else:
      self.results.append(last_result)
      return
    # Update the state of the staircase with the new information
    if last_result.sample_num == 0:
      self.initial_setup = self.run_initial_setup
    self.current_direction = last_result.current_direction
    self.current_sample = last_result.test_sample
    self.test_count = last_result.sample_num
    self.last_sample = last_result.test_sample
    new_result_data = self.get_next_sample(correct)
    self.test_count += 1
    new_result.reversal = new_result_data[0]
    new_result.test_sample_change = new_result_data[1]
    new_result.current_direction = self.current_direction
    self.determine_is_finished()
    self.results.append(new_result)

  def determine_is_finished(self):
    """
    :return: None
    Determines if the staircase has reached the completion criteria (number of reversals)
    """
    if self.reversal_count == self.end_criteria_reversals:
      self.is_finished = True

  def __eq__(self, other):
    return self.name == other.name

class Subject:
  """
  Class to hold the subjects detail.
  """
  def __init__(self, data_path):
    """
    Prompts the operator for an identifier for the current test subject. The name must not exist as an existing folder
    under the data_path directory
    :param data_path: the base path to save the subjects data in
    """
    while True:
      self.name = input('Please enter a Subject identifier: ')
      if not os.path.exists('%s/%s' % (data_path, self.name.replace(' ', '_'))):
        break
      print('There is already a Data Directory for this Subject Identifier')

class ResultSet:
  """
  Holds the result from a Test. Stores the Target, Test Sample, which was presented first, Test Number and
  whether the subject answered correctly
  """
  def __init__(self, target, test_sample, presented_first, sample_num, correct, current_direction=None, next_sample_data=None):
    self.target = target
    self.test_sample = test_sample
    self.presented_first = presented_first
    self.sample_num = sample_num
    self.correct = correct
    self.current_direction = current_direction
    if next_sample_data is not None:
      self.reversal = next_sample_data[0]
      self.test_sample_change = next_sample_data[1]

  def write_results(self, csv_writer):
    """
    :param csv_writer: The CSV Writer Object
    :return: None
    Writes the data to file
    """
    output = [int(self.target) if self.target.is_integer else self.target,
              int(self.test_sample) if self.test_sample.is_integer() else self.test_sample,
              1 if self.presented_first == self.target else 2,
              'Y' if self.correct else 'N',
              1 if self.reversal else 0]
    csv_writer.writerow(output)

  def __str__(self):
    if self.target.is_integer():
      return '%d to %d: %s' % (self.target, self.test_sample, self.correct)
    else:
      return '%0.2f to %0.2f: %s' % (self.target, self.test_sample, self.correct)

def main():
  """
  :return:
  Reads the name of the ini file from passed parameter (-c or --config) and runs the Experiment
  """
  parser = OptionParser()
  parser.add_option('-c', '--config', dest='config_file', action='store', type='str')
  opt, arg = parser.parse_args()
  if opt.config_file is None:
    parser.error('Please enter enter a config file')
  if not os.path.isfile(opt.config_file):
    parser.error('The selected config file (%s) does not exist or is not a file' % opt.config_file)

  try:
    # Ensures that the config file contains the relevant information
    exp = Experiment(opt.config_file)
  except (NoOptionError, NoSectionError):
    print('There was a problem processing the Config File')
    sys.exit(1)
  while exp.has_open_staircases():
    if exp.run():
      answer = input('Do you wish to end the Experiement? [Y/n] ')
      if answer.lower() == 'n':
        exp.undo_last_answer()
  exp.finish_experiement()

if __name__ == '__main__':
  main()