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
"""Creates a json info file containing classes and aspect-ratios of rendered object-images."""

import os, glob
import numpy as np
import argparse
import json

parser = argparse.ArgumentParser(description='Write a class_info file with image names for each class and ratio.')
parser.add_argument('--input_path', '--i', action='store',
                    default='../scenes/samples/train/rgba',
                    help='Path to the object images.')
parser.add_argument('--out_path', '--o', action='store',
                    default='../scenes/samples/train/obj_info.json',
                    help='Output path for the object info json file.')

args = parser.parse_args()

img_list = sorted(glob.glob(args.input_path + "/*.png"))

info = {}

for img_name in img_list:
  img_label_file = open(img_name[:-4] + '.txt', mode = "r")
  label = img_label_file.read()
  if label:
    obj_class, x_c, y_c, w, h = map(float, label.split(' '))
    obj_class = int(obj_class)
    if w >= h:
      ratio = h/w
    else:
      ratio = -w/h
    if obj_class in info:
      if round(ratio,1) in info[obj_class]:
        info[obj_class][round(ratio,1)].append({'img': img_name.split('/')[-1], 'center_x': x_c, 'center_y': y_c, 'width': w, 'height': h})
      else:
        info[obj_class][round(ratio,1)] = [{'img': img_name.split('/')[-1], 'center_x': x_c, 'center_y': y_c, 'width': w, 'height': h}]
    else:
      info[obj_class] = {round(ratio,1): [{'img': img_name.split('/')[-1], 'center_x': x_c, 'center_y': y_c, 'width': w, 'height': h}]}
    img_label_file.close()

for k in info:
  ratios = 'ratios: '
  for l in sorted(info[k]):
    ratios += '{}: {}; '.format(l,len(info[k][l]))
  print('class {} {}'.format(k,ratios))
  

with open(args.out_path, 'w') as outfile:
    json.dump(info, outfile)
