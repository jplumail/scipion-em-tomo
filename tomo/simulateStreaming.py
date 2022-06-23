# **************************************************************************
# *
# * Authors:    Alberto Garcia Mena (alberto.garcia@cnb.csic.es)
# *
# * [1] SciLifeLab, Stockholm University
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

from os.path import join
import time
import glob
import sys


def simulateStreaming(pathOrg, fileNameMdoc, timeSleep):
    import os
    import shutil
    pathMdoc = glob(join(pathOrg, fileNameMdoc))
    pathFolderData, mdocName = os.path.split(pathMdoc)
    print('pathMdoc: ', pathMdoc)

    # copied all files in streamingFolder. The first the mdoc, after that
    # added files with a sleeptime
    pathStreaming = os.path.join(pathFolderData, 'streamingData')
    os.makedirs(pathStreaming, exist_ok=True)
    shutil.copyfile(pathMdoc, os.path.join(pathStreaming, mdocName))
    #set streaming path for protocolfilesPath.set(pathStreaming)
    print('pathStreaming: ', pathStreaming)

    #print('pathStreaming updated: ', glob(join(pathOrg, self.filesPattern.get()))[0])

    for path in os.listdir(pathFolderData):
        headPath, nameFile = os.path.split(path)
        if nameFile[-3:] == 'mrc':
            print(nameFile)
            shutil.copyfile(path,
                            os.path.join(pathStreaming, nameFile))
            time.sleep(timeSleep)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 2:
        pathOrg = args[1]
        fileNameMdoc = args[2]
        timeSleep = args[3]

    simulateStreaming(pathOrg, fileNameMdoc, timeSleep)