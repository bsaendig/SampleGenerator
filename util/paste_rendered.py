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
"""Insert object images into background images by scaling and placing them randomly."""

import os, glob
import numpy as np
from scipy import ndimage, signal
from PIL import Image
import argparse
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import random
import json

parser = argparse.ArgumentParser(description='Paste croppped object images into backgrounds.')
parser.add_argument('--input_path', '--i', action='store',
                    default='../scenes/samples/train/rgba',
                    help='Path to the object images.')
parser.add_argument('--bg_path', '--bg', action='store',
                    default='../bg',
                    help='Path to the background images.')
parser.add_argument('--n', action='store', type = int,
                    default=1000,
                    help='Number of training images to be generated.')
parser.add_argument('--min_ratio', action='store', type = float,
                    default=.5,
                    help='The minimal ratio between object and background size.')
parser.add_argument('--max_ratio', action='store', type = float,
                    default=1.5,
                    help='The maximal ratio between object and background size.')
parser.add_argument('--n_objects', '--no', action='store', type = int,
                    default=3,
                    help='Maximum number of objects pasted into each image.')
parser.add_argument('--min_objects', action='store', type = int,
                    default=1,
                    help='Minimum number of objects pasted into each image.')
parser.add_argument('--output_path', '--o', action='store',
                    default='../augmented',
                    help='Output path.')

# determines if labels of background objects, which are occluded by added objects will be deleted
DELETE_OCCLUDED_OBJECT_LABELS = True
IGNORE_BG_LABELS = False

args = parser.parse_args()

img_list = sorted(glob.glob(args.input_path + "/*.png"))
bg_list = sorted(glob.glob(args.bg_path + "/*.png")+glob.glob(args.bg_path + "/*.jpg"))


def read_classes(line):
  c, x, y, w, h = line.split(' ')
  return int(c), float(x), float(y), float(w), float(h)

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

def delete_occluded_labels(prior_labels, added_labels):
  for a in added_labels:
    keep = [x for x in prior_labels if not is_in(x,a)]
    prior_labels = keep
    prior_labels.append(a)
  return prior_labels


def rand_resize(img, bg, max_ratio = 1.3, min_ratio =.07):
  """Resizes img to a fraction of the background image within given bounds.
  
  Arguments:
    img {PIL.Image} -- Object image
    bg {PIL.Image} -- Background image
  
  Keyword Arguments:
    max_ratio {float} -- maximum fraction of background size (default: {.7})
    min_ratio {float} -- minimum fraction of background size (default: {.07})
  """

  short_side = min(*bg.size)
  new_size = random.randint(int(short_side*min_ratio),int(short_side*max_ratio))
  ratios = np.divide(img.size,max(img.size))
  return img.resize(list(map(int,(np.multiply(ratios, new_size)))), Image.BICUBIC)

def rand_paste(img, bg, outside_ratio = .5):
  """Pastes img into background (placed randomly)
  
  Arguments:
    img {PIL.Image} -- Image that will be pasted.
    bg {PIL.Image} -- Background Image.
    outside_ratio {Float} -- part of img that is allowed to hang over the borders of bg and by that get cut off.
  
  Returns:
    bg {PIL.Image} -- Resulting Image.
    placed_coords {(int, int)} -- top-left corner of Image placement
  """

  x = random.randint(-int(img.size[0]*outside_ratio), bg.size[0] - int(img.size[0]*(1-outside_ratio)))
  y = random.randint(-int(img.size[1]*outside_ratio), bg.size[1] - int(img.size[1]*(1-outside_ratio)))
  bg.paste(img,(x,y),img)

  return bg, (x, y)


def get_stuff_mask(annotations):
  mask = None
  for ann in annotations:
    if mask is None:
      mask = coco.annToMask(ann) == 1
    else:
      mask = np.logical_or(mask, coco.annToMask(ann) == 1)
  return mask;

