# Adjusted Version from the tensorflow object detection repository
# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
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
# ==============================================================================

r"""Convert a folder with Yolo label files to a TFRecord for object_detection.
Assumes train and/or val folder inside input folder with images and Yolo label files.


Example usage:
    ./yolo_2_tf_record --data_dir=/home/user/images \
        --output_dir=/home/user/images/output
"""

import hashlib
import io
import logging
import os
import glob
import random
import re

from lxml import etree
import PIL.Image
import tensorflow as tf

from object_detection.utils import dataset_util
from object_detection.utils import label_map_util

flags = tf.app.flags
flags.DEFINE_string('data_dir', '../openImages', 'Root directory to raw dataset.')
flags.DEFINE_string('output_dir', '../openImages', 'Path to directory to output TFRecords.')
flags.DEFINE_string('label_map_path', '../openImages/label_map.pbtxt',
                    'Path to label map proto')
FLAGS = flags.FLAGS


def txt_to_tf_example(txt, img_path, label_map_dict):
  """Convert XML derived dict to tf.Example proto.

  Notice that this function normalizes the bounding box coordinates provided
  by the raw data.

  Args:
    data: dict holding PASCAL XML fields for a single image (obtained by
      running dataset_util.recursive_parse_xml_to_dict)
    label_map_dict: A map from string label names to integers ids.
    image_subdirectory: String specifying subdirectory within the
      Pascal dataset directory holding the actual image data.
    ignore_difficult_instances: Whether to skip difficult instances in the
      dataset  (default: False).

  Returns:
    example: The converted tf.Example.

  Raises:
    ValueError: if the image pointed to by data['filename'] is not a valid JPEG
  """

  # img_path = os.path.join(image_subdirectory, data['filename'])
  _, filename = os.path.split(img_path)
  with tf.gfile.GFile(img_path, 'rb') as fid:
    encoded_jpg = fid.read()
  encoded_jpg_io = io.BytesIO(encoded_jpg)
  image = PIL.Image.open(encoded_jpg_io)
  if image.format != 'JPEG':
    raise ValueError('Image {} format not JPEG'.format(img_path))
  key = hashlib.sha256(encoded_jpg).hexdigest()

  width = int(image.size[0])
  height = int(image.size[1])

  xmin = []
  ymin = []
  xmax = []
  ymax = []
  classes = []
  classes_text = []
  truncated = []
  poses = []
  difficult_obj = []
  for obj in txt.split('\n'):
    if obj == '':
      continue
    difficult_obj.append(0)
    obj_data = obj.split(' ')

    xmin.append(float(obj_data[1])-float(obj_data[3])/2)
    ymin.append(float(obj_data[2])-float(obj_data[4])/2)
    xmax.append(float(obj_data[1])+float(obj_data[3])/2)
    ymax.append(float(obj_data[2])+float(obj_data[4])/2)
    # class_name = get_class_name_from_filename(data['filename'])
    # classes_text.append(class_name.encode('utf8'))
    # classes.append(label_map_dict[class_name])
    for name, idx in label_map_dict.items():
      if idx == int(obj_data[0]):
        classes_text.append(name.encode('utf8'))
    classes.append(int(obj_data[0]))
    truncated.append(0)
    poses.append('Frontal'.encode('utf8'))

  example = tf.train.Example(features=tf.train.Features(feature={
      'image/height': dataset_util.int64_feature(height),
      'image/width': dataset_util.int64_feature(width),
      'image/filename': dataset_util.bytes_feature(
          filename.encode('utf8')),
      'image/source_id': dataset_util.bytes_feature(
          filename.encode('utf8')),
      'image/key/sha256': dataset_util.bytes_feature(key.encode('utf8')),
      'image/encoded': dataset_util.bytes_feature(encoded_jpg),
      'image/format': dataset_util.bytes_feature('jpeg'.encode('utf8')),
      'image/object/bbox/xmin': dataset_util.float_list_feature(xmin),
      'image/object/bbox/xmax': dataset_util.float_list_feature(xmax),
      'image/object/bbox/ymin': dataset_util.float_list_feature(ymin),
      'image/object/bbox/ymax': dataset_util.float_list_feature(ymax),
      'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
      'image/object/class/label': dataset_util.int64_list_feature(classes),
      'image/object/difficult': dataset_util.int64_list_feature(difficult_obj),
      'image/object/truncated': dataset_util.int64_list_feature(truncated),
      'image/object/view': dataset_util.bytes_list_feature(poses),
  }))
  return example


def create_tf_record(output_filename,
                     label_map_dict,
                     image_dir):
  """Creates a TFRecord file from examples.

  Args:
    output_filename: Path to where output file is saved.
    label_map_dict: The label map dictionary.
    annotations_dir: Directory where annotation files are stored.
    image_dir: Directory where image files are stored.
    examples: Examples to parse and save to tf record.
  """
  writer = tf.python_io.TFRecordWriter(output_filename)
  examples = glob.glob(os.path.join(image_dir, '*.jpg'))+glob.glob(os.path.join(image_dir, '*.png'))
  for idx, example in enumerate(examples):
    if idx % 100 == 0:
      print('On image {} of {}'.format(idx, len(examples)))
      logging.info('On image %d of %d', idx, len(examples))
    txt_file = os.path.join(image_dir, os.path.split(example)[1].split('.')[0] + '.txt')

    if not os.path.exists(txt_file):
      logging.warning('Could not find %s, ignoring example.', txt_file)
      continue
    with tf.gfile.GFile(txt_file, 'r') as fid:
      yolo_str = fid.read()

    tf_example = txt_to_tf_example(yolo_str, example, label_map_dict)
    writer.write(tf_example.SerializeToString())

  writer.close()


def main(_):
  data_dir = FLAGS.data_dir
  label_map_dict = label_map_util.get_label_map_dict(FLAGS.label_map_path)

  logging.info('Reading from Pet dataset.')
  train_dir = os.path.join(data_dir, 'train')
  val_dir = os.path.join(data_dir, 'val')

  if os.path.exists(train_dir):
    train_output_path = os.path.join(FLAGS.output_dir, 'train.record')
    create_tf_record(train_output_path, label_map_dict, train_dir)
  if os.path.exists(val_dir):
    val_output_path = os.path.join(FLAGS.output_dir, 'val.record')
    create_tf_record(val_output_path, label_map_dict, val_dir)

if __name__ == '__main__':
  tf.app.run()
