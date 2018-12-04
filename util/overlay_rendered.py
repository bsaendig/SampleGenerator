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
"""Insert object images into background images by scaling and placing them corresponding to labelled objects in the background images. Needs a json info file containing classes and aspect-ratios of rendered objects that can be generated with util/write_class_info.py."""

import os, glob
import numpy as np
from scipy import ndimage, signal
from PIL import Image
import argparse
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import random
import json
from pycocotools.coco import COCO

parser = argparse.ArgumentParser(description='Paste croppped object images into backgrounds.')
parser.add_argument('--input_path', '--i', action='store',
                    default='../scenes/samples/train/rgba',
                    help='Path to the object images.')
parser.add_argument('--object_info', action='store',
                    default='../scenes/samples/train/info.json',
                    help='Path to the object info JSON file containing classes and ratios of objects. (generated with util/write_class_info.py)')
parser.add_argument('--bg_path', '--bg', action='store',
                    default='../bg',
                    help='Path to the background images.')
parser.add_argument('--n', action='store', type = int,
                    default=1000,
                    help='Number of training images to be generated.')
parser.add_argument('--output_path', '--o', action='store',
                    default='../overlay',
                    help='Output path.')

args = parser.parse_args()

img_list = sorted(glob.glob(args.input_path + "/*.png"))
bg_list = sorted(glob.glob(args.bg_path + "/*.png")+glob.glob(args.bg_path + "/*.jpg"))

json_file = open(args.object_info)
obj_info = json.loads(json_file.read())
json_file.close()
obj_classes = obj_info.keys()

def read_classes(line):
  c, x, y, w, h = line.split(' ')
  return c, float(x), float(y), float(w), float(h)

def is_in(a, b):
  ax1 = a[1] - a[3]/2
  ax2 = a[1] + a[3]/2
  ay1 = a[2] - a[4]/2
  ay2 = a[2] + a[4]/2
  bx1 = b[1] - b[3]/2
  bx2 = b[1] + b[3]/2
  by1 = b[2] - b[4]/2
  by2 = b[2] + b[4]/2
  if ax1>bx1 and ax2<bx2 and ay1>by1 and ay2<by2:
    return True
  else:
    return False

def resize_and_paste(obj_img, obj_w, obj_h, obj_c_x, obj_c_y, bg, w, h, c_x, c_y):
  """Resizes and pastes an Object Image so that it matches the size of a bounding box from the original background image.
  
  Arguments:
    obj_img {PIL.Image} -- Object image
    obj_w {float} -- width of added object
    obj_h {float} -- height of added object
    obj_c_x {float} -- Center x position of added object
    obj_c_y {float} -- Center y position of added object
    bg {PIL.Image} -- Background image
    w {float} -- width of object in background
    h {float} -- height of object in background
    c_x {float} -- Center x position in background
    c_y {float} -- Center y position in background
  
  Returns:
    bg {PIL.Image} -- altered background image
    x {Float}-- x coordinate of the pasted image's center relative to background size
    y {Float}-- y coordinate of the pasted image's center relative to background size
    w {Float}-- width of the pasted image relative to background size
    h {Float}-- height of the pasted image relative to background size
  """

  # check if object bounding box is cut off by the image
  right_shift = False
  left_shift = False
  top_shift = False
  bottom_shift = False
  shift = 0.0
  e = 0.05
  if abs(1 - (c_x + w/2)) < e:
    right_shift = True
    shift = random.random()*.6
  if abs(0 - (c_x - w/2)) < e:
    left_shift = True
    shift = random.random()*.6
  if abs(1 - (c_y + h/2)) < e:
    bottom_shift = True
    shift = random.random()*.6
  if abs(0 - (c_y - h/2)) < e:
    top_shift = True
    shift = random.random()*.6

  # calculate the size ratio difference between the object from the bg and the pasted object
  bg_width = bg.size[0]
  bg_height = bg.size[1]
  bg_w = bg_width * w
  bg_h = bg_height * h
  obj_w = obj_img.size[0] * obj_w
  obj_h = obj_img.size[1] * obj_h
  ratio_x = bg_w/obj_w
  ratio_y = bg_h/obj_h
  # print('ratios x and y: ', ratio_x, ratio_y)
  scale_factor = max(ratio_x, ratio_y) + shift

  new_size = (int(obj_img.size[0] * scale_factor), int(obj_img.size[1] * scale_factor))
  obj_img = obj_img.resize(new_size, Image.BICUBIC)

  # coordinates for pasting (center x,y of the background image - offset of the object center in the object image)
  x = int(c_x*bg_width-(new_size[0]*obj_c_x))
  y = int(c_y*bg_height-(new_size[1]*obj_c_y))

  # if bbox reached the image border pasted image reaches outside
  if right_shift:
    x = int(x + obj_w*scale_factor*shift*obj_c_x)
  if left_shift:
    x = int(x - obj_w*scale_factor*shift*obj_c_x)
  if top_shift:
    y = int(y - obj_h*scale_factor*shift*obj_c_y)
  if top_shift:
    y = int(y + obj_h*scale_factor*shift*obj_c_y)

  bg = bg.paste(obj_img,(x,y),obj_img)

  c_x = (x + new_size[0]*obj_c_x)/bg_width
  c_y = (y + new_size[1]*obj_c_y)/bg_height
  w = (obj_w*scale_factor)/bg_width
  h = (obj_h*scale_factor)/bg_height
  return bg, c_x , c_y, w, h


