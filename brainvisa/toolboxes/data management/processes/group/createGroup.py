# -*- coding: utf-8 -*-
from __future__ import absolute_import
from brainvisa.processes import *
from brainvisa.group_utils import Subject
from soma.minf.api import registerClass, writeMinf

name = '1 Creation of a group of subject'
userLevel = 1

signature = Signature(
    'list_of_subjects', ListOf(ReadDiskItem("Subject", 'Directory')),
  'group_definition', WriteDiskItem('Group definition', 'XML'),
)


def initialization(self):
    pass


def execution(self, context):
    groupOfSubjects = list()

    for subject in self.list_of_subjects:
        groupOfSubjects.append(Subject(subject))

    registerClass('minf_2.0', Subject, 'Subject')

    writeMinf(self.group_definition.fullPath(), groupOfSubjects,
              reducer='minf_2.0')
