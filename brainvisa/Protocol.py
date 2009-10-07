#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCIL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL version 2 license and that you accept its terms.
__author__ = "Julien Gilli <jgilli@nerim.fr>"
__version__  = "0.0"
__date__ ="11 August 2002"

# port numbers
COMPILER_DAEMON_PORT = 51087
SCHEDULER_DAEMON_PORT = 51088
SCHEDULER_DAEMON_PORT_INFO = 51089

# listen on the machine that instanciate the compiler daemon
COMPILER_DAEMON_HOST =''
SCHEDULER_DAEMON_HOST = ''

COMMAND_TYPE_SIZE = 4
DATA_LENGTH = 8
EXIT_CODE_SIZE = 2

MAX_BROADCAST_SIZE = 1024

# Various client compiler to compiler daemon command codes
FILE_COMMAND = "FILE"
COMPILE_COMMAND = "COMP"
STOP_COMMAND = "STOP"
EXIT_CODE_COMMAND = "EXCO"

# Various client compiler to scheduler deamon command codes
REQUEST_HOST = "REHO"

# Various host compiler to scheduler deamon command codes
RECORD_ME = "HORE"
UNSUBSCRIBE_ME = "UNME"
HOST_FREE = "FREE"
JOB_DONE = "JODO"

# Various monitor to scheduler deamon command codes
REQUEST_INFO = "INFO"
