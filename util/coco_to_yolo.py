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
"""Creates Yolo style label files for the coco data set. Requires pycocotools."""

import json
from PIL import Image
import os, glob
import numpy as np
import argparse
from pycocotools.coco import COCO

parser = argparse.ArgumentParser(description='Create yolo-style label files from COCO training data.')
parser.add_argument('--input_file', '--i', action='store',
                    default='../coco/annotations/instances_train2017.json',
                    help='Path to annotations file.')
parser.add_argument('--output_path', '--o', action='store',
                    default='../coco/train2017',
                    help='Path to output folder.')

args = parser.parse_args()

coco=COCO(args.input_file)
imgIds = coco.getImgIds()

counter = 1
for imgId in imgIds:
  img = coco.loadImgs(imgId)[0]
  annIds = coco.getAnnIds(imgIds=imgId, iscrowd=None)
  anns = coco.loadAnns(annIds)
  f_out = open(args.output_path + '/' + img['file_name'].split('.')[0]+'.txt', mode='w')

  for ann in anns:
    # print(ann['bbox'])
    # print(img['file_name'])
    x = float(ann['bbox'][0])
    y = float(ann['bbox'][1])
    width = float(ann['bbox'][2])
    height = float(ann['bbox'][3])
    #yolo format ([x_centre, y_centre, width, heigth] relative to image size)
    c_x = (x + width/2)/img['width']
    c_y = (y + height/2)/img['height']
    w = width/img['width']
    h = height/img['height']
    f_out.write("{} {} {} {} {}\n".format(ann['category_id'], c_x, c_y, w, h))
  
  if counter % 200 == 0:
    print(counter, 'YOLO label files created.')
  counter += 1
  
  f_out.close()
