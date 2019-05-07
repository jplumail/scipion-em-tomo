# **************************************************************************
# *
# * Authors:     Adrian Quintana (adrian@eyeseetea.com) [1]
# *
# * [1] EyeSeeTea Ltd, London, UK
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************


"""
This module implements visualization program
for input tomograms.
"""

import os
from distutils.spawn import find_executable
from tkMessageBox import showerror

import pyworkflow.protocol.params as params
from pyworkflow.em.convert import ImageHandler
from pyworkflow.viewer import DESKTOP_TKINTER, WEB_DJANGO, ProtocolViewer, MessageView, MSG_ERROR
import pyworkflow.em.viewers as viewers

from tomo.protocols import protocol_import_tomograms

TOMOGRAM_SLICES = 1
TOMOGRAM_CHIMERA = 0


class ViewerProtImportTomograms(ProtocolViewer):
    """ Wrapper to visualize different type of objects
    with the Xmipp program xmipp_showj. """

    _label = 'viewer input tomogram'
    _targets = [protocol_import_tomograms.ProtImportTomograms]
    _environments = [DESKTOP_TKINTER, WEB_DJANGO]

    def _defineParams(self, form):
        form.addSection(label='Visualization of input tomograms')
        form.addParam('displayTomo', params.EnumParam,
                      choices=['chimera', 'slices'],
                      default=TOMOGRAM_CHIMERA,
                      display=params.EnumParam.DISPLAY_HLIST,
                      label='Display tomogram with',
                      help='*chimera*: display tomograms as surface with '
                           'Chimera.\n *slices*: display tomograms as 2D slices '
                           'along z axis.\n If number of tomograms == 1, '
                           'a system of coordinates is shown'
                      )

    def _getVisualizeDict(self):
        return {
            'displayTomo': self._showTomograms,
        }

    def _validate(self):
        if (self.displayTomo == TOMOGRAM_CHIMERA
                and find_executable(viewers.viewer_chimera.Chimera.getProgram()) is None):
            return ["chimera is not available. "
                    "Either install it or choose option 'slices'. "]
        return []

    # =========================================================================
    # ShowTomograms
    # =========================================================================

    def _showTomograms(self, paramName=None):
        if self.displayTomo == TOMOGRAM_CHIMERA:
            return self._showTomogramsChimera()

        elif self.displayTomo == TOMOGRAM_SLICES:
            return self._showTomogramsSlices()

    def _createSetOfTomograms(self):
        try:
            setOfTomograms = self.protocol.outputTomograms
            sampling = self.protocol.outputTomograms.getSamplingRate()
        except:
            setOfTomograms = self.protocol._createSetOfTomograms()
            setOfTomograms.append(self.protocol.outputTomogram)
            sampling = self.protocol.outputTomogram.getSamplingRate()

        return sampling, setOfTomograms

    def _showTomogramsChimera(self):
        """ Create a chimera script to visualize selected tomograms. """
        tmpFileNameCMD = self.protocol._getTmpPath("chimera.cmd")
        f = open(tmpFileNameCMD, "w")
        sampling, _setOfTomograms = self._createSetOfTomograms()
        count = 0  # first model in chimera is a tomogram

        if len(_setOfTomograms) == 1:
            count = 1  # first model in chimera is the bild file
            # if we have a single tomogram then create axis
            # as bild file. Chimera must read the bild file first
            # otherwise system of coordinates will not
            # be in the center of the window

            dim = self.protocol.outputTomogram.getDim()[0]
            tmpFileNameBILD = os.path.abspath(self.protocol._getTmpPath(
                "axis.bild"))
            viewers.viewer_chimera.Chimera.createCoordinateAxisFile(dim,
                                             bildFileName=tmpFileNameBILD,
                                             sampling=sampling)
            f.write("open %s\n" % tmpFileNameBILD)
            f.write("cofr 0,0,0\n")  # set center of coordinates
            count = 1  # skip first model because is not a 3D map

        for tomo in _setOfTomograms:
            localTomo = os.path.abspath(ImageHandler.removeFileType(
                tomo.getFileName()))
            if localTomo.endswith("stk"):
                self.showError("Extension .stk is not supported")
            f.write("open %s\n" % localTomo)
            f.write("volume#%d style surface voxelSize %f\n" %
                    (count, sampling))
            count += 1

        if len(_setOfTomograms) > 1:
            f.write('tile\n')
        else:
            x, y, z = tomo.getShiftsFromOrigin()
            f.write("volume#1 origin %0.2f,%0.2f,%0.2f\n" % (x, y, z))
        f.close()
        return [viewers.viewer_chimera.ChimeraView(tmpFileNameCMD)]

    def _showTomogramsSlices(self):
        # Write an sqlite with all tomograms selected for visualization.
        sampling, setOfTomograms = self._createSetOfTomograms()

        if len(setOfTomograms) == 1:
            return [self.objectView(self.protocol.outputTomogram)]

        return [self.objectView(setOfTomograms)]

