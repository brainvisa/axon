# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.

__author__ = "Julien Gilli <jgilli@nerim.fr>"
__version__ = "0.0"
__date__ = "Friday October 18"

"""This module provides common utility functions
to exchange data through network connections."""

import string
import Protocol

def send_data(socket, data):
    """Send data through the connection "socket" """
    
    # send data size
    data_size = str(hex(len(data))).replace('0x', '').replace('L', '')[:Protocol.DATA_LENGTH]
    data_size = '0' * (Protocol.DATA_LENGTH - len(data_size)) + data_size
    socket.send(data_size)
    
    # send data
    size_to_send = len(data)
    size_sent_so_far = 0
    while size_sent_so_far < size_to_send:
        size_sent_so_far += socket.send(data[size_sent_so_far:])
        
def recv_data(socket):
    """Receive data via the connection "socket" """
    
    # get the data size
    data_size = string.atoi(socket.recv(Protocol.DATA_LENGTH), 16)
    
    # get the data
    data = ""
    tmp_data = socket.recv(data_size)
    data_received_so_far = len(tmp_data)
    data += tmp_data
    
    while data_received_so_far < data_size:
        tmp_data = socket.recv(data_size - data_received_so_far)
        data_received_so_far += len(tmp_data)
        data += tmp_data

    return data