def masked_rand_paste(img, bg, mask_img, border_ratio = .0, erosion_ratio = .1):
  """Pastes img into background (placed randomly) but only onto masked area
  
  Arguments:
    img {PIL.Image} -- Image that will be pasted.
    bg {PIL.Image} -- Background Image.
    mask_img {numpy.array} -- Mask Image.
    border_ratio {Float} -- ratio of img size that is added as a border where the image will not be placed.
    erosion_ratio {Float} -- ratio of img size that gets eroded from mask (so that pasted image overlaps less with unallowed areas) When the actual object in a pasted image only occupies a quarter of the space in the middle of the pasted image, a value of .25 would already mean it would not touch unallowed areas.
  
  Returns:
    bg {PIL.Image} -- Resulting Image.
    placed_coords {(int, int)} -- top-left corner of Image placement
  """
  ## erosion so that objects do not overlap to much with disallowed areas
  border_x = int(img.size[0] * border_ratio * .5) 
  border_y = int(img.size[1] * border_ratio * .5)
  erosion = int(max(img.size[0], img.size[1]) * erosion_ratio)

  # print("erosion size:", erosion)

  if erosion > 0:
    #mask_img = ndimage.binary_erosion(mask_img, structure=np.ones((erosion ,erosion))).astype(mask_img.dtype)
    mask_img = np.logical_not(mask_img)
    mask_img = signal.fftconvolve(mask_img, np.ones((erosion,erosion)), 'same') > .5
    mask_img = np.logical_not(mask_img)

  # print("Size x and y:", img.size[0], img.size[1])
  # print("Border x and y:", border_x, border_y)
  mask_img[:int(border_y), :] = 0
  mask_img[mask_img.shape[0] - int(border_y):, :] = 0
  mask_img[:, :int(border_x)] = 0
  mask_img[:, mask_img.shape[1] - int(border_x):] = 0

  # plt.imshow(mask_img)
  # plt.show()

  ## indexes of allowed mask areas
  y,x = np.where(mask_img > 0)
  ## choose one at random
  if len(x) < 1:
    print('Allowed placements: ', len(x))
    return bg, None
  i = np.random.randint(len(x))
  ## get position of top left corner
  random_pos = [x[i] - int(img.size[0]/2), y[i] - int(img.size[1]/2)]

  bg.paste(img, random_pos ,img)

  return bg, random_pos


if not os.path.exists(args.output_path):
    os.makedirs(args.output_path)

bg_count = 0
i = 0
while i < args.n:
  
  bg = Image.open(bg_list[bg_count%len(bg_list)])
  # print("BG Image: ", bg_list[bg_count%len(bg_list)])

  bg_labels_file = open(bg_list[bg_count%len(bg_list)][:-4] + '.txt', mode = "r")
  added_labels = []

  count = 0
  n = random.randint(args.min_objects,args.n_objects)
  while count < n:
    ## open random object image
    img_name = img_list[random.randint(0,len(img_list)-1)]
    img = Image.open(img_name)
    ## read class
    img_label_file = open(img_name[:-4] + '.txt', mode = "r")
    label = img_label_file.read().replace('\n','').split(' ')
    if len(label) == 5:
      obj_class, c_x, c_y, w, h = label
      ## resize and paste random into background
      img = rand_resize(img, bg, max_ratio =args.max_ratio, min_ratio =args.min_ratio)
      bg, pos = rand_paste(img, bg)
    else:
      continue;

    ## add new label
    width = (img.size[0]*float(w))/bg.size[0]
    height = (img.size[1]*float(h))/bg.size[1]
    centre_x = (pos[0] + img.size[0]*float(c_x)) / bg.size[0]
    centre_y = (pos[1] + img.size[1]*float(c_y)) / bg.size[1]

    added_labels.append((obj_class, centre_x, centre_y, width, height))
    count += 1

  bg.save('{}/{}.jpg'.format(args.output_path, i))
  out_file = open('{}/{}.txt'.format(args.output_path, i), mode = 'w')
  labels = []
  if not IGNORE_BG_LABELS:
    for line in bg_labels_file:
      labels.append(read_classes(line))
  if DELETE_OCCLUDED_OBJECT_LABELS:
    labels = delete_occluded_labels(labels, added_labels)
  else:
    labels += added_labels

  for line in labels:
    out_file.write("{} {} {} {} {}\n".format(*line))
  bg_labels_file.close()
  out_file.close()
  i+=1
  bg_count+=1
  if i%100==0:
    print(i, 'images processed.')