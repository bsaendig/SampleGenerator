# coding=utf-8
# Copyright 2018 Bertram Sändig.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Copies images and label files from one folder to another if objects of classes defined by the 
'classes'-parameter are contained (Or only if they explicitely are NOT contained if the 'reverse'-parameter is set)."""

import os, glob
import numpy as np
import argparse
import json
from shutil import copy2

parser = argparse.ArgumentParser(description='Copies images and labels depending on class.')
parser.add_argument('--input_path', '--i', action='store',
                    default='../openImages/train_00',
                    help='Path to the object images.')
parser.add_argument('--out_path', '--o', action='store',
                    default='../openImages/bg',
                    help='Output path.')
parser.add_argument('--n', action='store', type = int,
                    default=4000,
                    help='Number of training images to be copied.')
parser.add_argument('--classes', '--c', nargs='+', default=[1, 2, 3], type = int,
                    help='Class-categories that are to be copied over (seperated by spaces).')
parser.add_argument('--reverse', '--r', dest='reverse', action='store_true', default=False,
                    help='Reverses the script function into only copying images without objects of the specified categories.')

args = parser.parse_args()

txt_list = sorted(glob.glob(args.input_path + "/*.txt"))
stats = {}
for c in args.classes:
  stats[c] = 0

n = 0

if not os.path.exists(args.out_path):
    os.makedirs(args.out_path)

for txt_name in txt_list:
  label_file = open(txt_name, mode = "r")
  label = label_file.read()
  label_file.close()
  copy = False
  if args.reverse:
    copy = True
  if label or args.reverse:
    for line in label.split('\n'):
      if line:
        obj_class = int(line.split(' ')[0])
        if obj_class in args.classes:
          stats[obj_class] += 1
          if args.reverse:
            copy = False
          else:
            copy = True
    if copy:
      if os.path.isfile(txt_name[:-4] + '.jpg'):
        copy2(txt_name[:-4] + '.jpg', args.out_path)
      elif os.path.isfile(txt_name[:-4] + '.png'):
        copy2(txt_name[:-4] + '.png', args.out_path)
      else:
        continue;
      copy2(txt_name, args.out_path)
      n += 1
      if n >=args.n:
        break;
  if copy and n%50==0:
    print(n, "images copied")
    if not args.reverse:
      print(stats)

if not args.reverse:
  print(stats)