if not os.path.exists(args.output_path):
    os.makedirs(args.output_path)

bg_count = 0
i = 0
while i < args.n:

  bg = Image.open(bg_list[bg_count%len(bg_list)])
  # print("BG Image: ", bg_list[bg_count%len(bg_list)])
  print('Image: ', i)

  bg_labels_file = open(bg_list[bg_count%len(bg_list)][:-4] + '.txt', mode = "r")
  labels = []

  count = 0
  for line in bg_labels_file:
    c, c_x, c_y, w, h = read_classes(line)
    if w >= h:
      ratio = str(round(h/w,1))
    else:
      ratio = str(round(-w/h,1))
    ## check if object image with similar ratio exists
    if c in obj_info:
      if not ratio in obj_info[c]:
        ratios = list(obj_info[c].keys())
        ratio = ratios[random.randint(0,len(ratios)-1)]
      ## choose a random object image with similar ratio
      obj_dict = obj_info[c][ratio][random.randint(0,len(obj_info[c][ratio])-1)]
      obj_img = Image.open(os.path.join(args.input_path, obj_dict['img']))
      obj_c_x = obj_dict['center_x']
      obj_c_y = obj_dict['center_y']
      obj_w = obj_dict['width']
      obj_h = obj_dict['height']
      ## resize and paste onto background
      obj_img, c_x, c_y, w, h = resize_and_paste(obj_img, obj_w, obj_h, obj_c_x, obj_c_y, bg, w, h, c_x, c_y)
      # print('new bbox size', w, h)

      ## add new label

      # w = (obj_img.size[0]*float(w))/bg.size[0]
      # h = (obj_img.size[1]*float(h))/bg.size[1]
      # c_x = (pos[0] + obj_img.size[0]*float(c_x)) / bg.size[0]
      # c_y = (pos[1] + obj_img.size[1]*float(c_y)) / bg.size[1]

      labels.append((c, c_x, c_y, w, h))
      count += 1
    else:
      # print('Class {} not found in rendered training images'.format(c))
      labels.append((c, c_x, c_y, w, h))

    

  bg.save('{}/{}.jpg'.format(args.output_path, i))
  out_file = open('{}/{}.txt'.format(args.output_path, i), mode = 'w')

  for line in labels:
    out_file.write("{} {} {} {} {}\n".format(*line))
  bg_labels_file.close()
  out_file.close()
  i+=1
  bg_count+=1
  if i%100==0:
    print(i, 'images processed.')