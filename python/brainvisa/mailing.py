# Copyright CEA and IFR 49 (2000-2005)
#
#  This software and supporting documentation were developed by
#      CEA/DSV/SHFJ and IFR 49
#      4 place du General Leclerc
#      91401 Orsay cedex
#      France
#
# This software is governed by the CeCILL license version 2 under 
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
# knowledge of the CeCILL license version 2 and that you accept its terms.
try:
  import email
  from email.MIMEText import MIMEText
  from email.MIMEBase import MIMEBase
  canMail = 1
except:
  canMail = 0

if canMail:
  try:
    from email.MIMEMultipart import MIMEMultipart
  except:
    # Copyright (C) 2002 Python Software Foundation
    # Author: barry@zope.com (Barry Warsaw)

    """Base class for MIME multipart/* type messages.
    """


    class MIMEMultipart(MIMEBase):
      """Base class for MIME multipart/* type messages."""

      def __init__(self, _subtype='mixed', boundary=None, *_subparts, **_params):
        """Creates a multipart/* type message.

        By default, creates a multipart/mixed message, with proper
        Content-Type and MIME-Version headers.

        _subtype is the subtype of the multipart content type, defaulting to
        `mixed'.

        boundary is the multipart boundary string.  By default it is
        calculated as needed.

        _subparts is a sequence of initial subparts for the payload.  It
        must be possible to convert this sequence to a list.  You can always
        attach new subparts to the message by using the attach() method.

        Additional parameters for the Content-Type header are taken from the
        keyword arguments (or passed into the _params argument).
        """
        MIMEBase.__init__(self, 'multipart', _subtype, **_params)
        if _subparts:
            self.attach(*list(_subparts))
        if boundary:
            self.set_boundary(boundary)

