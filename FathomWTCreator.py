#!/bin/python

import sys
import os
import getopt
import wave
import struct
import xml.etree.ElementTree as ET


def writeError(message):
	sys.stderr.write(message)

def printUsage():
	usageText = """
Use the following basic parameters:
  -f, --file: Convert the single file "filename".
  -d, --dir: Recursively convert all files in the given directory.
  -g, --targetdir: Put all converted files into the given target directory. If
                   this parameter is not given and you convert a whole
                   directory then all files will be put next to the original
                   files.
  -l, --length: The number of samples that's assumed for wave table files.
  -w: Mode that converts Fathom XML to wav files. Provide the file to convert
      using the -f option. The resulting file will have the same name as the
      input file with ".wav" appended.

Parameters for meta data:
  -c, --category: Use the given category for all converted files
  -a, --author: Use the given author for all converted files
  -m, --comment: Use the given comment for all converted files
  -r, --rating: Use the given rating (in [0, 10]) for all converted files
  -t, --type: Use the given type for all converted files
	"""
	writeError(usageText)
	writeFormatConditions()

def writeFormatConditions():
	formatText = """
Make sure that the files you want to convert meet the following conditions:
* The file contains wav data and its extension is "wav".
* The file is mono and is in 16 or 32 bit PCM format (not IEEE float format)
* If the number of samples is greater than 2048 it must be a multiple of 2048
	"""
	writeError (formatText)

def writeWaveTableToXMLFile(waveForms, waveTableName,  outfile):
	numberOfWaveForms = len(waveForms)
	swt = ET.Element("SynthWaveTable")
	swt.attrib["Name"] = waveTableName
	wt = ET.SubElement(swt, "WaveTable")
	for i in range(numberOfWaveForms):
		wave = ET.SubElement(wt, "wave")
		members = ET.SubElement(wave, "Members")
		members.attrib["WaveMode"] = "DRAW"
		# TODO Currently hard coded to 3
		members.attrib["ObjectIdNumber"] = str(3)
		members.attrib["ModulatorId"] = str(0)
		members.attrib["TableX"] = str(0)
		members.attrib["TableY"] = str(i)
		buffer = ET.SubElement(wave, "Buffer")
		currentWaveForm = waveForms[i]
		numSamplesCurrentWave = len(currentWaveForm)
		bmembers = ET.SubElement(buffer, "Members")
		bmembers.attrib["NumSamples"] = str(numSamplesCurrentWave)
		bmembers.attrib["Size"] = str(numSamplesCurrentWave)
		bmembers.attrib["SizeAllocated"] = str(numSamplesCurrentWave)
		bmembers.attrib["Index"] = str(0)
		bmembers.attrib["IsDoubleSize"] = str(0)
		samples = ET.SubElement(buffer, "Samples")
		currentText = ""
		for j in range(numSamplesCurrentWave - 1):
			currentText += str(currentWaveForm[j]) + ","
		currentText += str(currentWaveForm[numSamplesCurrentWave - 1])
		samples.text = currentText

	ET.ElementTree(swt).write(outfile)

def writeWaveToXMLFile(waveForm, waveTableName, outfile):
	numberOfWaveForms = len(waveForms)
	swt = ET.Element("SynthWaveform")
	swt.attrib["Name"] = waveTableName

	wave = ET.SubElement(swt, "wave")
	members = ET.SubElement(wave, "Members")

	members.attrib["ObjectIdNumber"] = str(1)
	
	buffer = ET.SubElement(wave, "Buffer")
	bmembers = ET.SubElement(buffer, "Members")
	numSamplesCurrentWave = len(waveForm)
	bmembers.attrib["NumSamples"] = str(numSamplesCurrentWave)
	bmembers.attrib["Size"] = str(numSamplesCurrentWave)
	bmembers.attrib["SizeAllocated"] = str(numSamplesCurrentWave)
	bmembers.attrib["Index"] = str(0)
	bmembers.attrib["IsDoubleSize"] = str(0)
	samples = ET.SubElement(buffer, "Samples")
	currentText = ""
	for j in range(numSamplesCurrentWave - 1):
		currentText += str(waveForm[j]) + ","
	currentText += str(waveForm[numSamplesCurrentWave - 1])
	samples.text = currentText

	ET.ElementTree(swt).write(outfile, encoding='UTF-8', xml_declaration=True)

def replaceUnderscore(text):
	return text.replace("_", " ")

