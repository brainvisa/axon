#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
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

from neuroProcesses import *
import shfjGlobals
import string
from brainvisa import anatomist

name = 'Anatomist Check Register'
userLevel = 2

def validation():
  anatomist.validation()

signature = Signature(
  'epi_image',         ReadDiskItem(  'fMRI', 'Series of SPM image', requiredAttributes={ 'SPM preprocessing': 'none','Distorsion correction': 'no' } ),
  'epicorr_image',     ReadDiskItem(  'fMRI', 'Series of SPM image', requiredAttributes={ 'SPM preprocessing': 'none','Distorsion correction': 'yes','fieldmap': 'apply' } ),
  'index',             Integer(),
  'anat_image',        ReadDiskItem( "T1 MRI", 'SPM image' ),
  'epiTOanat',         ReadDiskItem( 'Transformation matrix', 'Transformation matrix' ),
  'view',              Choice('Axial', 'Sagittal', 'Coronal','All 3 views (for epi_image only)' ),
)
	
def initialization( self ):
    self.linkParameters( 'epicorr_image', 'epi_image')
    self.linkParameters( 'anat_image', 'epi_image')
    self.linkParameters( 'epiTOanat', 'epi_image')
    self.setOptional( 'epicorr_image', 'epiTOanat' )
    self.index = 1
    self.view = "Axial"
    
def execution( self, context ):
## ANATOMIST   
    a = anatomist.Anatomist()
    
    ImageFonct = a.loadObject( self.epi_image.fullPathSerie( self.index-1 )  )
    context.write( self.epi_image.fullPathSerie( self.index-1 ) )
    ImageFonct.setPalette( a.getPalette("rainbow2-fusion") )
    ImageAnat = a.loadObject( self.anat_image.fullPath()  )
    fusion1 = a.fusionObjects( [ImageFonct, ImageAnat], method = 'Fusion2DMethod' )

    if self.view != 'All 3 views (for epi_image only)':
        window1 = a.createWindow( self.view )
        RefAnat = a.createReferential()
        a.assignReferential(refAnat, [ImageAnat, window1] )
        RefFonct = a.createReferential()
        a.assignReferential(RefFonct, [ImageFonct, window1] )
        window1.addObjects( [fusion1] )

        if self.epicorr_image is not None:
            if self.epicorr_image.fullPath() == self.epi_image.fullPath():
                fusion2 = None
                window2 = None
                ImageFonctCorr = None
            else:
                context.write( self.epicorr_image.fullPathSerie( self.index-1 ) )
                ImageFonctCorr = a.loadObject( self.epicorr_image.fullPathSerie( self.index-1 )  )
                ImageFonctCorr.setPalette( a.getPalette("rainbow2-fusion") )
                fusion2 = a.fusionObjects( [ImageFonctCorr, ImageAnat], 
                                                        method \
                                                        = 'Fusion2DMethod' )
                window2 = a.createWindow( self.view )
                imageFonctRef=ImageFonct.referential
                window2.assignReferential( imageFonctRef )
                ImageFonctCorr.assignReferential( imageFonctRef )
                window2.addObjects( [fusion2] )
        else:
                fusion2 = None
                window2 = None
                ImageFonctCorr = None

        if self.epiTOanat is not None:
                self.trans = a.loadTransformation( self.epiTOanat.fullPath(), RefFonct, RefAnat )
                
        window3 = None
    
    else:

        window1 = a.createWindow( 'Axial' )
        RefAnat = a.createReferential()
        a.assignReferential(RefAnat, [ImageAnat, window1] )
        RefFonct = a.createReferential()
        a.assignReferential(RefFonct, [ImageFonct, window1] )
        fusion1 = a.fusionObjects( [ImageAnat, ImageFonct],
                                           method = 'Fusion2DMethod' )
        window1.addObjects( [fusion1] )
            
        window2 = a.createWindow( 'Sagittal' )
        window2.assignReferential( RefFonct )
        window2.addObjects( [fusion1] )
            
        window3 = a.createWindow( 'Coronal' )
        window3.assignReferential( RefFonct )
        window3.addObjects( [fusion1] )

        if self.epiTOanat is not None:
                self.trans = a.loadTransformation( self.epiTOanat.fullPath(), RefFonct, RefAnat )

        fusion2 = None
        ImageFonctCorr = None
        
    return [ImageFonct, ImageAnat, ImageFonctCorr, RefFonct, RefAnat, fusion1, fusion2, window1, window2, window3 ]

