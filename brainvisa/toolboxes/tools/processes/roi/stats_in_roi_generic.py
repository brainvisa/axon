import csv
import json
import os
import shutil
from tempfile import NamedTemporaryFile

import pandas as pd

from brainvisa.processes import Signature
from brainvisa.processes import ListOf, ReadDiskItem, WriteDiskItem, Choice

userLevel = 0
name = 'Statistics in ROI - generic'

signature = Signature(
    'images', ListOf(ReadDiskItem('4D Volume',
                                  ['gz compressed NIFTI-1 image', 'NIFTI-1 image'])),
    'ROI', ReadDiskItem('4D Volume',
                        ['gz compressed NIFTI-1 image', 'NIFTI-1 image']),
    'translation', ReadDiskItem('Any type', 'JSON file'),
    'statistics_csv', WriteDiskItem('CSV file', 'CSV file'),
    'statistics', ListOf(Choice("mean", "volume", "median", "stddev", "min", "max", "point_count")),
)


def initialization(self):
    self.setOptional('translation')
    self.statistics = ["mean", "volume", "max", "min"]


def execution(self, context):
    images_join = [image.fullPath() for image in self.images]
    images_joined = ' '.join(images_join)
    cmd = ['AimsRoiFeatures',
           '-f', 'csv',
           '-i', self.ROI.fullPath(),
           '-s', images_joined,
           '-o', self.statistics_csv.fullPath()]
    context.system(*cmd)

    stats = pd.read_csv(self.statistics_csv.fullPath(), sep='\t')
    columns = ['ROI_label']

    # Use translate to save ROI name
    if self.translation:
        with open(self.translation.fullPath(), 'r') as trans_file:
            trans_dict = json.load(trans_file)
        stats['ROI_name'] = stats.apply(lambda row: trans_dict[str(int(row['ROI_label']))], axis=1)
        columns.append('ROI_name')

    # Only keep interesting statistics
    columns += self.statistics
    stats = stats[columns]
    stats.to_csv(self.statistics_csv.fullPath(), sep='\t', index=False)
