from __future__ import print_function
import sys
import os
from pprint import pprint


from tempfile import mkdtemp
from shutil import rmtree
from pprint import pprint
from fedji.sqlite_backend import FedjiSqlite
import six

tmp = mkdtemp()
try:
    mongo = FedjiSqlite(tmp)
    mongo.base.collection.insert([
        {'path': '/somewhere/toto',
            'subject': 'toto'},
        {'path': '/somewhere/titi',
            'subject': 'titi'}])
    mongo.base.collection.create_index('path')
    mongo.base.collection.create_index('subject')
    pprint(mongo.base.collection.find_one({'path': '/somewhere/toto'}))
    pprint(mongo.base.collection.find({'subject': 'titi'}).count())
    pprint(list(mongo.base.collection.find({'subject': 'titi'})))
    pprint(list(mongo.base.collection.find({}).distinct('subject')))
    pprint(mongo.base.collection.fields)
finally:
    rmtree(tmp)

# pa=PathAttributes()
# pa.add_path('titi', dict(s='no',i=4,f=4.3,l=[1,'tutu']))
# pa.add_path('toto', dict(s='yes',i=4,f=4.3,l=[1,2,'tutu']))
# pa.add_path('bubu', dict(i=4,f=4.3,l=[1,'tutu']))
# for query in [
        # dict(),
        # dict(i=4),
        # dict(s='yes'),
        # dict(l=[1,'tutu']),
        # dict(s=None)
        #]:
    # print 'Query:', query
    # pprint(list(pa.query_path(query)))


# sa = PathAttributes('/tmp/db.sqlite')
# sa.add_path('memento/001/0010007_BOND/MRI/0010007_BOND_MRI_3dt1',
    # dict(study='the_study',
    # center='001',
    # subject='0010007_BOND',
    # modality='mri',
    # sequence='3dt1',
    # geo_corrected=False,
    # bias_corrected=False))
# sa.add_path('memento/001/0010007_BOND/MRI/0010007_BOND_MRI_3dt1_geo',
    # dict(study='the_study',
    # center='001',
    # subject='0010007_BOND',
    # modality='mri',
    # sequence='3dt1',
    # geo_corrected=True,
    # bias_corrected=False))
# sa.add_path('memento/001/0010007_BOND/MRI/0010007_BOND_MRI_3dt1_nobias',
    # dict(study='the_study',
    # center='001',
    # subject='0010007_BOND',
    # modality='mri',
    # sequence='3dt1',
    # geo_corrected=False,
    # bias_corrected=True))
# print sa.attributes
# print sa.path_attributes('memento/001/0010007_BOND/MRI/0010007_BOND_MRI_3dt1')
# print sa.path_attributes('memento/001/0010007_BOND/MRI/0010007_BOND_MRI_3dt1_geo')
# print sa.path_attributes('memento/001/0010007_BOND/MRI/0010007_BOND_MRI_3dt1_nobias')
# print list(sa.query_path(dict(subject='0010007_BOND')))


import random
import time
from fedji.sqlite_backend import FedjiSqlite
from fedji.mongodb_backend import FedjiMongo

# 438.09 seconds for 10000 subjects = 22.83 subjects/second
db = FedjiSqlite('/tmp/fedji_sqlite').test.paths

# 875.94 seconds for 10000 subjects = 11.42 subjects/second
# db = FedjiMongo().test.paths


def mri_path(attributes):
    if attributes['study']:
        path = ['%s_%s' % (attributes['study'], attributes['center'])]
    else:
        path = [attributes['center']]
    path.append(attributes['subject'])
    path.append(attributes['sequence'])
    acquisition = '_'.join(i for i in (attributes.get('visit'),
                                       attributes.get('scan'),
                                       '-'.join(
        attributes.get(
        'bias_correction', [])),
        '-'.join(
        attributes.get(
            'geo_correction', [])),
                                        attributes.get('registration_method'),
                                        attributes.get('registration_source'),
                                        attributes.get('registration_target')) if i)
    if not acquisition:
        acquisition = 'default_acquisition'
    path.append(acquisition)
    path.append(attributes['subject'] + (
        attributes['format'] if 'format' in attributes else '.nii'))
    return os.path.join(*path)


def pet_path(attributes):
    mri_attributes = attributes.copy()
    tracer = attributes.get('tracer')
    if tracer:
        mri_attributes['sequence'] = tracer
    return mri_path(mri_attributes)

start = time.time()
nb_studies = 4
nb_centers = 40
nb_subjects = 10000
studies = ['study%d' % i for i in range(1, nb_studies + 1)]
centers = [('00' + str(i))[-3:] for i in range(1, nb_centers + 1)]
letters = [chr(i) for i in range(65, 91)]
visits = [None, 'M000', 'M018']
scans = [None, 'rescan1']
bias_corrections = [None, ['nobias1'], ['nobias2'], ['nobias1', 'nobias2']]
geo_corrections = [None, ['geo1'], ['geo2'], ['geo1', 'geo2']]

count_by_center = {}
for i in six.moves.xrange(nb_subjects):
    # if i % 100 == 0:
        # db.commit()
    study = random.choice(studies)
    center = random.choice(centers)
    center_count = count_by_center[center] = count_by_center.get(center, 0) + 1
    subject = '%s%s_%s%s%s%s' % (
        center,
        ('000' + str(center_count))[-4:],
        random.choice(letters),
        random.choice(letters),
        random.choice(letters),
        random.choice(letters))
    print(i, subject)

    attributes = dict(study=study, center=center,
                      subject=subject, modality='mri', sequence='t1mri')
    for visit in visits:
        if visit:
            attributes['visit'] = visit
        for scan in scans:
            if scan:
                attributes['scan'] = scan
            for bias_correction in bias_corrections:
                if bias_correction:
                    attributes['bias_correction'] = bias_correction
                for geo_correction in geo_corrections:
                    if geo_correction:
                        attributes['geo_correction'] = geo_correction
                    doc = attributes.copy()
                    doc['path'] = mri_path(attributes)
                    db.insert(doc)
                del attributes['geo_correction']
            del attributes['bias_correction']
        del attributes['scan']

    attributes = dict(
        study=study, center=center, subject=subject, modality='pet')
    tracers = ['fdg', 'datscan']
    for visit in visits:
        if visit:
            attributes['visit'] = visit
        for tracer in tracers:
            attributes['tracer'] = tracer
            for scan in scans:
                if scan:
                    attributes['scan'] = scan
                for bias_correction in bias_corrections:
                    if bias_correction:
                        attributes['bias_correction'] = bias_correction
                    for geo_correction in geo_corrections:
                        if geo_correction:
                            attributes['geo_correction'] = geo_correction
                        doc = attributes.copy()
                        doc['path'] = pet_path(attributes)
                        db.insert(doc)
                    del attributes['geo_correction']
                del attributes['bias_correction']
            del attributes['scan']

# db.commit()
print('duration:', time.time() - start)