def extractPatchNameFromFilename(filename):
	absolutePath = os.path.abspath(filename)
	folder, basename = os.path.split(absolutePath)

	basenameWithoutExtension = os.path.splitext(basename)[0]
	patchname = replaceUnderscore(basenameWithoutExtension)
	
	return patchname

# Creates a name with a pattern as used by the Fathom synth:
# Name.Category.Author.Comment.Rating.Type.xml
# Example: "Perfect Saw.Lead.Joe Doe.A nice lead sound.10.Wave Table.xml"
def createFathomBasename(patchname, category, author, comment, rating, waveType):
	return patchname + "." + category + "." + author + "." + comment + "." + rating + "." + waveType + ".xml"

def endsWith(filename, extension):
	return filename.lower().endswith(extension)

def createDirIfNotExists(targetDir):
	absTargetDir = os.path.abspath(targetDir)
	if not os.path.exists(absTargetDir):
		print ("Creating target directory " + absTargetDir)
		try:
			os.makedirs(absTargetDir)
		except:
			writeError("Could not create target directory. Aborting...")
			exit (1)

def collectSourceTargetPairs(absStartDir, absTargetDir, sourceTargetPairs):
	for root, dirs, files in os.walk(absStartDir):
		composedTargetPath = root
		if absTargetDir != None:
			relPath = os.path.relpath(root, absStartDir)
			composedTargetPath = os.path.join(absTargetDir, relPath)
		for file in files:
			if endsWith(file, "wav"):
				sourceFile = os.path.join(root, file)

				currentPatchName = extractPatchNameFromFilename(file)
				outBasename = createFathomBasename(currentPatchName, category, author, comment, rating, waveType)
				targetFile = os.path.join(composedTargetPath, outBasename)
				
				# TODO Move to the actual writing code!
				createDirIfNotExists(composedTargetPath)

				sourceTargetPairs.append((sourceFile, targetFile, currentPatchName))

def readWaveTables(filename, lengthOfSingleWave):
	conversionFailed = False
	errorMessages = []
	try:
		f = wave.open(filename)
	except FileNotFoundError:
		conversionFailed = True
		errorMessages.append("File not found")
	except:
		conversionFailed = True
		errorMessages.append("File could not be read. Conditions might not be met, e.g. not in PCM.")

	numberOfChannels = f.getnchannels()
	sampleWidth = f.getsampwidth()
	numberOfFrames = f.getnframes()

	# Perform necessary checks
	if numberOfChannels != 1:
		conversionFailed = True
		errorMessages.append("Not exactly one channel")
		
	if sampleWidth != 2 and sampleWidth != 4:
		conversionFailed = True
		errorMessages.append("Not 16 or 32 bit")
		
	if numberOfFrames > lengthOfSingleWave and numberOfFrames % lengthOfSingleWave != 0:
		conversionFailed = True
		errorMessages.append("Wrong number of samples")
	
	if errorMessages:
		return ([], errorMessages)

	numberOfWaveForms = int (numberOfFrames / lengthOfSingleWave)
	if numberOfFrames > 0 and numberOfFrames <= lengthOfSingleWave:
		numberOfWaveForms = 1
		lengthOfSingleWave = numberOfFrames

	divisor = pow(2, 31) - 1
	structFormat = "<i"

	if sampleWidth == 2:
		divisor = pow(2, 15) - 1
		structFormat = "<h"

	waveForms = []

	try:
		for i in range(numberOfWaveForms):
			waveData = []
			for j in range(lengthOfSingleWave):
				bytes = f.readframes(1)
				data = struct.unpack(structFormat, bytes)
				waveData.append(data[0] / divisor)
			waveForms.append(waveData)
	except:
		errorMessages.append("Error while reading byte stream.")

	f.close()
	
	if errorMessages:
		return ([], errorMessages)
	
	return (waveForms, errorMessages)

# Functions related to the conversion from Fathom XML to wav
def readBuffersFromXML(absFilename):
	tree = ET.parse(absFilename)
	root = tree.getroot()

	# root is already at "SynthWaveTable" so we search starting from there
	samples = root.findall("./WaveTable/wave/Buffer/Samples")
	buffer = []
	for sample in samples:
		text = sample.text
		doubleText = text.split(',')
		for d in doubleText:
			buffer.append(float(d))
	
	return buffer

