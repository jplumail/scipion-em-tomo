# coding=utf-8
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

from os.path import abspath

import pyworkflow.em as pwem
from pyworkflow.em import ImageHandler
from pyworkflow.em.data import Transform
from pyworkflow.em.convert import Ccp4Header
from pyworkflow.utils.path import createAbsLink

from .protocol_base import ProtTomoBase
from tomo.objects import SubTomogram


class ProtImportSubTomograms(pwem.ProtImportVolumes, ProtTomoBase):
    """Protocol to import a set of tomograms to the project"""
    _outputClassName = 'SetOfSubTomograms'
    _label = 'import subtomograms'

    def __init__(self, **args):
        pwem.ProtImportVolumes.__init__(self, **args)

    def _insertAllSteps(self):
        self._insertFunctionStep('importSubTomogramsStep',
                                 self.getPattern(),
                                 self.samplingRate.get(),
                                 self.setOrigCoord.get())

    # --------------------------- STEPS functions -----------------------------

    def importSubTomogramsStep(self, pattern, samplingRate, setOrigCoord=False):
        """ Copy images matching the filename pattern
        Register other parameters.
        """
        self.info("Using pattern: '%s'" % pattern)

        # Create a Volume template object
        subtomo = SubTomogram()
        subtomo.setSamplingRate(samplingRate)

        imgh = ImageHandler()

        subtomoSet = self._createSetOfSubTomograms()
        subtomoSet.setSamplingRate(samplingRate)

        for fileName, fileId in self.iterFiles():
            x, y, z, n = imgh.getDimensions(fileName)
            if fileName.endswith('.mrc') or fileName.endswith('.map'):
                fileName += ':mrc'
                if z == 1 and n != 1:
                    zDim = n
                    n = 1
                else:
                    zDim = z
            else:
                zDim = z
            origin = Transform()
            if setOrigCoord:
                origin.setShiftsTuple(self._getOrigCoord())
            else:
                origin.setShifts(x/-2. * samplingRate,
                            y/-2. * samplingRate,
                            zDim/-2. * samplingRate)

            subtomo.setOrigin(origin)  # read origin from form

            if self.copyFiles or setOrigCoord:
                newFileName = abspath(self._getVolumeFileName(fileName, "mrc"))
                Ccp4Header.fixFile(fileName, newFileName, origin.getShifts(),
                                   samplingRate, Ccp4Header.ORIGIN)
            else:
                newFileName = abspath(self._getVolumeFileName(fileName))

                if fileName.endswith(':mrc'):
                    fileName = fileName[:-4]
                createAbsLink(fileName, newFileName)
            if n == 1:
                subtomo.cleanObjId()
                subtomo.setFileName(newFileName)
                subtomoSet.append(subtomo)
            else:
                for index in range(1, n+1):
                    subtomo.cleanObjId()
                    subtomo.setLocation(index, newFileName)
                    subtomoSet.append(subtomo)

        if subtomoSet.getSize() > 1:
            self._defineOutputs(outputSubTomograms=subtomoSet)
        else:
            self._defineOutputs(outputSubTomogram=subtomo)

    # --------------------------- INFO functions ------------------------------
    def _hasOutput(self):
        return (self.hasAttribute('outputSubTomogram')
                or self.hasAttribute('outputSubTomograms'))

    def _getSubTomMessage(self):
        if self.hasAttribute('outputSubTomogram'):
            return "SubTomogram %s" % self.getObjectTag('outputSubTomogram')
        else:
            return "SubTomograms %s" % self.getObjectTag('outputSubTomograms')

    def _summary(self):
        summary = []
        if self._hasOutput():
            summary.append("%s imported from:\n%s"
                           % (self._getSubTomMessage(), self.getPattern()))

            summary.append(u"Sampling rate: *%0.2f* (Å/px)" %
                           self.samplingRate.get())
        return summary

    def _methods(self):
        methods = []
        if self._hasOutput():
            methods.append(" %s imported with a sampling rate *%0.2f*" %
                           (self._getSubTomMessage(), self.samplingRate.get()),)
        return methods

    def _getOrigCoord(self):
        return -1.*self.x.get(), -1.*self.y.get(), -1.*self.z.get()