# -*- coding: utf-8 -*-
from __future__ import absolute_import
from brainvisa.processes import *
from brainvisa.data.directory_iterator import DirectoryIterator
from brainvisa.data.neuroHierarchy import databases
from six.moves import zip

name = 'Copy data between databases'
userLevel = 0

signature = Signature(
    'data_type', Choice('Any type'),
    'input_data', ReadDiskItem('Any Type', 'Directory'),
    'output_database', Choice(),
    'output_data', WriteDiskItem('Any Type', getAllFormats()),
)


def dataTypeChanged(self, dataType):
    if dataType:
        formats = list(databases.getTypesFormats(dataType))
        if not formats:
            formats = getAllFormats()
        self.signature['input_data'] = ReadDiskItem(dataType, formats)
        self.signature['output_data'] = WriteDiskItem(dataType, formats)
        self.signatureChangeNotifier.notify(self)


def initialization(self):
    def linkDB(proc, dummy):
        if proc.input_data is not None:
            idbn = proc.input_data.get('_database')
            idbo = [p for p in neuroConfig.dataPath
                    if p.directory == idbn][0]
            onto = idbo.expert_settings.ontology
            odbo = [p for p in neuroConfig.dataPath
                    if p.expert_settings.ontology == onto]
            if len(odbo) >= 2:
                odb = [p.directory for p in odbo if p.directory != idbn]
                if len(odb) != 0:
                    return odb[0]
            if len(odbo) >= 1:
                return odbo[0].directory
        return proc.output_database

    def linkDtype(proc, dummy):
        db = None
        if proc.output_database is not None:
            db = proc.output_database
        if proc.input_data is not None:
            proc.signature['output_data'] = WriteDiskItem(
                proc.input_data.type, proc.input_data.format)
        else:
            proc.signature['output_data'] = WriteDiskItem(
                'Any Type', getAllFormats())
        proc.changeSignature(proc.signature)
        if db is not None:
            return proc.signature['output_data'].findValue(
                proc.input_data,
                requiredAttributes={'_database': db.directory})
        else:
            return proc.signature['output_data'].findValue(
                proc.input_data)

    possibleTypes = [t.name for t in getAllDiskItemTypes()]
    self.signature['data_type'].setChoices(*sorted(possibleTypes))
    self.data_type = 'Any Type'
    databases = [(dbs.directory, neuroHierarchy.databases.database(dbs.directory))
                 for dbs in neuroConfig.dataPath if not dbs.builtin]
    self.signature['output_database'].setChoices(*databases)
    if len(databases) > 0:
        self.output_database = databases[0][1]
    self.addLink('input_data', 'data_type', self.dataTypeChanged)
    self.linkParameters('output_database', 'input_data', linkDB)
    self.linkParameters('output_data', ('input_data', 'output_database'),
                        linkDtype)


def copyData(self, context, input_data, output_data, insertdb=None):
    prefix = os.path.dirname(output_data.fullPath())
    if not os.path.exists(prefix):
        os.makedirs(prefix)
    if input_data.format.name.lower() != 'directory':
        for idta, odta in \
                zip(input_data.fullPaths(), output_data.fullPaths()):
            if os.path.isdir(idta):
                if os.path.exists(odta):
                    shutil.rmtree(odta)
                shutil.copytree(idta, odta)
            else:
                shutil.copy2(idta, odta)
    minf = input_data.minfFileName()
    if minf is not None and os.path.exists(minf):
        shutil.copy2(minf, output_data.minfFileName())
    if insertdb:
        insertdb.insertDiskItem(output_data, update=True)


def execution(self, context):
    context.write('input:', self.input_data.fullPaths())
    outdb = self.output_data.get('_database')
    context.write('output db:', outdb)
    if self.output_data.get('_database') is None:
        output_data = self.signature['output_data'].findValue(
            self.output_data)
        outdb = output_data.get('_database')
        context.write('fixed output:', output_data)
    else:
        output_data = self.output_data
    context.write('output atts:', output_data.hierarchyAttributes())

    self.copyData(context, self.input_data, output_data)

    if os.path.isdir(self.input_data.fullPath()):
        dbn = self.input_data.get('_database', None)
        if dbn is not None:
            db = neuroHierarchy.databases.database(dbn)
            gen = db.scanDatabaseDirectories( \
                # directoriesIterator=DirectoryIterator(
                # self.input_data.fullPath() ),
                directoriesToScan=(self.input_data.fullPath() + '/', ),
                recursion=True, includeUnknowns=False, context=context)
            notdone = []
            odb = neuroHierarchy.databases.database(outdb)
            for item in gen:
                outitem = WriteDiskItem(item.type, item.format).findValue(
                    item,
                    requiredAttributes=output_data.hierarchyAttributes())
                context.write(item.type, item.format, item, '->', outitem)
                if outitem is not None:
                    self.copyData(context, item, outitem, odb)
                else:
                    notdone.append(item)
            if len(notdone) != 0:
                context.write(
                    'The following items could <b>not</b> be copied:')
                context.write('\n'.join([str(item) for item in notdone]))
                raise RuntimeError('Files not copied')
