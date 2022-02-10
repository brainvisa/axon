import csv
import json
import shutil
from tempfile import NamedTemporaryFile

from brainvisa.processes import Signature
from brainvisa.processes import ListOf, ReadDiskItem, WriteDiskItem

userLevel = 0
name = 'Statistics in ROI - generic'

signature = Signature(
    'images', ListOf(ReadDiskItem('4D Volume',
                                  ['gz compressed NIFTI-1 image', 'NIFTI-1 image'])),
    'ROI', ReadDiskItem('4D Volume',
                        ['gz compressed NIFTI-1 image', 'NIFTI-1 image']),
    'translation', ReadDiskItem('Any type', 'JSON file'),
    'statistics', WriteDiskItem('CSV file', 'CSV file'),
)


def initialization(self):
    self.setOptional('translation')


def execution(self, context):
    images_join = [image.fullPath() for image in self.images]
    images_joined = ' '.join(images_join)
    cmd = ['AimsRoiFeatures',
           '-f', 'csv',
           '-i', self.ROI.fullPath(),
           '-s', images_joined,
           '-o', self.statistics.fullPath()]
    context.system(*cmd)

    if self.translation:
        with open(self.translation.fullPath(), 'r') as trans_file:
            trans_dict = json.load(trans_file)

        tempfile = NamedTemporaryFile(mode='w', delete=False)
        with open(self.statistics.fullPath(), 'r') as stat_file, tempfile:
            reader = csv.reader(stat_file, delimiter='\t')
            writer = csv.writer(tempfile, delimiter='\t')

            header = next(reader)
            header.insert(1, 'ROI_name')
            writer.writerow(header)
            
            for row in reader:
                label = row[0]
                row.insert(1, trans_dict.get(label, ''))
                writer.writerow(row)

        shutil.move(tempfile.name, self.statistics.fullPath())