def writeWaveFile(filename, buffer):
	# The wave package can only read and write integer data so we need to
	# convert the floats from the XML to integers. This is the same value
	# that we used for the other way around.
	multiplier = pow(2, 31) - 1

	# ww is a wave_write object
	ww = wave.open(filename, 'w')
	ww.setnchannels(1)
	ww.setsampwidth(4)
	ww.setframerate(44100)
	ww.setnframes(len(buffer))
	for val in buffer:
		asInt = int(val * multiplier)
		byte = struct.pack('<i', asInt)
		ww.writeframesraw(byte)

	ww.close()


# Main block starts here
filename = None

category = "_"
author = "_"
comment = "_"
rating = "0"
waveType = "Wave Table"
startDir = None
targetDir = None
absTargetDir = None
waveDump = False

waveTableName = "Wave Table 1"

lengthOfSingleWave = 2048

opts,args = getopt.getopt(sys.argv[1:],'f:c:a:m:r:t:l:d:g:w', ["file=", "category=", "author=", "comment=", "rating=", "type=", "length=", "dir=", "targetdir="])
for o, a in opts:
	if o in ("-f", "--file"):
		filename = a
	if o in ("-c", "--category"):
		category = replaceUnderscore(a)
	if o in ("-a", "--author"):
		author = replaceUnderscore(a)
	if o in ("-m", "--comment"):
		comment = replaceUnderscore(a)
	if o in ("-r", "--rating"):
		rating = replaceUnderscore(a)
	if o in ("-t", "--type"):
		waveType = replaceUnderscore(a)
	if o in ("-l", "--length"):
		try:
			lengthOfSingleWave = int(a)
		except:
			print ("Error parsing length of single cycle. Please enter an integer number.")
			exit (1)
	if o in ("-d", "--dir"):
		startDir = a
	if o in ("-g", "--targetdir"):
		targetDir = a
	if o in ("-w"):
		waveDump = True

# Quick check if we want to convert Fathom wavetables to wav
if waveDump:
	if filename == None:
		writeError ("Please specify a filename.")
		printUsage()
		exit(1)
	else:
		absFilename = os.path.abspath(filename)
		buffer = readBuffersFromXML(absFilename)

		wavFilename = absFilename + ".wav"
		print ("Writing file " + wavFilename)
		writeWaveFile(wavFilename, buffer)
	exit(0)

if startDir != None and filename != None:
	writeError ("Please specify a source directory or a file exclusively.")
	printUsage()
	exit(1)

if targetDir != None:
	absTargetDir = os.path.abspath(targetDir)
	if not os.path.exists(absTargetDir):
		print ("Creating target directory " + absTargetDir)
		try:
			os.makedirs(absTargetDir)
		except:
			writeError("Could not create target directory. Aborting...")
			exit (1)

sourceTargetPairs = []
			
if startDir != None:
	absStartDir = os.path.abspath(startDir)
	if not os.path.isdir(absStartDir):
		writeError ("Directory " + absStartDir + " does not exist. Please point to an existing directory!")
		exit(1)

	collectSourceTargetPairs(absStartDir, absTargetDir, sourceTargetPairs)

if filename != None:
	sourceFile = os.path.abspath(filename)
	if os.path.exists(sourceFile):
		patchname = extractPatchNameFromFilename(sourceFile)
		outBasename = createFathomBasename(patchname, category, author, comment, rating, waveType)
		folder, basename = os.path.split(sourceFile)
		targetFile = os.path.join(folder, outBasename)
		sourceTargetPairs.append((sourceFile, targetFile, patchname))

if not sourceTargetPairs:
	writeError ("Please specify an input file and / or an input directory.")
	printUsage()
	exit(1)

sourceErrorMessages = []
	
for source, target, patchname in sourceTargetPairs:
	waveForms, errorMessages = readWaveTables(source, lengthOfSingleWave)
	if not waveForms or errorMessages:
		sourceErrorMessages.append((source, errorMessages))
	else:
		print ("Writing " + target)
		writeWaveTableToXMLFile(waveForms, patchname, target)
		# Comment this in if you only convert files with single waveforms and want to write a wave file
		#writeWaveToXMLFile(waveForms[0], patchname, target)

if sourceErrorMessages:
	writeError("Errors encountered for the following files:\n")
	for source, errorMessages in sourceErrorMessages:
		writeError("Errors occurred for " + source + "\n")
		for errorMessage in errorMessages:
			writeError(errorMessage + "\n")

	writeError("\n")		
	writeFormatConditions()
