''' Specialized viewer process, working with an underlying process.

New in Axon 4.6.

This convenience class is a way to define a viewer process which is linked to
another process (or pipeline). A viewer attached to a process will be able to
access the reference process parameters in order to build a display using the
exact same parameters values. This can avoid ambiguities.

Such a viewer will get an additional attribute, 'reference_process', when
executing.
It can (should) be specialized to work witn one or several processes, which
are specified in its 'allowed_processes' attribute. The viewer will only be triggered when displaying a parameter of these specific processes.
The viewer still needs a signature with a main input parameter, which should match the desired process parameter.

To use it, a specialized viewer process should import this brainvisa.processing.process_based_viewer module, and declare a 'base_class' attribute with the value of the ProcessBasedViewer class

Here is an example of a specialized viewer process, using this mechanism:

::

    from brainvisa.processes import ReadDiskItem
    from brainvisa.processing.process_based_viewer import ProcessBasedViewer

    name = 'Anatomist view bias correction, Morphologist pipeline variant'
    base_class = ProcessBasedViewer
    allowed_processes = ['morphologist']

    signature = Signature(
        'input', ReadDiskItem('T1 MRI Bias Corrected',
                              'anatomist volume formats'),
    )

    def execution(self, context):
        # run the regular viewer using custom parameters
        viewer = getProcessInstance('AnatomistShowBiasCorrection')
        if not hasattr(self, 'reference_process'):
            # fallback to regular behavior
            return context.runProcess(viewer, self.input)
        # get t1mri and histo_analysis from morphologist pipeline instance
        t1mri = self.reference_process.t1mr1
        histo_analysis = self.reference_process.histo_analysis
        return context.runProcess(
            viewer, mri_corrected=self.input,
            t1mri=t1mri, histo_analysis=histo_analysis)

Technically, the ProcessBasedViewer class merely delclares some default attribute values for the process:

::

    reference_process = None
    roles = ('viewer', )
    userLevel = 3
    allowed_processes = []

A viewer linked to a process could directly delclare these attibutes instead of inheriting the ProcessBasedViewer class - it is also a matter of code clarity. The viewer mechanism does not check inheritance, but tests the presence of these attributes in the viewer class. A specialized viewer can of course overwrite these attributes, and actually should, at least for the 'allowed_processes' variable.
'''

from brainvisa import processes

class ProcessBasedViewer(processes.Process):
    ''' Specialized viewer process, working with an underlying process.

    See the :py:mod:`brainvisa.processing.process_based_viewer` doc for
    details.
    '''
    reference_process = None
    roles = ('viewer', )
    userLevel = 3

    def __init__(self):
        super(ProcessBasedViewer, self).__init__()
        self.reference_process = None
        if not hasattr(self, 'allowed_processes'):
            self.allowed_processes = []

