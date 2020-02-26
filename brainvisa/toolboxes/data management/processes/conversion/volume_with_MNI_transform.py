
from __future__ import absolute_import
from brainvisa.processes import *
from brainvisa.data import neuroDiskItems
from brainvisa import registration
try:
    from soma import aims
except:
    aims = None

def validation():
    try:
        from soma import aims
    except ImportError as e:
        raise ValidationError(str(e))


name = 'Write Volume with MNI transformation in header'


def children_of(type_name):
    types = neuroDiskItems.getAllDiskItemTypes()
    children = set((type_name, ))
    again = True
    while again:
        for t in types:
            again = False
            if t.name not in children and any([p.name in children
                                               for p in t.parents()]):
                children.add(t.name)
                again = True
    return children

signature = Signature(
    'volume_type', Choice(*sorted(children_of('4D Volume'))),
    'volume', ReadDiskItem('4D Volume', 'aims readable volume formats'),
    'output_volume', WriteDiskItem('4D Volume',
                                   'aims writable volume formats'),
    'MNI_transform_chain', ListOf(ReadDiskItem('Transformation matrix',
                                               'Transformation matrix')),
)


def search_transform(self, proc, dummy):
    if self.volume is None:
        return None
    tm = registration.getTransformationManager()
    pl = tm.findPaths(tm.referential(self.volume),
                      registration.talairachMNIReferentialId)
    for p in pl:
        return p


def change_vol_type(self, proc, dummy):
    s = self.signature
    s['volume'] = ReadDiskItem(self.volume_type,
                               'aims readable volume formats')
    self.changeSignature(s)


def initialization(self):
    self.volume_type = '4D Volume'
    self.linkParameters(None, 'volume_type', self.change_vol_type)
    self.linkParameters('output_volume', 'volume')
    self.linkParameters('MNI_transform_chain', 'volume', self.search_transform)


def execution(self, context):
    tr = aims.AffineTransformation3d()
    for t in self.MNI_transform_chain:
        ti = aims.read(t.fullPath())
        tr = ti * tr
    #context.write('transform:', tr)
    vol = aims.read(self.volume.fullPath())
    trl = vol.header().get('transformations', [])
    refl = vol.header().get('referentials', [])

    rname = aims.StandardReferentials.mniTemplateReferential()
    if rname in refl:
        trl[refl.index(rname)] = tr.toVector()
    elif len(trl) < 2:
    #else:
        trl.append(tr.toVector())
        refl.append(rname)
    else:
        trl = [list(trl[0]), list(tr.toVector())] \
            + [list(t) for t in list(trl)[1:]]
        refl = [refl[0], rname] + list(refl)[1:]
    # context.write('now:', refl, trl)
    vol.header()['referentials'] = refl
    vol.header()['transformations'] = trl
    context.write('new header:', vol.header())
    aims.write(vol, self.output_volume.fullPath())
    self.output_volume.readAndUpdateMinf()
    tm = registration.getTransformationManager()
    tm.copyReferential(self.volume, self.output_volume,
                       copy_transformations=False)

