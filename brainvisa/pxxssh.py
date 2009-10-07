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
from pexpect import *
#import os, sys, getopt, shutil

class pxssh (spawn):
    """
    This class extends pexpect.spawn to specialize setting up SSH connections.
    This adds methods for login, logout, and expecting the prompt.
    It does various hacky things to handle any situation in the SSH login process.
    For example, if the session is your first login, then it automatically
    accepts the certificate; or if you have public key authentication setup
    and you don't need a password then this is OK too.

    Example usage that runs 'ls -l' on server and prints the result:
        import pxssh
        s = pxssh.pxssh()
        if not s.login ('localhost', 'myusername', 'mypassword'):
            print "SSH session failed on login."
            print str(s)
        else:
            print "SSH session login successful"
            s.sendline ('ls -l')
            s.prompt()           # match the prompt
            print s.before     # print everything before the prompt.
            s.logout()
    """

    def __init__ (self):
        # SUBTLE HACK ALERT!
        # Note that the command to set the prompt uses a slightly different string
        # than the regular expression to match it. This is because when you set the
        # prompt the command will echo back, but we don't want to match the echoed
        # command. So if we make the set command slightly different than the regex
        # we eliminate the problem. To make the set command different we add a
        # backslash in front of $. The $ doesn't need to be escaped, but it doesn't
        # hurt and serves to make the set command different than the regex.
        self.PROMPT = "\[PEXPECT\][\$\#] " # used to match the command-line prompt.
        # used to set shell command-line prompt to something more unique.
        self.PROMPT_SET_SH = "PS1='[PEXPECT]\$ '"
        self.PROMPT_SET_CSH = "set prompt='[PEXPECT]\$ '"

    ### TODO: This is getting messy and I'm pretty sure this isn't perfect.
    ### TODO: I need to draw a better flow chart for this.
    def login (self,server,username,password='',terminal_type='ansi',original_prompts=r"][#$]|~[#$]|bash.*?[#$]|[#$] ",login_timeout=10):
        """
        This logs the user into the given server. By default the prompt is
        rather optimistic and should be considered more of an example. It's
        better to try to match the prompt as exactly as possible to prevent
        any false matches by server strings such as a "Message Of The Day" or
        something. The closer you can make the original_prompt match your real prompt
        then the better. A timeout will not necessarily cause the login to fail.
        In the case of a timeout we assume that the prompt was so weird that
        we could not match it. We still try to reset the prompt to something
        more unique. If that still fails then we return False.
        """
        cmd = "ssh -l %s %s -X -o NumberOfPasswordPrompts=1 -o NoHostAuthenticationForLocalhost=yes" % (username, server)
        spawn.__init__(self, cmd, timeout=login_timeout)
        #, "(?i)no route to host"])
        i = self.expect(["(?i)are you sure you want to continue connecting", original_prompts, "(?i)password", "(?i)permission denied", "(?i)terminal type", TIMEOUT, "(?i)connection closed by remote host"])
        if i==0: # New certificate -- always accept it. This is what you if SSH does not have the remote host's public key stored in the cache.
            self.sendline("yes")
            i = self.expect(["(?i)are you sure you want to continue connecting", original_prompts, "(?i)password", "(?i)permission denied", "(?i)terminal type", TIMEOUT])
        if i==2: # password
            self.sendline(password)
            i = self.expect(["(?i)are you sure you want to continue connecting", original_prompts, "(?i)password", "(?i)permission denied", "(?i)terminal type", TIMEOUT])
        if i==4:
            self.sendline(terminal_type)
            i = self.expect(["(?i)are you sure you want to continue connecting", original_prompts, "(?i)password", "(?i)permission denied", "(?i)terminal type", TIMEOUT])

        if i==0:
            # This is weird. This should not happen twice in a row.
            self.close()
            return False
        elif i==1: # can occur if you have a public key pair set to authenticate. 
            ### TODO: May NOT be OK if expect() matched a false prompt.
            pass
        elif i==2: # password prompt again
            # For incorrect passwords, some ssh servers will
            # ask for the password again, others return 'denied' right away.
            # If we get the password prompt again then this means
            # we didn't get the password right the first time. 
            self.close()
            return False
        elif i==3: # permission denied -- password was bad.
            self.close()
            return False
        elif i==4: # terminal type again? WTF?
            self.close()
            return False
        elif i==5: # Timeout
            # This is tricky... presume that we are at the command-line prompt.
            # It may be that the prompt was so weird that we couldn't match it.
            pass
        elif i==6: # Connection closed by remote host
            self.close()
            return False
        else: # Unexpected 
            self.close()
            return False
        # We appear to be in -- reset prompt to something more unique.
        """
        if not self.set_unique_prompt():
            self.close()
            return False
        """
        return True

    def logout (self):
        """
        This sends exit. If there are stopped jobs then this sends exit twice.
        """
        self.sendline("exit")
        index = self.expect([EOF, "(?i)there are stopped jobs"])
        if index==1:
            self.sendline("exit")
            self.expect(EOF)

    def prompt (self, timeout=20):
        """
        This expects the prompt. This returns True if the prompt was matched.
        This returns False if there was a timeout.
        """
        i = self.expect([self.PROMPT, TIMEOUT], timeout=timeout)
        if i==1:
            return False
        return True
        
    def set_unique_prompt (self, optional_prompt=None):
        """
        This attempts to reset the shell prompt to something more unique.
        This makes it easier to match unambiguously.
        """
        if optional_prompt is not None:
            self.prompt = optional_prompt
        self.sendline (self.PROMPT_SET_SH) # sh-style
        i = self.expect ([TIMEOUT, self.PROMPT], timeout=10)
        if i == 0: # csh-style
            self.sendline (self.PROMPT_SET_CSH)
            i = self.expect ([TIMEOUT, self.PROMPT], timeout=10)
            if i == 0:
                return 0
        return 1

