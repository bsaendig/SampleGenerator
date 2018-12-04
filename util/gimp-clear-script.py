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
"""Clears objects from background images with the help of gimp and its 'heal-selection' filter.
Reads Yolo style label files to gather the corresponding object bounding boxes. Copy into Gimps python-console to use."""

def clear(folder):
  import os, glob
  import numpy as np
  IGNORED_CLASSES = [1]
  img_list = sorted(glob.glob(folder + "*.jpg"))
  # print(img_list)
  for img_path in img_list:
    img = pdb.gimp_file_load(img_path, img_path)
    drawable = pdb.gimp_image_get_active_layer(img)
    label_path = img_path[:-4]+'.txt'
    if not os.path.exists(label_path):
      print('{} not found'.format(label_path))
      continue;
    with open(label_path) as f_labels:
      labels = f_labels.read().split('\n')
    for label in labels:
      params = label.split(' ')
      if len(params) != 5:
        continue;
      c, x, y, w, h = list(map(float, params))
      if int(c) in IGNORED_CLASSES:
        continue;
      x *= img.width
      y *= img.height
      w *= img.width
      h *= img.height
      pdb.gimp_image_select_rectangle(img, 0, int(x-w/2), int(y-h/2), w, h)
      pdb.python_fu_heal_selection(img, drawable, 50, 0, 0)
    pdb.gimp_file_save(img, drawable, img_path, img_path)
    pdb.gimp_image_delete(img)
#clear('./path_to_images') ## example usage