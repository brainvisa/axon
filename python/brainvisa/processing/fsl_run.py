
from capsul.in_context import fsl
from soma.wip.application.application import Application
import os
import os.path as osp


def run_fsl_command(context, cmd, **kwargs):
    ''' Run a FSL command inside its environment.

    Uses capsul.in_context.fsl to do so.
    '''
    configuration = Application().configuration
    print('FSL conf:', configuration.FSL.fsldir)
    print(configuration.FSL.fsl_commands_prefix)
    os.environ['FSL_CONFIG'] = osp.join(configuration.FSL.fsldir, 'etc',
                                        'fslconf', 'fsl.sh')
    if configuration.FSL.fsl_commands_prefix:
        os.environ['FSL_PREFIX'] = configuration.FSL.fsl_commands_prefix
    full_cmd = fsl.fsl_command_with_environment(cmd)
    return context.system(*full_cmd, **kwargs)

